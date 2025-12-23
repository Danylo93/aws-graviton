from http import HTTPStatus
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.domain.value_objects import ProfilePermissions
from sqlalchemy import func

from src.domain.value_objects import UserData
from src.infrastructure.models import (
    AccessProfileModel,
    AddressModel,
    ConfigModel,
    ContactModel,
    PersonModel,
    UserModel,
    ProfileModel,
    UserGuestModel
)
from src.infrastructure.models.pilot_model import PilotModel
from src.use_case.access_profile import LoadAccessProfilesUseCase
from .requests import(
    GetAllPersonRequestAuth,
    GetPersonRequestAuth,
    GetPersonByDocRequestAuth,
    UpdatePersonRequestAuth,
    DeletePersonRequestAuth
)

from .responses import(
    PersonAllGetResponse,
    PersonGetResponse,
    PersonCreatedResponse,
    PersonGetByDocResponse,
    PersonUpdatedResponse,
    PersonDeletedResponse
)

class PersonController(BaseController):

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllPersonRequestAuth,
        response=PersonAllGetResponse)
    def get_all_peoples(self, req: GetAllPersonRequestAuth, resp: PersonAllGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        person_rep = self.load_repository(PersonModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        people = person_rep.db.with_query(subquery_params)\
            .paginate(req.page, req.per_page, 
                      load=[
                            "cba_card_type",
                            "fia_card_type",
                            "addresses",
                            "contacts",
                            "profiles",
                            "user",
                        ]
                    )

        if not people:
            return resp(HTTPStatus.NOT_FOUND, {}, "Person not found")

        return resp(HTTPStatus.OK, people, "Successfully")

    @BaseController.route(
        path="/<person_id>",
        methods=["GET"],
        request=GetPersonRequestAuth,
        response=PersonGetResponse)
    def get_person(self, req: GetPersonRequestAuth, resp: PersonGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        person_model = self.load_repository(PersonModel)\
                    .db.get_by_id(id=req.person_id)
        
        if not person_model:
            return resp(HTTPStatus.NOT_FOUND, {}, "Person not found")
        
        return resp(
                HTTPStatus.OK, 
                person_model.to_dict(
                    lazy_load=[
                            "cba_card_type",
                            "fia_card_type",
                            "addresses",
                            "contacts",
                            "profiles",
                            "user",
                        ]), 
                        "Successfully"
                )
    
    @BaseController.route(
        path="/<person_id>",
        methods=["PUT", "PATCH"],
        request=UpdatePersonRequestAuth,
        response=PersonUpdatedResponse
    )
    def update_person(self, req: UpdatePersonRequestAuth, resp:PersonUpdatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        person_repo = self.load_repository(PersonModel)

        if not (person_model := person_repo.db.get_by_id(req.person_id)):
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Person not found")

        person_model.first_name = req.first_name or person_model.first_name
        person_model.last_name = req.last_name or person_model.last_name
        person_model.full_name = req.full_name or person_model.full_name
        person_model.identification = req.identification or person_model.identification
        person_model.status = req.status or person_model.status
        person_model.pronoun = req.pronoun or person_model.pronoun
        person_model.social_name = req.social_name or person_model.social_name
        person_model.birth_date = req.birth_date or person_model.birth_date
        person_model.doc = req.doc or person_model.doc
        person_model.reg_doc = req.reg_doc or person_model.reg_doc
        person_model.passport = req.passport or person_model.passport
        person_model.birth_place = req.birth_place or person_model.birth_place
        person_model.blood_type = req.blood_type or person_model.blood_type
        person_model.medical_agreement = req.medical_agreement or person_model.medical_agreement
        person_model.weight = req.weight or person_model.weight
        person_model.height = req.height or person_model.height
        person_model.shirt_size = req.shirt_size or person_model.shirt_size
        person_model.shoe_size = req.shoe_size or person_model.shoe_size
        person_model.cba_card_code = req.cba_card_code or person_model.cba_card_code
        person_model.cba_card_type_id = req.cba_card_type_id or person_model.cba_card_type_id
        person_model.fia_card = req.fia_card or person_model.fia_card
        person_model.fia_card_type_id = req.fia_card_type_id or person_model.fia_card_type_id

        person_model = person_repo.db.update(person_model, id=req.person_id)

        if not person_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating person")

        return resp(HTTPStatus.OK, person_model, "Updated Succefully")

    @BaseController.route(
        path="/<person_id>",
        methods=["DELETE"],
        request=DeletePersonRequestAuth,
        response=PersonDeletedResponse
    )
    def delete_person(self, req: DeletePersonRequestAuth, resp:PersonDeletedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        person_repo = self.load_repository(PersonModel)
        user_repo = self.load_repository(UserModel)
        user_guest_repo = self.load_repository(UserGuestModel)
        profile_repo = self.load_repository(ProfileModel)

        if not person_repo.db.contains(id=req.person_id):
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Person not found")
        
        user_repo.db.remove(person_id=req.person_id)
        profiles = profile_repo.db.find(person_id=req.person_id)

        for profile in profiles:
            if hasattr(profile, "id"):
                profile_id=getattr(profile, "id")
                user_guest_repo.db.remove(profile_id=profile_id)
                ProfilePermissions.remove_in_redis(person_repo.redis, profile_id=profile_id)

        profile_repo.db.remove(person_id=req.person_id)
        person_model = person_repo.db.remove_by_id(req.person_id)
        
        
        return resp(HTTPStatus.OK, person_model, message="Person deleted successfully")
    
    @BaseController.route(
        path="/doc/<doc>/",
        methods=["GET"],
        request=GetPersonByDocRequestAuth,
        response=PersonGetByDocResponse
    )
    def get_person_by_doc(self, req: GetPersonByDocRequestAuth, resp: PersonGetByDocResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
    
        person_model = self.load_repository(PersonModel).db.get_by(filters=[func.regexp_replace(PersonModel.doc, r'[^0-9]', '', 'g') == req.doc])
        
        if not person_model:
            return resp(HTTPStatus.NOT_FOUND, {}, "Person not found")
        
        profile_model = self.load_repository(ProfileModel).db.get_by(person_id=person_model.id)

        #profile_model = person_model.profiles[0] if person_model.profiles and len(person_model.profiles) > 0 else None

        if not profile_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Profile not found")

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