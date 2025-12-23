from http import HTTPStatus

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.domain import AppClientPermissions
from arcs_lib_pca.use_case import execute_use_case

from src.infrastructure.models import AccessProfileModel
from src.infrastructure.models.user_model import UserModel
from src.use_case.access_profile import LoadAccessProfilesUseCase
from .requests import(
    GetAccessProfileAuth,
    GetAllAccessProfileAuth,
    GetAccessProfilesByUserIDRequestAuth
)
from .responses import(
    AccessProfileAllGetResponse,
    AccessProfileGetResponse,
    GetAccessProfilesByUserIDResponse
)

class AccessProfilesController(BaseController):
    
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllAccessProfileAuth,
        response=AccessProfileAllGetResponse)
    def get_all_access_profile(self, req: GetAllAccessProfileAuth, resp: AccessProfileAllGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        app_repo = self.load_repository(AccessProfileModel)
        subquery = QueryParamsUseCase.load(req.params)
        data = app_repo.db.with_query(subquery).paginate(page=req.page, per_page=req.per_page)

        return resp(HTTPStatus.OK, data, "Request Succefully")

    @BaseController.route(
        path="/<path:profile_id>",
        methods=["GET"],
        request=GetAccessProfileAuth,
        response=AccessProfileGetResponse)
    def get_access_profile(self, req: GetAccessProfileAuth, resp: AccessProfileGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        ap_repo = self.load_repository(AccessProfileModel)
        ap_model = ap_repo.db.get_by(profile_id=req.profile_id)

        if not ap_model:
            return resp(HTTPStatus.NOT_FOUND, {}, f"Access profile: not found")
        
        return resp(HTTPStatus.OK, ap_model.to_dict(), "Request Succefully")
    
    @BaseController.route(
        path="/users/<path:user_id>",
        methods=["GET"],
        request=GetAccessProfilesByUserIDRequestAuth,
        response=GetAccessProfilesByUserIDResponse)
    def get_access_profiles_by_user_id(self, req: GetAccessProfilesByUserIDRequestAuth, resp: GetAccessProfilesByUserIDResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        # Validação do Profile
        user_model = self.load_repository(UserModel).db.get_by_id(req.user_id)

        if not user_model:
            return resp(HTTPStatus.NOT_FOUND, message="User not found")
        
        app_client = req.header.get("X-App-Client")
        app_client_permissions = None

        if app_client:
            app_client = to_snake_case(app_client)

            app_client_permissions = AppClientPermissions.get_of_redis(self.get_redis(), app_client, self.app.settings.microservice_name)

        # Validação do AccessProfile
        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, user_id=user_model.id, app_client_permissions=app_client_permissions)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")
    
        _, access_profiles_list = next(iter(access_profiles.items()))
        
        return resp(HTTPStatus.OK, access_profiles_list or [], "Request Succefully")
