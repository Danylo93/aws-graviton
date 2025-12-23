from http import HTTPStatus

from src.infrastructure.models import CBACardTypeModel
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.application import BaseController

from .requests import(
    GetCBACardTypeRequestAuth,
    GetCBACardTypeIdRequestAuth,
    CreateCBACardTypeIdRequestAuth,
    DeleteCBACardTypeIdRequestAuth,
    UpdateCBACardTypeIdRequestAuth
)

from .responses import(
    GetCBACardTypeResponse,
    GetUniqueCBACardTypeResponse,
    CreateCBACardTypeIdResponse,
    DeleteCBACardTypeIdResponse,
    UpdateCBACardTypeIdResponse
)

class CBACardTypeController(BaseController):
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetCBACardTypeRequestAuth,
        response=GetUniqueCBACardTypeResponse
    )
    def get_list_cba_card_types(self, req: GetCBACardTypeRequestAuth, resp:GetUniqueCBACardTypeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        cba_card_type_repo = self.load_repository(CBACardTypeModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        cba_card_type = cba_card_type_repo.db.with_query(subquery_params).paginate(req.page, req.per_page)

        return resp(HTTPStatus.OK, cba_card_type, "Succesfully")

    @BaseController.route(
        path="/<cba_card_type_id>",
        methods=["GET"],
        request=GetCBACardTypeIdRequestAuth,
        response=GetCBACardTypeResponse
    )
    def get_cba_card_type_by_id(self, req: GetCBACardTypeIdRequestAuth, resp:GetCBACardTypeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        cba_card_type_repo = self.load_repository(CBACardTypeModel)
        cba_card_type_model = cba_card_type_repo.db.get_by_id(id=req.cba_card_type_id)

        if not cba_card_type_model:
            return resp(HTTPStatus.BAD_REQUEST, message="CBACardType not exists")

        return resp(HTTPStatus.OK, cba_card_type_model.to_dict(), "Succesfully")
    
    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateCBACardTypeIdRequestAuth,
        response=CreateCBACardTypeIdResponse
    )
    def create_cba_card(self, req: CreateCBACardTypeIdRequestAuth, resp:CreateCBACardTypeIdResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        cba_card_type_repo = self.load_repository(CBACardTypeModel)

        if cba_card_type_repo.db.contains(type=req.type, description=req.description):
            return resp(HTTPStatus.CONFLICT, message="CBA Card Type already exists")

        cba_card_type = cba_card_type_repo.db.add(req.to_dict())

        return resp(HTTPStatus.OK, cba_card_type.to_dict(), "Succesfully")
    
    @BaseController.route(
        path="/<cba_card_type_id>",
        methods=["PUT"],
        request=UpdateCBACardTypeIdRequestAuth,
        response=UpdateCBACardTypeIdResponse
    )
    def update_cba_card_type_by_id(self, req: UpdateCBACardTypeIdRequestAuth, resp:UpdateCBACardTypeIdResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        
        cba_card_type_repo = self.load_repository(CBACardTypeModel)

        cba_card_type_model = cba_card_type_repo.db.get_by_id(req.cba_card_type_id)

        if (cba_card_type_model.type != req.type or cba_card_type_model.description != req.description):
            cba_temp = cba_card_type_repo.db.get_by(type=req.type, description=req.description)

            if cba_temp is not None and cba_temp.id != req.cba_card_type_id:
                return resp(HTTPStatus.CONFLICT, message="CBA Card Type already exists")
        
        cba_card_type_model = cba_card_type_repo.db.update_by_id(id=req.cba_card_type_id, data={"type": req.type, "description": req.description})

        return resp(HTTPStatus.OK, cba_card_type_model.to_dict(), "Succesfully")
    
    @BaseController.route(
        path="/<cba_card_type_id>",
        methods=["DELETE"],
        request=DeleteCBACardTypeIdRequestAuth,
        response=DeleteCBACardTypeIdResponse
    )
    def delete_cba_card_type_by_id(self, req: DeleteCBACardTypeIdRequestAuth, resp:DeleteCBACardTypeIdResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        if not self.load_repository(CBACardTypeModel).db.contains(id=req.cba_card_type_id):
            return resp(HTTPStatus.BAD_REQUEST, message="CBACardType not exists")
        
        self.load_repository(CBACardTypeModel).db.remove_by_id(req.cba_card_type_id)

        return resp(HTTPStatus.OK, message="Delete Succesfully")