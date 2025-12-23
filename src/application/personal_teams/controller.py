from http import HTTPStatus
import typing as t
from pydantic import HttpUrl
from urllib.parse import urlparse, urlencode, urlunparse, ParseResult
from src.infrastructure.models import (
    PersonalTeamMemberModel,
    PersonalTeamStatus,
    SubGroupModel,
    ProfileModel,
    PersonModel,
    UserModel,
    ContactModel,
    UserGuestModel,
    AccessProfileModel,
    ContactTypeModel,
    ConfigModel
)

from arcs_lib_pca.tools.notify import Notification, TargetNotification, EmailDynamicData
from arcs_lib_pca.domain import AccessProfile, DateTime, GenericUUID
from arcs_lib_pca.application import BaseController
from src.use_case.profile import LoadProfileUseCase
from src.use_case.access_profile import LoadAccessProfilesUseCase
from arcs_lib_pca.tools.security.repository import TokenJwt

from .requests import(
    GetAPersonalTeamsByPilotIdRequestAuth,
    GetPersonalTeamIdWithMemberIdRequestAuth,
    UpdatePersonalTeamIdWithMemberIdRequestAuth,
    CreatePersonalTeamByPilotIdRequestAuth,
    DeletePersonalTeamIdWithMemberIdRequestAuth,
    UpdateMemberAcceptanceRequestAuth,
    GetPersonalTeamByMemberIdRequestAuth
)

from .responses import(
    PersonalTeamAllGetResponse,
    PersonalTeamGetByIdResponse,
    PersonalTeamCreatedResponse,
    PersonalTeamDeletedResponse,
    PersonalTeamUpdatedResponse,
    UpdateMemberAcceptanceResponse
)

