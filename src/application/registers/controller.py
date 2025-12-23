from http import HTTPStatus
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.use_case import execute_use_case

from src.use_case import RegisterUserUseCase

from .requests import(
    RegisterAccountRequest,
)

from .responses import(
    GetRegisterResponse
)

class RegisterController(BaseController):
    @BaseController.route(
        path="/",
        methods=["POST"],
        request=RegisterAccountRequest,
        response=GetRegisterResponse)
    def register_accounts_user(self, req: RegisterAccountRequest, resp: GetRegisterResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        r = execute_use_case(
            RegisterUserUseCase,
            email=req.email,
            person=req.person,
            password=req.password,
            registration_page_url=req.registration_page_url,
            user_guest_id=req.user_guest_id,
            subgroup_id=req.subgroup_id,
            profile=req.profile,
            contacts=req.contacts,
            address=req.address,
        )
        
        return resp(r.http_status, r.data, r.message)