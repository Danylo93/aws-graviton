import typing as t
import datetime

from http import HTTPStatus

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.application.http.client import http_client_service
from arcs_lib_pca.domain import DateTime

from src.infrastructure.models import (
    AccessProfileModel,
    ServiceModel,
    PersonModel
)

from src.domain.value_objects import (
    DashboardResponse,
    DashboardPilotsPerStageResponse,
    DashboardPendingShipmentsResponse,
    DashboardDataShipmentsResponse,
    DashboardShipmentsResponse
)

from .requests import(
    GetDashRequestAuth
)

from .responses import(
    DashResponse
)

class DashboardsController(BaseController):
    _CACHE_DURATION_ = 60*60*4

    def _get_all_keys_of_pattern_from_redis_(self, pattern: str = '*') -> t.List[bytes]:
        redis = self.get_redis()
        keys = redis.get_sync_keys(pattern)
        return keys

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetDashRequestAuth,
        response=DashResponse
    )
    def get_dashboard(self, req: GetDashRequestAuth, resp: DashResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        data_dash = DashboardResponse()

        data_shipments = self.get_shipments(req)

        data_dash.total_pilots = self.load_repository(AccessProfileModel).db.count(subgroup_name="main_pilot")
        data_dash.total_stages = self.get_total_stages_in_year(req)
        data_dash.total_cars = len(self._get_all_keys_of_pattern_from_redis_("@car_service:model:cars:*"))
        data_dash.total_users = self.load_repository(AccessProfileModel).db.count()
        data_dash.pilots_per_stage = self.get_pilots_per_stage(req)
        
        data_dash.shipments = DashboardShipmentsResponse(
            labels=["Realizados", "Pendentes"],
            data=[data_shipments.total_realized, data_shipments.total_outstanding]
        )
        data_dash.pending_shipments = DashboardPendingShipmentsResponse(
            total_items = data_shipments.total_items,
            data = data_shipments.data 
        )

        return resp(HTTPStatus.OK, data_dash, "Succesfully")

    def get_total_stages_in_year(self, req: GetDashRequestAuth) -> int:
        """
        Return the total number of stages in the current year.
        
        This method fetches data from the championship service and returns the total number of
        stages in the current year. If the refresh flag is set to True, the cache is invalidated and
        the data is refetched from the championship service.
        
        :param req: GetDashRequestAuth request object containing headers and refresh flag.
        :return: The total number of stages in the current year.
        """
        redis = self.get_redis()
        cache_key = "dash:total_stages_in_year"
        
        if not req.refresh:
            cached_value = redis.get_by_key(cache_key)
            if cached_value is not None:
                return int(cached_value)
        
        championship_service_model = self.load_repository(ServiceModel).db.get_by(name="championship_service")
        if not championship_service_model:
            return 0
        
        token = req.header.get("Authorization")
        if not token:
            return 0
        
        try:
            champ_page = http_client_service(
                base_url=championship_service_model.internal_url,
                authorization=token
            ).get(
                url_or_uri="/stages/", 
                params={"page": 1, "per_page": 100, "year": DateTime.now().year}
            )
            
            total_stages = int(champ_page.get("data", {}).get("totalItems", 0)) if champ_page else 0
            redis.add(cache_key, total_stages, ex=self._CACHE_DURATION_)
            return total_stages
            
        except Exception as e:
            self.logger.error(f"Error fetching total stages: {e}")
            return 0

    def get_pilots_per_stage(self, req: GetDashRequestAuth) -> DashboardPilotsPerStageResponse:
        """
        Return the number of pilots per cars per stage.
        
        This endpoint fetches data from the championship service and returns a
        DashboardPilotsPerStageResponse object containing the total number of
        pilots per stage and the labels for each stage. If the refresh flag is
        set to True, the cache is invalidated and the data is refetched from the
        championship service.

        :param req: The request model containing the refresh flag.
        :return: A DashboardPilotsPerStageResponse object containing the total number of
        pilots per stage and the labels for each stage.
        """
        redis = self.get_redis()
        if not req.refresh and (resp := redis.get_by_key("dash:pilots_per_stage", DashboardPilotsPerStageResponse)):
            return resp

        championship_service_model = self.load_repository(ServiceModel).db.get_by(name="championship_service")
        resp  = DashboardPilotsPerStageResponse()

        if not championship_service_model:
            return resp
            
        try:
            if not (token := req.header.get("Authorization")):
                return resp

            champ_page = http_client_service(
                base_url=championship_service_model.internal_url,
                authorization=token
            ).get(
                url_or_uri="/cars_by_stage/", 
                params={"page":1, "per_page": 1000}
            )
            if not champ_page:
                return resp
            
            resp = resp.process_totals(champ_page)
            redis.add("dash:pilots_per_stage", resp.to_dict(), ex=self._CACHE_DURATION_)
            return resp                
        except:
            return resp

    def get_shipments(self, req: GetDashRequestAuth) -> DashboardDataShipmentsResponse:
        """
        Return the number of shipments per status.

        This endpoint fetches data from the maintenance and contracts services and
        returns a DashboardDataShipmentsResponse object containing the total number
        of shipments per status. If the refresh flag is set to True, the cache is
        invalidated and the data is refetched from the services.

        :param req: The request model containing the refresh flag.
        :return: A DashboardDataShipmentsResponse object containing the total number of
        shipments per status.
        """
        redis = self.get_redis()
        
        cache_key = "dash:shipments"
        if not req.refresh and (resp := redis.get_by_key(cache_key, DashboardDataShipmentsResponse)):
            return resp

        maintenance_service_model = self.load_repository(ServiceModel).db.get_by(name="maintenance_service")
        contracts_service_model = self.load_repository(ServiceModel).db.get_by(name="contracts_service")
        start_date = f"{DateTime.now().year}-01-01"

        resp = DashboardDataShipmentsResponse()

        if not maintenance_service_model or not contracts_service_model:
            return resp

        if not (token := req.header.get("Authorization")):
            return resp

        def fetch_paginated_data(
                data: DashboardDataShipmentsResponse, 
                service_model: ServiceModel,
                endpoint: str,
                params: t.Dict[str, t.Any], 
                service_type: str, 
                field_status: str
            ) -> t.Optional[DashboardDataShipmentsResponse]:
            """
            Função genérica para buscar dados paginados de um serviço e processar o status.
            """
            try:
                response = http_client_service(
                    base_url=service_model.internal_url, 
                    authorization=token
                ).get(url_or_uri=endpoint, params=params)
                
                if not response:
                    return None

                return data.process_status(redis, response, service_type, field_status)
            except Exception as e:
                print(f"Erro ao buscar dados de {service_type}: {e}")

        # Busca relatórios de manutenção
        new_resp = fetch_paginated_data(
            data=resp,
            service_model=maintenance_service_model,
            endpoint="/all/",
            params={"page": 1, "per_page": 10000, "start_date": start_date},
            service_type="maintenance",
            field_status="status",
        )

        if new_resp:
            resp = new_resp

        # Busca contratos de pilotos
        new_resp = fetch_paginated_data(
            data=resp,
            service_model=contracts_service_model,
            endpoint="/all/",
            params={"page": 1, "per_page": 1000, "start_date": start_date},
            service_type="contract",
            field_status="shipping_contract_status",
        )
        if new_resp:
            resp = new_resp

        # Adiciona ao cache
        redis.add(cache_key, resp.to_dict(), ex=self._CACHE_DURATION_)

        return resp
