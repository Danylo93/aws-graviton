from http import HTTPStatus

from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.application import BaseController

from src.infrastructure.models import ContactTypeModel
from .requests import(
    GetContactTypeRequestAuth,
    GetContactTypeIdRequestAuth
)

from .responses import(
    GetContactTypeResponse,
    GetUniqueContactTypeResponse
)

class ContactTypeController(BaseController):
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetContactTypeRequestAuth,
        response=GetUniqueContactTypeResponse
    )
    def get_list_contact_types(self, req: GetContactTypeRequestAuth, resp:GetUniqueContactTypeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        contact_type_repo = self.load_repository(ContactTypeModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        contact_type = contact_type_repo.db.with_query(subquery_params).paginate(req.page, req.per_page)

        return resp(HTTPStatus.OK, contact_type, "Succesfully")

    @BaseController.route(
        path="/<contact_type_id>",
        methods=["GET"],
        request=GetContactTypeIdRequestAuth,
        response=GetContactTypeResponse
    )
    def get_contact_type_by_id(self, req: GetContactTypeIdRequestAuth, resp:GetContactTypeResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        contact_type_repo = self.load_repository(ContactTypeModel)
        contact_type_model = contact_type_repo.db.get_by_id(id=req.contact_type_id)

        if not contact_type_model:
            return resp(HTTPStatus.BAD_REQUEST, message="ContactType not exists")

        return resp(HTTPStatus.OK, contact_type_model, "Succesfully")
    
    #TODO: Finalizar o CRUD