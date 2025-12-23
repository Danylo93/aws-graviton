import typing as t
from http import HTTPStatus
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.domain.value_objects import GenericUUID, ArcsServices

from src.infrastructure.models import ServiceModel, PermissionModel

from .requests import(
    GetAllServicesAuth,
    CreateServiceAuth,
    GetServiceAuth,
    UpdateServiceAuth,
    DeleteServiceAuth
)
from .responses import(
    ServiceAllGetResponse,
    ServiceCreatedResponse,
    ServiceGetResponse,
    ServiceUpdatedResponse,
    ServiceDeletedResponse,
)

class ServicesController(BaseController):
    
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllServicesAuth,
        response=ServiceAllGetResponse)
    def get_all_services(self, req: GetAllServicesAuth, resp: ServiceAllGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        service_repo = self.load_repository(ServiceModel)
        subquery = QueryParamsUseCase.load(req.params)
        data = service_repo.db.with_query(subquery).paginate(page=req.page, per_page=req.per_page, load=["icon"])

        return resp(HTTPStatus.OK, data, "Request Succefully")

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateServiceAuth,
        response=ServiceCreatedResponse)
    def create_service(self, req: CreateServiceAuth, resp: ServiceCreatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        service_repo = self.load_repository(ServiceModel)

        if service_repo.db.contains(name=req.name):
            return resp(400, message="Service already exists")
        
        service_data = req.to_dict()

        icon = None
        if req.icon:
            icon = service_repo.storage.add(req.icon)
            service_data['icon_id'] = icon.id

        service_model = service_repo.db.add(service_data)

        if not service_model:
            if icon:
                service_repo.storage.remove(icon.filename)
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Service")

        if not service_model.to_vo().upsert_in_redis(service_repo.redis):
            if icon:
                service_repo.storage.remove(icon.filename)
            service_repo.db.remove_by_id(service_model.id)
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error add App client in Redis")

        return resp(HTTPStatus.CREATED, service_model, "Created Succefully")
    
    @BaseController.route(
        path="/<path:service_id>",
        methods=["GET"],
        request=GetServiceAuth,
        response=ServiceGetResponse)
    def get_service(self, req: GetServiceAuth, resp: ServiceGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        service_repo = self.load_repository(ServiceModel)
        
        service_model = service_repo.db.get_by_id(id=req.service_id)

        if not service_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Service not found")
        
        return resp(HTTPStatus.OK, service_model.to_dict(lazy_load=["icon", "permissions"]), "Request Succefully")
    
    @BaseController.route(
        path="/<path:id>",
        methods=["PUT", "PATCH"],
        request=UpdateServiceAuth,
        response=ServiceUpdatedResponse)
    def update_service(self, req: UpdateServiceAuth, resp: ServiceUpdatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        service_data = req.to_dict()
        
        service_repo = self.load_repository(ServiceModel)
        if not (old_service := service_repo.db.get_by_id(req.id)):
            return resp(HTTPStatus.NOT_FOUND, {}, "Service not found")

        if req.icon:
            icon_vo = service_repo.storage.update(req.icon)
            service_data["icon_id"] = icon_vo.id

        service_data["updated_by"] = req.current_profile.profile_id
        service_model = service_repo.db.update_by_id(id=req.id, data=service_data)

        if not service_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating App client")

        if old_service.name != service_model.name:
            ArcsServices.remove_in_redis(service_repo.redis, old_service.name)
        
        service_model.to_vo().upsert_in_redis(service_repo.redis)

        return resp(HTTPStatus.OK, service_model.to_dict(), "Updated Succefully")
        
    @BaseController.route(
        path="/<path:service_id>",
        methods=["DELETE"],
        request=DeleteServiceAuth,
        response=ServiceDeletedResponse)
    def delete_service(self, req: DeleteServiceAuth, resp: ServiceDeletedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        service_repo = self.load_repository(ServiceModel)
        permission_repo = self.load_repository(PermissionModel)

        service_model : t.Optional[ServiceModel] = service_repo.db.get_by_id(req.service_id)

        if not service_model:
            return resp(HTTPStatus.NOT_FOUND, {}, "Service not found")

        permission_repo.db.remove(service_id=req.service_id)
        
        if service_model.icon_id:
            service_repo.storage.remove_by_id(service_model.icon_id)
        
        service_repo.db.delete(id=req.service_id)
        ArcsServices.remove_in_redis(service_repo.redis, service_model.name)

        return resp(HTTPStatus.OK, service_model, "Deleted successfully")
