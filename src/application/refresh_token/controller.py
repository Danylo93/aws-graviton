import typing as t
from http import HTTPStatus

from urllib.parse import urlparse, urlencode, urlunparse, ParseResult
from pydantic import HttpUrl

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.tools.security.repository import TokenJwt
from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.domain import DateTime, AppClientPermissions, GenericUUID, AccessProfile
from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.tools.notify import Notification, TargetNotification, EmailDynamicData

from src.infrastructure.models import UserModel, ProfileModel, PersonModel, AccessProfileModel
from src.use_case import LoadAccessProfilesUseCase, TokenProviderUseCase, TokenProvider, RegisterUserUseCase
from src.domain.value_objects import PersonBase
from .requests import(
    RefreshTokenRequestAuth,
)

from .responses import(
    RefreshTokenResponse,
)

class RefreshTokenController(BaseController):

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=RefreshTokenRequestAuth,
        response=RefreshTokenResponse)
    def refresh_token(self, req: RefreshTokenRequestAuth, resp: RefreshTokenResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        app_client = req.header.get("X-App-Client")

        if not app_client:
            return resp(HTTPStatus.BAD_REQUEST, message="client app undefined")
        
        app_client = to_snake_case(app_client)

        if not AppClientPermissions.contains_in_redis(self.get_redis(), app_client, self.app.settings.microservice_name):
            return resp(HTTPStatus.BAD_REQUEST,
                    {
                        "required_login": True,
                        "token": None
                    },
                    message="client app not found")

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, profile_id=req.current_profile.profile_id)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, 
                    {
                        "required_login": True,
                        "token": None
                    },
                    message="Your access has expired, please log in again")

        person_id, access_profiles_list = next(iter(access_profiles.items()))

        if not access_profiles_list:
            return resp(HTTPStatus.UNAUTHORIZED,
                    {
                        "required_login": True,
                        "token": None
                    },
                    message="Your access has expired, please log in again")

        access_profile = access_profiles_list[0]

        token_jwt = TokenJwt.from_access_profile(
                    settings=self._app.settings,
                    access_profile=access_profile,
                    aud=app_client,
                    exp_minutes=24*60
                )

        ap_repo = self.load_repository(AccessProfileModel, access_profile.to_dict())
        ap_repo.db.upsert(profile_id=access_profile.profile_id)
        access_profile.upsert_in_redis(ap_repo.redis)

        self.load_repository(ProfileModel).db.update_by_id(
            id = access_profile.profile_id,
            data = {"last_access": DateTime.now()}
        )

        return resp(HTTPStatus.OK, {
            "required_login": False,
            "token": token_jwt.encode_token(self._app.settings)
        })


