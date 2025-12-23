import json
import typing as t

from http import HTTPStatus

from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.domain import AppClientPermissions, DateTime, AccessProfile
from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.tools.security.repository import TokenJwt

from src.domain.value_objects import ProfileVO
from src.infrastructure.models import (
    ProfileModel,
    AccessProfileModel,
    ConfigModel,
    UserGuestModel
)

from src.infrastructure.models.group_model import GroupModel
from src.infrastructure.models.pilot_model import PilotModel
from src.infrastructure.models.subgroup_model import SubGroupModel
from src.infrastructure.models.user_model import UserModel
from src.use_case.access_profile import LoadAccessProfilesUseCase
from src.use_case.profile import LoadProfileUseCase

from .requests import(
    UpdateProfileRequestAuth,
    GetProfileRequestAuth,
    GetProfileIdRequestAuth,
    DeleteProfileRequestAuth,
    GenerateTokenRequestAuth
)

from .responses import(
    GetProfileResponse,
    GetUniqueProfileResponse,
    UpdateProfileResponse,
    DeleteProfileResponse,
    GenerateTokenResponse
)

class ProfileController(BaseController):
    _SCORES = {
            'get': 1,
            'post': 2,
            'put': 2,
            'delete': 3
        }
    
    _TOKEN_EXP_DURATION = 24*60

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetProfileRequestAuth,
        response=GetUniqueProfileResponse
    )
    def get_list_profiles(self, req: GetProfileRequestAuth, resp:GetUniqueProfileResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        profile_repo = self.load_repository(ProfileModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        
        profile = None
        
        if not req.group_name and req.subgroup_name:            
            subgroup_model = self.load_repository(SubGroupModel).db.get_by(name=req.subgroup_name)

            subgroup_id = subgroup_model.id if subgroup_model else None
            
            profile = profile_repo.db.with_query(subquery_params).paginate(req.page, req.per_page, subgroup_id=subgroup_id, load=["person", "subgroup", "creator", "deletor", "updator"])

        elif req.group_name:
            group_model = self.load_repository(GroupModel).db.get_by(name=req.group_name)

            group_id = group_model.id if group_model else None

            if req.subgroup_name:
                subgroup_model = self.load_repository(SubGroupModel).db.get_by(name=req.subgroup_name)

                subgroup_id = subgroup_model.id if subgroup_model else None

                profile = profile_repo.db.with_query(subquery_params).paginate(req.page, req.per_page, group_id=group_id, subgroup_id=subgroup_id, load=["person", "subgroup", "creator", "deletor", "updator"])
            else:
                profile = profile_repo.db.with_query(subquery_params).paginate(req.page, req.per_page, group_id=group_id, load=["person", "subgroup", "creator", "deletor", "updator"])
        else:
            profile = profile_repo.db.with_query(subquery_params).paginate(req.page, req.per_page,  load=["person", "subgroup", "creator", "deletor", "updator"])


        items = profile.get('items')
        
        profiles_vos = []
        
        if items:
            for item in items:
                profile_vo = self._convert_profile_dict_to_profile_vo(item)
                profiles_vos.append(profile_vo.to_dict())

        if profiles_vos:
            profile['items'] = profiles_vos

        return resp(HTTPStatus.OK, profile, "Succesfully")

    @BaseController.route(
        path="/<path:profile_id>",
        methods=["GET"],
        request=GetProfileIdRequestAuth,
        response=GetProfileResponse
    )
    def get_profile_by_id(self, req: GetProfileIdRequestAuth, resp:GetProfileResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        profile_repo = self.load_repository(ProfileModel)

        profile_model = profile_repo.db.get_by_id(id=req.profile_id, load=["creator", "updator", "deletor"])

        if not profile_model:
            return resp(HTTPStatus.BAD_REQUEST, message="Profile not exists")

        profile_dict = profile_model.to_dict(lazy_load=["person", "subgroup", "creator", "updator", "deletor"])

        profile_vo = self._convert_profile_dict_to_profile_vo(profile_dict)

        return resp(HTTPStatus.OK, profile_vo.to_dict(), "Succesfully")

    @BaseController.route(
        path="/<path:profile_id>/generate_token/",
        methods=['POST'],
        request=GenerateTokenRequestAuth,
        response=GenerateTokenResponse
    )
    def generate_token(self, req: GenerateTokenRequestAuth, resp: GenerateTokenResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        # Validação do App Client
        app_client = req.header.get("X-App-Client")

        if not app_client:
            return resp(HTTPStatus.BAD_REQUEST, message="client app undefined")
        
        app_client = to_snake_case(app_client)

        if not (app_client_permissions := AppClientPermissions.get_of_redis(self.get_redis(), app_client, self.app.settings.microservice_name)):
            return resp(HTTPStatus.BAD_REQUEST, message="client app not found")

        # Validação do Profile
        profile_model = self.load_repository(ProfileModel).db.get_by_id(req.profile_id)

        if not profile_model:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")

        if profile_model.person.user.id != req.current_profile.user_id:
            return resp(HTTPStatus.UNAUTHORIZED,  message="User unauthorized")

        # Validação do AccessProfile
        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, profile_id=profile_model.id, app_client_permissions=app_client_permissions)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")
    
        _, access_profiles_list = next(iter(access_profiles.items()))

        if not access_profiles_list:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        access_profile = access_profiles_list[0]

        token_jwt = TokenJwt.from_access_profile(
                    settings=self._app.settings,
                    access_profile=access_profile,
                    aud=app_client,
                    exp_minutes=self._TOKEN_EXP_DURATION
                )

        ap_repo = self.load_repository(AccessProfileModel)
        if ap_repo.db.contains(profile_id=access_profile.profile_id):
            ap_repo.db.update(access_profile.to_dict(), profile_id=access_profile.profile_id)
        else:
            ap_repo.db.add(access_profile.to_dict())

        access_profile.upsert_in_redis(ap_repo.redis)

        self.load_repository(ProfileModel).db.update_by_id(
            id = access_profile.profile_id,
            data = {"last_access": DateTime.now()}
        )

        return resp(HTTPStatus.OK, {
                "token": token_jwt.encode_token(self._app.settings)
        })

    @BaseController.route(
        path="/<profile_id>",
        methods=["PUT"],
        request=UpdateProfileRequestAuth,
        response=UpdateProfileResponse
    )
    def update_profile(self, req: UpdateProfileRequestAuth, resp:UpdateProfileResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        profile_repo = self.load_repository(ProfileModel)
        
        profile_model = profile_repo.db.get_by_id(id=req.profile_id, load=['person'])

        if not profile_model:
            return resp(HTTPStatus.BAD_REQUEST, message="Profile not exists")
        
        applicant = profile_repo.db.get_by_id(req.current_profile.profile_id)
        
        if applicant and not self._compare_profiles(applicant, profile_model):
            return resp(HTTPStatus.UNAUTHORIZED, message="Insufficient profile access level")

        profile_data = {
            "description": req.description,
            "pictures": req.pictures,
            "permissions": req.profile_permissions,
        }

        profile_model : ProfileModel = self.exec_use_case(LoadProfileUseCase,                  
                                        person=profile_model.person,
                                        profile_id=profile_model.id,
                                        profile_description=profile_data['description'],
                                        profile_picture=profile_data['pictures'],
                                        profile_permissions=profile_data['permissions']
                                        )
        
        if not profile_model:
            return resp(HTTPStatus.BAD_REQUEST, message="Error to update profile")

        return resp(HTTPStatus.OK, profile_model.to_dict(), message="Request Sucessfully")

    @BaseController.route(
        path="/<path:profile_id>",
        methods=["DELETE"],
        request=DeleteProfileRequestAuth,
        response=DeleteProfileResponse
    )
    def delete_profile(self, req: DeleteProfileRequestAuth, resp:DeleteProfileResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        
        profile_repo = self.load_repository(ProfileModel)
        
        profile_model = profile_repo.db.get_by_id(req.profile_id)
        if not profile_model:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")
        
        applicant = profile_repo.db.get_by_id(req.current_profile.profile_id)
        
        if applicant and not self._compare_profiles(applicant, profile_model):
            return resp(HTTPStatus.UNAUTHORIZED, message="Insufficient profile access level")
        
        self.load_repository(AccessProfileModel).db.delete(profile_id=req.profile_id)
        self.load_repository(ConfigModel).db.remove(profile_id=req.profile_id)
        self.load_repository(UserGuestModel).db.remove(profile_id=req.profile_id)

        self.load_repository(PilotModel).db.delete(profile_id=req.profile_id)
        
        profile_repo.db.delete(id=req.profile_id)

        return resp(HTTPStatus.OK, {}, message="Request Sucessfully")

    @BaseController.route(
        path="/<path:profile_id>/pictures/<path:key>/",
        methods=["DELETE"],
        request=DeleteProfileRequestAuth,
        response=DeleteProfileResponse
    )
    def delete_profile(self, req: DeleteProfileRequestAuth, resp: DeleteProfileResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")

        profile: ProfileModel | None = self.load_repository(ProfileModel).db.get_by_id(req.profile_id)

        if not profile:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")

        if not profile.pictures or req.key not in profile.pictures:
            return resp(HTTPStatus.NOT_FOUND, message="Profile picture not found")

        profile.pictures.pop(req.key)

        self.load_repository(ProfileModel).db.upsert(profile.to_dict(), id=profile.id)

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, profile_id=profile.id)

        access_profile: AccessProfile = access_profiles[profile.person_id][0]

        if not access_profile:
            return resp(HTTPStatus.NOT_FOUND, message="Access profile not found")

        access_profile.profile_picture = profile.pictures

        self.load_repository(AccessProfileModel).db.upsert(access_profile.to_dict(), profile_id=profile.id)

        access_profile.upsert_in_redis(self.get_redis())

        return resp(HTTPStatus.OK, {}, message="Picture deleted successfully")
    
    def _compare_profiles(self, applicant: ProfileModel, target: ProfileModel):
        if applicant.id == target.id:
            return True
    
        applicant_score = self._get_score(applicant) 
        target_score = self._get_score(target) 
        return applicant_score > target_score

    def _get_score(self, profile: ProfileModel):
        score = 0
        for permissions in profile.permissions:
            if not permissions.get('service'):
                continue

            service_score = self._base_permission_pontuation(permissions.get('service'))
            score += service_score

            if not permissions.get('controllers'):
                continue

            for ctr in permissions.get('controllers'):
                ctr_score = self._base_permission_pontuation(ctr)

                score += ctr_score
        
        return score

    def _base_permission_pontuation(self, base_permission):
        score = 0

        for key, value in self._SCORES.items():
            if base_permission.get(key):
                score += value
                
        return score
    
    def _convert_profile_dict_to_profile_vo(self, profile_dict: t.Dict) -> ProfileVO:
        person_id = profile_dict['person_id']
        user_model = self.load_repository(UserModel).db.get_by(person_id=person_id)
        
        email = None

        if user_model:
            email = user_model.email
        else:
            user_guest_model = self.load_repository(UserGuestModel).db.get_by(profile_id=profile_dict['id'])

            if user_guest_model:
                email = user_guest_model.email

        
        name = profile_dict['person']['full_name']
        group_id = profile_dict['subgroup']['group_id']
        subgroup_name = profile_dict['subgroup']['name']
        group_model = self.load_repository(GroupModel).db.get_by_id(group_id)

        profile_vo = ProfileVO(
            **profile_dict,
            email=email or "",
            group_name=group_model.name,
            name=name,
            subgroup_name=subgroup_name
        )

        return profile_vo