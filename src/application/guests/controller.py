from arcs_lib_pca.application import BaseController
from src.infrastructure.models import UserGuestModel
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase

from .requests import(
    GetGuestRequestAuth,
    GetAllGuestRequestAuth
)

from .responses import(
    GetGuestResponse,
    GetAllResponse
)

class GuestController(BaseController):
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllGuestRequestAuth,
        response=GetAllResponse)
    def get_all_guests(self, req: GetAllGuestRequestAuth, resp: GetAllResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        guest_rep = self.load_repository(UserGuestModel)
        subquery = QueryParamsUseCase.load(req.params)
        guest = guest_rep.db.with_query(subquery).paginate(req.page, req.per_page, load=["profile"])

        resp(200, guest, "Successfully")

    @BaseController.route(
        path="/<guest_id>",
        methods=["GET"],
        request=GetGuestRequestAuth,
        response=GetGuestResponse)
    def create_guest(self, req: GetGuestRequestAuth, resp: GetGuestResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        guest_rep = self.load_repository(UserGuestModel)
        guest = guest_rep.db.get_by_id(req.guest_id, load=["profile"])

        if not guest:
            return resp(404, {}, "Guest not found")

        resp(200, guest, "Successfully")