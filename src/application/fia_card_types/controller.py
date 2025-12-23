from http import HTTPStatus

from src.infrastructure.models import FIACardTypeModel
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.application import BaseController

from .requests import(
    GetFiaCardTypeRequestAuth,
    GetFiaCardTypeIdRequestAuth,
    CreateFiaCardTypeIdRequestAuth,
    DeleteFiaCardTypeIdRequestAuth,
    UpdateFiaCardTypeIdRequestAuth
)

from .responses import(
    GetFiaCardTypeResponse,
    GetUniqueFiaCardTypeResponse,
    CreateFiaCardTypeIdResponse,
    DeleteFiaCardTypeIdResponse,
    UpdateFiaCardTypeIdResponse
)

class FiaCardTypeController(BaseController):
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetFiaCardTypeRequestAuth,
        response=GetUniqueFiaCardTypeResponse
    )
    def get_list_fia_card_types(self, req: GetFiaCardTypeRequestAuth, resp:GetUniqueFiaCardTypeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        fia_card_type_repo = self.load_repository(FIACardTypeModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        fia_card_type = fia_card_type_repo.db.with_query(subquery_params).paginate(req.page, req.per_page)

        return resp(HTTPStatus.OK, fia_card_type, "Succesfully")

    @BaseController.route(
        path="/<fia_card_type_id>",
        methods=["GET"],
        request=GetFiaCardTypeIdRequestAuth,
        response=GetFiaCardTypeResponse
    )
    def get_fia_card_type_by_id(self, req: GetFiaCardTypeIdRequestAuth, resp:GetFiaCardTypeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        fia_card_type_repo = self.load_repository(FIACardTypeModel)
        fia_card_type_model = fia_card_type_repo.db.get_by_id(id=req.fia_card_type_id)

        if not fia_card_type_model:
            return resp(HTTPStatus.BAD_REQUEST, message="FiaCardType not exists")

        return resp(HTTPStatus.OK, fia_card_type_model.to_dict(), "Succesfully")
    
    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateFiaCardTypeIdRequestAuth,
        response=CreateFiaCardTypeIdResponse
    )
    def create_fia_card(self, req: CreateFiaCardTypeIdRequestAuth, resp:CreateFiaCardTypeIdResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        fia_card_type_repo = self.load_repository(FIACardTypeModel)

        if fia_card_type_repo.db.contains(type=req.type, description=req.description):
            return resp(HTTPStatus.CONFLICT, message="Fia Card Type already exists")

        fia_card_type = fia_card_type_repo.db.add(req.to_dict())

        return resp(HTTPStatus.OK, fia_card_type.to_dict(), "Succesfully")
    
    @BaseController.route(
        path="/<fia_card_type_id>",
        methods=["PUT"],
        request=UpdateFiaCardTypeIdRequestAuth,
        response=UpdateFiaCardTypeIdResponse
    )
    def update_fia_card_type_by_id(self, req: UpdateFiaCardTypeIdRequestAuth, resp:UpdateFiaCardTypeIdResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        
        fia_card_type_repo = self.load_repository(FIACardTypeModel)

        fia_card_type_model = fia_card_type_repo.db.get_by_id(req.fia_card_type_id)

        if (fia_card_type_model.type != req.type or fia_card_type_model.description != req.description):
            fia_temp = fia_card_type_repo.db.get_by(type=req.type, description=req.description)

            if fia_temp is not None and fia_temp.id  != req.fia_card_type_id:
                return resp(HTTPStatus.CONFLICT, message="Fia Card Type already exists")
        
        fia_card_type_model = fia_card_type_repo.db.update_by_id(id=req.fia_card_type_id, data={"type": req.type, "description": req.description})

        return resp(HTTPStatus.OK, fia_card_type_model.to_dict(), "Succesfully")
    
    @BaseController.route(
        path="/<fia_card_type_id>",
        methods=["DELETE"],
        request=DeleteFiaCardTypeIdRequestAuth,
        response=DeleteFiaCardTypeIdResponse
    )
    def delete_fia_card_type_by_id(self, req: DeleteFiaCardTypeIdRequestAuth, resp:DeleteFiaCardTypeIdResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        if not self.load_repository(FIACardTypeModel).db.contains(id=req.fia_card_type_id):
            return resp(HTTPStatus.BAD_REQUEST, message="FiaCardType not exists")
        
        self.load_repository(FIACardTypeModel).db.remove_by_id(req.fia_card_type_id)

        return resp(HTTPStatus.OK, message="Delete Succesfully")