class PersonalTeamController(BaseController):
    _EXPIRATION_TIME = 24*60

    @BaseController.route(
        path="/pilot/<path:pilot_id>",
        methods=["GET"],
        request=GetAPersonalTeamsByPilotIdRequestAuth,
        response=PersonalTeamAllGetResponse)
    def get_all_personal_teams(self, req: GetAPersonalTeamsByPilotIdRequestAuth,
                               resp: PersonalTeamAllGetResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        personal_team_rep = self.load_repository(PersonalTeamMemberModel)

        pilot_team = personal_team_rep.db.find(pilot_id=req.pilot_id)
        if not pilot_team:
            return resp(status_code=HTTPStatus.NOT_FOUND, body={},
                        message=f'Personal team not found for pilot_id: {req.pilot_id}')

        access_profile_data = {
            "pilot_id": req.pilot_id,
            'members': []
            }
        
        members = []

        for member in pilot_team:
            if req.subgroup_name and member.member.subgroup_name != req.subgroup_name:
                continue

            members.append({
                "access_profile": member.member,
                "member_acceptance": member.member_acceptance,
                "acceptance_status": member.acceptance_status,
                "member_rejection": member.member_rejection
            })

        access_profile_data['members'] = members

        return resp(HTTPStatus.OK, access_profile_data, "Successfully")

    @BaseController.route(
        path="/pilot/<path:pilot_id>",
        methods=["POST"],
        request=CreatePersonalTeamByPilotIdRequestAuth,
        response=PersonalTeamCreatedResponse)
    def create_personal_team_member(self, req: CreatePersonalTeamByPilotIdRequestAuth,
                                  resp: PersonalTeamCreatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        sub_group_rep = self.load_repository(SubGroupModel)

        sub_group = sub_group_rep.db.get_by_id(req.subgroup_id)
        
        if not sub_group:
            return resp(HTTPStatus.NOT_FOUND, {}, f"Subgroup not found by subgroup_id: {req.subgroup_id}")

        contact_type_rep = self.load_repository(ContactTypeModel)
        contact_type = contact_type_rep.db.get_by(type_contact='Cell/Whatsapp')

        user_guest_id = None
        person_model = None
        is_new_person = True

        person_repo = self.load_repository(PersonModel)
        profile_repo = self.load_repository(ProfileModel)

        user_repo = self.load_repository(UserModel)
        user_model = user_repo.db.get_by(email=req.email)

        if user_model:
            is_new_person = False

            person_model = person_repo.db.get_by_id(id=user_model.person_id)
            
            if not person_model:
                return resp(HTTPStatus.NOT_FOUND, message="Person not found")

        if not person_model:
            person_data = self.separate_name_into_parts(name=req.name)

            if person_data.get('last_name') is None:
                return resp(HTTPStatus.BAD_REQUEST, {}, 'Error: send full name in request')

            person_model = person_repo.db.add(person_data)

        if not person_model:
            return resp(HTTPStatus.BAD_REQUEST, 'Error occurred while register person')

        profile_model = self.exec_use_case(
                            LoadProfileUseCase, 
                            person=person_model,
                            subgroup_id=req.subgroup_id,
                            profile_permissions=req.member_permissions
                        )
        
        if not profile_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error to create a new profile for member")

        if is_new_person:
            user_guest_repo = self.load_repository(UserGuestModel)
            user_guest_model: UserGuestModel = user_guest_repo.model
            user_guest_data = {
                'email': req.email,
                'profile_id': profile_model.id,
                'code' : user_guest_model.generate_code()
            }

            user_guest_model = user_guest_repo.db.add(data=user_guest_data)
            if not user_guest_model:
                return resp(HTTPStatus.BAD_REQUEST, message="Error add user guest")
            
            user_guest_id = user_guest_model.id

        access_profiles = self.exec_use_case(
            LoadAccessProfilesUseCase,
            profile_id=profile_model.id
        )

        if not access_profiles:
            return resp(HTTPStatus.CONFLICT, message="You do not have access to the application, contact the admin")

        access_profile : AccessProfile = access_profiles[person_model.id][0]

        ap_model = self.load_repository(AccessProfileModel).db.upsert(access_profile.to_dict(), profile_id=profile_model.id)

        if not ap_model:
            user_repo.db.remove_by_id(user_model.id)
            if not user_guest_id:
                profile_repo.db.remove_by_id(person_model.id)
                person_repo.db.remove_by_id(person_model.id)

            return resp(
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR, 
                message="Error add access profile"
            )

        access_profile.upsert_in_redis(self.get_redis())

        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=access_profile,
            aud=str(profile_model.id),
            exp_minutes=self._EXPIRATION_TIME
        )

        cta_url = self._get_cta_url(
            token=token_jwt.encode_token(self.settings),
            id=user_guest_model.id if user_guest_model else user_model.id,
            page_url=req.registration_page_url if is_new_person else req.acceptance_page_url,
            is_new_person=is_new_person
        )

        self._send_email(
            access_profile=access_profile,
            current_profile=req.current_profile,
            target_name=person_model.full_name,
            target_email=req.email,
            cta_url=cta_url,
            is_new_person=is_new_person
        )

        personal_team_rep = self.load_repository(PersonalTeamMemberModel)
        personal_team_data = {
            'pilot_id': req.pilot_id,
            'member_id': profile_model.id
        }

        personal_team = personal_team_rep.db.add(personal_team_data)

        contact_rep = self.load_repository(ContactModel)
        
        contact_data = {
            'contact_type_id': contact_type.id,
            'person_id': person_model.id,
            'name': person_data.get('full_name'),
            'value': req.contact
        }
        
        contact_rep.db.add(contact_data)

        return resp(HTTPStatus.CREATED, personal_team.to_dict(), "Member register in personal team successfully")

    @BaseController.route(
        path="/pilot/<path:pilot_id>/member/<path:member_id>",
        methods=["GET"],
        request=GetPersonalTeamIdWithMemberIdRequestAuth,
        response=PersonalTeamGetByIdResponse)
    def get_member_information_by_id(self, req: GetPersonalTeamIdWithMemberIdRequestAuth,
                                     resp: PersonalTeamGetByIdResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        personal_team_rep = self.load_repository(PersonalTeamMemberModel)
        personal_team = personal_team_rep.db.get_by(pilot_id=req.pilot_id, member_id=req.member_id)

        if not personal_team:
            return resp(HTTPStatus.NOT_FOUND, {},
                        f'Personal team not found by pilot_id: {req.pilot_id} and member_id: {req.member_id}')

        profile_repo = self.load_repository(ProfileModel)
        profile_model = profile_repo.db.get_by_id(id=req.member_id)

        contact_model = self.load_repository(ContactModel).db.get_by(person_id=profile_model.person_id)

        access_profile_dict = {
            "pilot_id": req.pilot_id,
            "member":
                {
                    "id": personal_team.member_id,
                    "access_profile": personal_team.member,                    
                    "permissions": profile_model.permissions,
                    "member_acceptance": personal_team.member_acceptance,
                    "acceptance_status": personal_team.acceptance_status,
                    "member_rejection": personal_team.member_rejection,
                    "contact": contact_model.to_dict() if contact_model else None
                }
        }

        return resp(HTTPStatus.OK, access_profile_dict, 'Successfully')
    
    @BaseController.route(
        path="/member/<path:member_id>",
        methods=["GET"],
        request=GetPersonalTeamByMemberIdRequestAuth,
        response=PersonalTeamGetByIdResponse)
    def get_member_information_by_member_id(self, req: GetPersonalTeamByMemberIdRequestAuth,
                                     resp: PersonalTeamGetByIdResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        personal_team_rep = self.load_repository(PersonalTeamMemberModel)
        personal_team = personal_team_rep.db.get_by(member_id=req.member_id)

        if not personal_team:
            return resp(HTTPStatus.NOT_FOUND, {},
                f'Personal team not found by member_id: {req.member_id}')

        profile_repo = self.load_repository(ProfileModel)
        profile_model = profile_repo.db.get_by_id(id=req.member_id)

        contact_model = self.load_repository(ContactModel).db.get_by(person_id=profile_model.person_id)

        access_profile_dict = {
            "pilot_id": personal_team.pilot_id,
            "member":
                {
                    "id": personal_team.member_id,
                    "access_profile": personal_team.member,                    
                    "permissions": profile_model.permissions,
                    "member_acceptance": personal_team.member_acceptance,
                    "acceptance_status": personal_team.acceptance_status,
                    "member_rejection": personal_team.member_rejection,
                    "contact": contact_model.to_dict() if contact_model else None
                }
        }

        return resp(HTTPStatus.OK, access_profile_dict, 'Successfully')

    @BaseController.route(
        path="/pilot/<path:pilot_id>/member/<path:member_id>",
        methods=["PUT"],
        request=UpdatePersonalTeamIdWithMemberIdRequestAuth,
        response=PersonalTeamUpdatedResponse)
    def update_permission_of_member(self, req: UpdatePersonalTeamIdWithMemberIdRequestAuth,
                                    resp: PersonalTeamUpdatedResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        personal_team_rep = self.load_repository(PersonalTeamMemberModel)
        profile_repo = self.load_repository(ProfileModel)

        subgroup_id = None

        if not personal_team_rep.db.contains(pilot_id=req.pilot_id, member_id=req.member_id):
            return resp(HTTPStatus.NOT_FOUND, {},
                        f'Personal team not found by pilot_id: {req.pilot_id} and member_id: {req.member_id}')

        profile_repo = self.load_repository(ProfileModel)
        profile_model = profile_repo.db.get_by_id(id=req.member_id)

        if not profile_model:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")

        if req.subgroup_id:
            subgroup_rep = self.load_repository(SubGroupModel)
            subgroup_model =  subgroup_rep.db.get_by_id(id=req.subgroup_id)
            
            if not subgroup_model:
                return resp(HTTPStatus.NOT_FOUND, {}, f'Subgroup not found by id: {req.subgroup_id}')

            subgroup_id = subgroup_model.id

        person_repo = self.load_repository(PersonModel)
        person_model = person_repo.db.get_by_id(id=profile_model.person_id)

        profile_model = self.exec_use_case(
                            LoadProfileUseCase,
                            person=person_model,
                            subgroup_id=subgroup_id,
                            profile_permissions=req.member_permissions,
                            profile_id=profile_model.id
                        )

        profile_data = profile_model.to_dict()

        return resp(HTTPStatus.OK, profile_data, 'Successfully')

    @BaseController.route(
        path="/pilot/<path:pilot_id>/member/<path:member_id>",
        methods=["DELETE"],
        request=DeletePersonalTeamIdWithMemberIdRequestAuth,
        response=PersonalTeamDeletedResponse)
    def delete_member_of_team(self, req: DeletePersonalTeamIdWithMemberIdRequestAuth,
                              resp: PersonalTeamDeletedResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        if req.pilot_id != req.current_profile.profile_id:
            return resp(HTTPStatus.UNAUTHORIZED, messsage="Profile unauthorized")

        profile_repo = self.load_repository(ProfileModel)
        personal_team_rep = self.load_repository(PersonalTeamMemberModel)

        member_model = personal_team_rep.db.get_by(pilot_id=req.pilot_id, member_id=req.member_id)

        if not member_model:
            return resp(HTTPStatus.NOT_FOUND, {},
                        f'Personal team not found by pilot_id: {req.pilot_id} and member_id: {req.member_id}')

        profile_model = profile_repo.db.get_by_id(id=req.member_id)
        
        if not profile_model:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")

        self.load_repository(AccessProfileModel).db.delete(profile_id=req.member_id)
        self.load_repository(ConfigModel).db.remove(profile_id=req.member_id)
        self.load_repository(UserGuestModel).db.remove(profile_id=req.member_id)
        self.load_repository(PersonalTeamMemberModel).db.remove(member_id=req.member_id)
        self.load_repository(ProfileModel).db.delete(id=profile_model.id)

        return resp(HTTPStatus.OK, {}, "Member removed successfully")

    @BaseController.route(
        path="/pilot/<path:pilot_id>/member/<path:member_id>/rejected/",
        methods=["PUT", "PATCH"],
        request=UpdateMemberAcceptanceRequestAuth,
        response=UpdateMemberAcceptanceResponse)
    def member_rejected_invitation(self, req: UpdateMemberAcceptanceRequestAuth,
                              resp: UpdateMemberAcceptanceResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        personal_team_rep = self.load_repository(PersonalTeamMemberModel)
        
        personal_model = personal_team_rep.db.get_by(pilot_id=req.pilot_id, member_id=req.member_id)

        if not (personal_model):
            return resp(HTTPStatus.NOT_FOUND, message="Personal team not found")
        
        personal_model.acceptance_status = PersonalTeamStatus.REJECTED
        personal_model.member_rejection = DateTime.now()
        personal_model.member_acceptance = None
        personal_model = personal_team_rep.db.update_by_id(id=personal_model.id, data=personal_model)
        
        if not personal_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating personal team")
        
        return resp(HTTPStatus.OK, personal_model, "Successfully")

    @BaseController.route(
        path="/pilot/<path:pilot_id>/member/<path:member_id>/accepted/",
        methods=["PUT", "PATCH"],
        request=UpdateMemberAcceptanceRequestAuth,
        response=UpdateMemberAcceptanceResponse)
    def member_accepted_invitation(self, req: UpdateMemberAcceptanceRequestAuth, resp: UpdateMemberAcceptanceResponse):
        
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        personal_team_rep = self.load_repository(PersonalTeamMemberModel)
        
        personal_model = personal_team_rep.db.get_by(pilot_id=req.pilot_id, member_id=req.member_id)
        
        if not personal_model:
            return resp(HTTPStatus.NOT_FOUND, message="Personal team not found")
        
        personal_model.acceptance_status = PersonalTeamStatus.ACCEPTED
        personal_model.member_rejection = None
        personal_model.member_acceptance = DateTime.now()
        personal_model = personal_team_rep.db.update_by_id(personal_model.id, personal_model)
        
        if not personal_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating personal team")
        
        return resp(HTTPStatus.OK, personal_model, "Successfully")
        
    def separate_name_into_parts(self, name: str) -> dict:
        person_name = name
        full_name_parts = str(person_name).strip().split()
        first_name = full_name_parts[0] if full_name_parts else None
        last_name = full_name_parts[-1] if len(full_name_parts) > 1 else None

        if len(full_name_parts) > 2:
            first_name = ' '.join(full_name_parts[:-1])

        name_data = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': name
        }

        return name_data

    def _send_email(self,
            access_profile: AccessProfile,
            current_profile: AccessProfile,
            target_name: str,
            target_email: str,
            cta_url: str,
            is_new_person: bool = False):

        subject = "(Porsche CUP) Vocês acaba de receber um novo convite"
        if is_new_person:
            body_text = f"Você recebeu um convite para acessar como {access_profile.subgroup_name} do(a) {current_profile.name}, na plataforma da Porsche CUP Brasil. Acesse agora mesmo e descubra as novidades do seu novo perfil!."
            cta_label = "ACESSAR AGORA"
        else:
            body_text = f"Vocês recebeu um convite para criação de conta como {access_profile.subgroup_name} na Porsche CUP Brasil, para finalizar o seu cadastro vocês deve clicar em Aceitar Convite"
            cta_label = "ACEITAR CONVITE"

        self.notify.send_email(
            notification=Notification(
                channel_names=["EMAIL"],
                targets=[TargetNotification(
                    target_type=["USER"],
                    target_name=target_name,
                    target_address=target_email
                )],
                subject=subject,
                template_id=self._app.settings.sendgrid_template_default_id,
                meta_data=EmailDynamicData(
                    body_text=body_text,
                    cta_label=cta_label,
                    cta_url=cta_url
                ).model_dump()
            )
        )

    def _get_cta_url(self, token: str, id: str, page_url: t.Union[str, HttpUrl],
                     is_new_person: bool = False) -> str:

        parsed_url = urlparse(str(page_url))

        if not is_new_person:
            return f"{parsed_url.scheme}://{parsed_url.netloc}"

        query_params = {
            "token": token,
            "user_guest_id": id,
            "open-app": True
        }
        query_string = urlencode(query_params)

        new_url = ParseResult(
            scheme=parsed_url.scheme,
            netloc=parsed_url.netloc,
            path=parsed_url.path,
            params=parsed_url.params,
            query=query_string,
            fragment=parsed_url.fragment,
        )

        return urlunparse(new_url)
