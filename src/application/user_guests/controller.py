from http import HTTPStatus
from arcs_lib_pca.application import BaseController
from src.infrastructure.models.user_guest_model import UserGuestModel
from .requests import(
    GetUserGuestRequest
)
from .responses import(
    GetUserGuestResponse
)


class UserGuestController(BaseController):
    
    @BaseController.route(
        path="<path:user_guest_id>",
        methods=["GET"],
        request=GetUserGuestRequest,
        response=GetUserGuestResponse)
    def get_user_guest(self, req: GetUserGuestRequest, resp: GetUserGuestResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        user_guest_model = self.load_repository(UserGuestModel).db.get_by_id(req.user_guest_id, load=['profile'])

        if not user_guest_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")
        

        return resp(HTTPStatus.OK, user_guest_model.to_dict(lazy_load=['profile']), "Success")