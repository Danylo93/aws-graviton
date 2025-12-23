from http import HTTPStatus

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.domain import AccessProfile
from arcs_lib_pca.use_case import execute_use_case
from pydantic import EmailStr

from src.domain.value_objects import UserData, UserMetadataVO, MetaDataEmailVO
from src.infrastructure.models import (
    AccessProfileModel,
    AddressModel,
    ConfigModel,
    ContactModel,
    PersonModel,
    ProfileModel,
    SubGroupModel,
    UserModel
)
from src.infrastructure.models.pilot_model import PilotModel
from src.use_case.access_profile import LoadAccessProfilesUseCase
from src.use_case.profile import LoadProfileUseCase
from .requests import (
    GetUserRequestAuth,
    PilotGetUserRequestAuth,
    PilotUpdateUserRequestAuth,
    UpdateUserRequestAuth, UpsertUserEmailsRequestAuth, GetUserEmailsRequestAuth,
    GetUserByEmailRequestAuth
)
from .responses import (
    GetUserResponse,
    UpdateUserResponse, UpsertUserEmailResponse, GetUserEmailsResponse, DeleteUserEmailResponse, GetUserByEmailResponse
)
from ...utils.user_utils import get_user_by_email


# TODO: REMOVER ESSA DUPLICAÇÃO DE ENDPOINTS, ELA SÓ EXISTE PARA NÃO DAR PROBLEMA NO MOBILE V1
class UserController(BaseController):

    @BaseController.route(
        path="<path:user_id>/profiles/<path:profile_id>",
        methods=["GET"],
        request=PilotGetUserRequestAuth,
        response=GetUserResponse)
    def get_mobile_user(self, req: PilotGetUserRequestAuth, resp: GetUserResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        user_model = self.load_repository(UserModel).db.get_by_id(req.user_id)

        if not user_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")

        profile_model = self.load_repository(ProfileModel).db.get_by_id(req.profile_id)

        if not profile_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Profile not found")

        if user_model.person_id != profile_model.person_id:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Incompatible profile and user")

        person_model = self.load_repository(PersonModel).db.get_by_id(id=profile_model.person_id)

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, profile_id=profile_model.id)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        _, access_profiles_list = next(iter(access_profiles.items()))

        access_profile: AccessProfileModel = None

        if access_profiles_list and len(access_profiles_list) > 0:
            access_profile = access_profiles_list[0].to_dict()

        contacts = self.load_repository(ContactModel).db.find(person_id=profile_model.person_id)
        addresses = self.load_repository(AddressModel).db.find(person_id=profile_model.person_id)
        profile_config = self.load_repository(ConfigModel).db.get_by(profile_id=profile_model.id)
        pilot_model = self.load_repository(PilotModel).db.get_by(profile_id=profile_model.id)

        data = UserData(
            email=user_model.email,
            person=person_model.to_dict(),
            access_profile=access_profile,
            contacts=list(map(lambda x: x.to_dict(), contacts)),
            addresses=list(map(lambda x: x.to_dict(), addresses)),
            profile=profile_model.to_dict(),
            pilot=pilot_model.to_dict() if pilot_model else {},
            config=profile_config.to_dict() if profile_config else {}
        )

        return resp(status_code=HTTPStatus.OK, body=data.model_dump(), message="Request Succefully")

    @BaseController.route(
        path="<path:user_id>/profiles/<path:profile_id>",
        methods=["PUT"],
        request=PilotUpdateUserRequestAuth,
        response=UpdateUserResponse)
    def update_mobile_user(self, req: PilotUpdateUserRequestAuth, resp: UpdateUserResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        subgroup_model = self.load_repository(SubGroupModel).db.get_by_id(id=req.subgroup_id)

        if not subgroup_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Subgroup not found")

        profile_model = self.load_repository(ProfileModel).db.get_by_id(req.profile_id)

        if not profile_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Profile not found")

        user_model = self.load_repository(UserModel).db.get_by_id(req.user_id)

        if not user_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")

        if user_model.person_id != profile_model.person_id:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Incompatible profile and user")

        if user_model.email != req.email:
            return resp(status_code=HTTPStatus.CONFLICT, message="Email cannot be changed")

            # Atualizar person
        person_model: PersonModel = self.load_repository(PersonModel).db.get_by_id(profile_model.person_id)

        person_model.merge_person_base(req.person)

        person_model = self.load_repository(PersonModel).db.update_by_id(id=person_model.id, data=person_model)

        # Atualizar profile
        profile_description = None
        profile_picture = None
        profile_permissions = None

        if req.profile:
            profile_description = req.profile.description
            profile_picture = req.profile.pictures
            profile_permissions = req.profile.permissions

        profile_model: ProfileModel = self.exec_use_case(LoadProfileUseCase,
                                                         person=person_model,
                                                         profile_id=profile_model.id,
                                                         subgroup_id=req.subgroup_id,
                                                         profile_description=profile_description,
                                                         profile_picture=profile_picture,
                                                         profile_permissions=profile_permissions
                                                         )

        user_model = self.load_repository(UserModel).db.get_by(person_id=person_model.id)

        if not user_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, profile_id=profile_model.id)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        _, access_profiles_list = next(iter(access_profiles.items()))

        access_profile: AccessProfileModel = None

        if access_profiles_list and len(access_profiles_list) > 0:
            access_profile = access_profiles_list[0].to_dict()

        self.load_repository(AccessProfileModel).db.update(profile_id=access_profile['profile_id'], data=access_profile)

        profile_config = self.load_repository(ConfigModel).db.get_by(profile_id=profile_model.id)

        if req.contacts:
            for contact in req.contacts:
                if contact.id and self.load_repository(ContactModel).db.contains(id=contact.id):
                    self.load_repository(ContactModel).db.update_by_id(id=contact.id, data=contact.model_dump())
                else:
                    data = contact.model_dump()
                    data['person_id'] = person_model.id
                    self.load_repository(ContactModel).db.add(data=data)

        contacts = self.load_repository(ContactModel).db.find(person_id=person_model.id)

        if req.address:
            address_repo = self.load_repository(AddressModel)
            address_data = req.address.model_dump()
            address_data['person_id'] = person_model.id

            if address_repo.db.contains(id=req.address.id, person_id=person_model.id):
                address_repo.db.update_by_id(id=req.address.id, data=address_data)
            else:
                address_repo.db.add(address_data)

        addresses = self.load_repository(AddressModel).db.find(person_id=person_model.id)
        pilot_model = self.load_repository(PilotModel).db.get_by(profile_id=profile_model.id)

        data = UserData(
            email=user_model.email,
            person=person_model.to_dict(),
            access_profile=access_profile,
            contacts=list(map(lambda x: x.to_dict(), contacts)),
            addresses=list(map(lambda x: x.to_dict(), addresses)),
            profile=profile_model.to_dict(),
            pilot=pilot_model.to_dict() if pilot_model else {},
            config=profile_config.to_dict() if profile_config else {}
        )

        return resp(HTTPStatus.OK, data.model_dump(), "Request Succefully")

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetUserRequestAuth,
        response=GetUserResponse)
    def get_mobile_user(self, req: GetUserRequestAuth, resp: GetUserResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        profile_model = self.load_repository(ProfileModel).db.get_by_id(req.profile_id)

        if not profile_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Profile not found")

        person_model = self.load_repository(PersonModel).db.get_by_id(id=profile_model.person_id)

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, profile_id=profile_model.id)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        _, access_profiles_list = next(iter(access_profiles.items()))

        access_profile: AccessProfileModel = None

        if access_profiles_list and len(access_profiles_list) > 0:
            access_profile = access_profiles_list[0].to_dict()

        contacts = self.load_repository(ContactModel).db.find(person_id=profile_model.person_id)
        addresses = self.load_repository(AddressModel).db.find(person_id=profile_model.person_id)
        profile_config = self.load_repository(ConfigModel).db.get_by(profile_id=profile_model.id)
        pilot_model = self.load_repository(PilotModel).db.get_by(profile_id=profile_model.id)

        data = UserData(
            email=access_profile["email"] if access_profile else None,
            person=person_model.to_dict(),
            access_profile=access_profile,
            contacts=list(map(lambda x: x.to_dict(), contacts)),
            addresses=list(map(lambda x: x.to_dict(), addresses)),
            profile=profile_model.to_dict(),
            pilot=pilot_model.to_dict() if pilot_model else {},
            config=profile_config.to_dict() if profile_config else {}
        )

        return resp(status_code=HTTPStatus.OK, body=data.model_dump(), message="Request Succefully")

    @BaseController.route(
        path="/",
        methods=["PUT"],
        request=UpdateUserRequestAuth,
        response=UpdateUserResponse)
    def update_user(self, req: UpdateUserRequestAuth, resp: UpdateUserResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        subgroup_model = self.load_repository(SubGroupModel).db.get_by_id(id=req.subgroup_id)

        if not subgroup_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Subgroup not found")

        profile_model = self.load_repository(ProfileModel).db.get_by_id(req.profile_id)

        if not profile_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Profile not found")

        # Atualizar person
        person_model: PersonModel = self.load_repository(PersonModel).db.get_by_id(profile_model.person_id)

        person_model.merge_person_base(req.person)

        person_model = self.load_repository(PersonModel).db.update_by_id(id=person_model.id, data=person_model)

        # Atualizar profile
        profile_description = None
        profile_picture = None
        profile_permissions = None

        if req.profile:
            profile_description = req.profile.description
            profile_picture = req.profile.pictures
            profile_permissions = req.profile.permissions

        profile_model: ProfileModel = self.exec_use_case(LoadProfileUseCase,
                                                         person=person_model,
                                                         profile_id=profile_model.id,
                                                         subgroup_id=req.subgroup_id,
                                                         profile_description=profile_description,
                                                         profile_picture=profile_picture,
                                                         profile_permissions=profile_permissions,
                                                         merge=False
                                                         )

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, profile_id=profile_model.id)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        _, access_profiles_list = next(iter(access_profiles.items()))

        access_profile: AccessProfileModel = None

        if access_profiles_list and len(access_profiles_list) > 0:
            access_profile = access_profiles_list[0].to_dict()

        self.load_repository(AccessProfileModel).db.update(profile_id=access_profile['profile_id'], data=access_profile)

        profile_config = self.load_repository(ConfigModel).db.get_by(profile_id=profile_model.id)

        if req.contacts:
            for contact in req.contacts:
                if contact.id and self.load_repository(ContactModel).db.contains(id=contact.id):
                    self.load_repository(ContactModel).db.update_by_id(id=contact.id, data=contact.model_dump())
                else:
                    data = contact.model_dump()
                    data['person_id'] = person_model.id
                    self.load_repository(ContactModel).db.add(data=data)

        contacts = self.load_repository(ContactModel).db.find(person_id=person_model.id)

        if req.address:
            address_repo = self.load_repository(AddressModel)
            address_data = req.address.model_dump()
            address_data['person_id'] = person_model.id

            if address_repo.db.contains(id=req.address.id, person_id=person_model.id):
                address_repo.db.update_by_id(id=req.address.id, data=address_data)
            else:
                address_repo.db.add(address_data)

        addresses = self.load_repository(AddressModel).db.find(person_id=person_model.id)
        pilot_model = self.load_repository(PilotModel).db.get_by(profile_id=profile_model.id)


        data = UserData(
            email=access_profile["email"] if access_profile else None,
            person=person_model.to_dict(),
            access_profile=access_profile,
            contacts=list(map(lambda x: x.to_dict(), contacts)),
            addresses=list(map(lambda x: x.to_dict(), addresses)),
            profile=profile_model.to_dict(),
            pilot=pilot_model.to_dict() if pilot_model else {},
            config=profile_config.to_dict() if profile_config else {}
        )

        return resp(HTTPStatus.OK, data.model_dump(), "Request Succefully")

    @BaseController.route(
        path="/by-email/",
        methods=["GET"],
        request=GetUserByEmailRequestAuth,
        response=GetUserByEmailResponse)
    def get_user_by_email(self, req: GetUserByEmailRequestAuth, resp: GetUserByEmailResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        user = get_user_by_email(self.load_repository(UserModel), req.email)

        if not user:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")

        return resp(HTTPStatus.OK, message="Request Succefully")

    @BaseController.route(
        path="/<path:user_id>/emails/",
        methods=["POST"],
        request=UpsertUserEmailsRequestAuth,
        response=UpsertUserEmailResponse)
    def upsert_user_emails(self, req: UpsertUserEmailsRequestAuth, resp: UpsertUserEmailResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        main_emails_count = sum(1 for email in req.emails if email.is_main)

        if main_emails_count > 1:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Can't have more than one main email")

        if main_emails_count == 0:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Must have one main email")

        user_repository = self.load_repository(UserModel)
        user: UserModel = user_repository.db.get_by_id(req.user_id)

        if not user:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")

        for email in req.emails:

            user_by_email = get_user_by_email(user_repository, email.email)

            if user_by_email and user_by_email.id != user.id:
                return resp(status_code=HTTPStatus.CONFLICT, message="Email is already in use")

        metadata = UserMetadataVO(**user.meta_data)

        main_email = next((email for email in req.emails if email.is_main))

        metadata.emails = [MetaDataEmailVO(email=user_email.email) for user_email in req.emails if not user_email.is_main]

        user_repository.db.update_by_id(id=user.id, data={'email': main_email.email, 'meta_data': metadata.model_dump()})

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, person_id=user.person_id)

        for ac in access_profiles.values():
            for access_profile in ac:
                # Atualiza o email principal do access profile
                main_email = next((email for email in req.emails if email.is_main), None)

                if main_email:
                    access_profile.email = main_email.email

                self.load_repository(AccessProfileModel).db.update(access_profile.to_dict(), profile_id=access_profile.profile_id)

                access_profile.upsert_in_redis(self.get_redis())

        return resp(HTTPStatus.OK, req.emails, message="Email added successfully")

    @BaseController.route(
        path="/<path:user_id>/emails/",
        methods=["GET"],
        request=GetUserEmailsRequestAuth,
        response=GetUserEmailsResponse)
    def get_user_emails(self, req: GetUserEmailsRequestAuth, resp: GetUserEmailsResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        user: UserModel = self.load_repository(UserModel).db.get_by_id(req.user_id)

        if not user:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="User not found")

        metadata = UserMetadataVO(**user.meta_data)

        classified_emails = [{'email': email.email, 'is_main': False} for email in metadata.emails]
        classified_emails.insert(0, {'email': user.email, 'is_main': True})

        return resp(HTTPStatus.OK, classified_emails, message="Request Succefully")
