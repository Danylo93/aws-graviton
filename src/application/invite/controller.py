import typing as t 

from urllib.parse import urlparse, urlencode, urlunparse, ParseResult
from http import HTTPStatus
from pydantic import HttpUrl
from datetime import datetime, timedelta
import pytz

from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.tools.notify import Notification, TargetNotification, EmailDynamicData
from arcs_lib_pca.tools.security.repository import TokenJwt
from arcs_lib_pca.infrastructure.repository import Repositories
from arcs_lib_pca.domain import DateTime, AccessProfile

from src.infrastructure.models import (
    PersonModel, 
    UserModel, 
    UserGuestModel, 
    ContactTypeModel,
    ContactModel,
    SubGroupModel,
    AddressModel
)

from src.infrastructure.models.access_profile_model import AccessProfileModel
from src.use_case import LoadProfileUseCase
from src.use_case.access_profile import LoadAccessProfilesUseCase

from .requests import(
    CreateInviteRequest,
    ResendInvitationRequestAuth,
    GenerateInviteRequestAuth
)

from .responses import(
    CreateInviteResponse,
    ResendInvitationResponse,
    GenerateInviteResponse
)

class InviteController(BaseController):
    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateInviteRequest,
        response=CreateInviteResponse)
    def create_invite(self, req: CreateInviteRequest, resp: CreateInviteResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Invalid request")
        
        is_new_person = False
        
        user_guest_repo = self.load_repository(UserGuestModel)
        user_repo = self.load_repository(UserModel)
        person_repo = self.load_repository(PersonModel)
        subgroup_repo = self.load_repository(SubGroupModel)

        user_guest_model: UserGuestModel = user_guest_repo.model
        user_model: UserModel = user_repo.model
        person_model: PersonModel = person_repo.model

        # SUBGROUP VALIDATION
        subgroup_model = subgroup_repo.db.get_by_id(id=req.subgroup_id)

        if not subgroup_model:
            return resp(HTTPStatus.NOT_FOUND, message='Subgroup not found')

        # VALIDATE IF THE USER ALREADY EXISTS
        # TODO: validar caso em que dois convites para uma pessoa com mesmo email e sem user cadastrado, dois user_guest apontando para o mesmo email

        if req.user_id:
            if not (user_model := user_repo.db.get_by_id(req.user_id, load=['person'])):
                return resp(HTTPStatus.BAD_REQUEST, message="Guest code is not valid")
            person_model = user_model.person
            
        elif (user_model := user_repo.db.get_by(email=req.email, load=['person'])):
            person_model = user_model.person

        else:
            person_model = self._create_person(
                person_model=person_model,
                person_data=req.person.model_dump(),
                person_repo=person_repo
            )
            is_new_person = True

        if not person_model.id:
            return resp(HTTPStatus.BAD_REQUEST, message="Error add person")

        # ADDRESS CREATION
        if req.address:
            address_repo = Repositories(AddressModel())
            address_data = req.address.model_dump()
            address_data['person_id'] = person_model.id

            address_repo.db.add(address_data)

        # CONTACTS CREATION
        if req.contacts:
            #TODO: centralizar o processo de criação de contatos, para ser possível validar cada contato adicionado
            contacts_data = []

            contacts_repo = Repositories(ContactModel())
            contact_type_repo = Repositories(ContactTypeModel())
            for contact in req.contacts:
                if not contact:
                    continue

                contact_data = contact.model_dump()
                contact_data['person_id'] = person_model.id
                if not contact_type_repo.db.contains(id=contact_data['contact_type_id']):
                    contact_type_others = contact_type_repo.db.get_by(name="Others")

                    if not contact_type_others:
                        continue

                    contact_data['contact_type_id'] = contact_type_others.id

                contacts_data.append(contact_data)

            contacts_repo.db.add_all(contacts_data)

        # PROFILE CREATION
        profile_description = None
        profile_picture = None
        profile_permissions = None

        if req.profile:
            profile_description = req.profile.description
            profile_picture = req.profile.pictures
            profile_permissions = req.profile.permissions

        profile_model = self.exec_use_case(LoadProfileUseCase,                  
                                        person=person_model,
                                        subgroup_id=req.subgroup_id,
                                        profile_description=profile_description,
                                        profile_picture=profile_picture,
                                        profile_permissions=profile_permissions
                                    )

        if not profile_model:
            return resp(HTTPStatus.BAD_REQUEST, message="Error add profile")

        # USER GUEST CREATION
        user_guest_data = {
            'email': req.email,
            'profile_id': profile_model.id,
            'code' : user_guest_model.generate_code()
        }

        if not is_new_person:
            #TODO: Esse delete deve ser mantido até o front desenvolver as telas para confirmação de convites
            user_guest_data['deleted_at'] = DateTime.now()
            user_guest_data['deleted_by'] = req.current_profile.profile_id

        user_guest_model = user_guest_repo.db.add(data=user_guest_data)

        if not user_guest_model:
            return resp(HTTPStatus.BAD_REQUEST, message="Error add user guest")

        # Access Profile
        access_profiles = execute_use_case(LoadAccessProfilesUseCase,
                                            profile_id=profile_model.id)

        access_profile: AccessProfile = access_profiles[person_model.id][0]
        
        Repositories(AccessProfileModel()).db.upsert(access_profile.to_dict(), profile_id=profile_model.id)

        access_profile.upsert_in_redis(self.get_redis())

        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=access_profile,
            aud=str(profile_model.id),
            exp_minutes=24 * 60
        )

        cta_url = self._get_cta_url(
            token=token_jwt.encode_token(self.settings), 
            id=user_guest_model.id, 
            registration_page_url=req.registration_page_url,
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

        return resp(
                HTTPStatus.OK,
                access_profile.to_dict(),
                "User registered successfully"
            )

    @BaseController.route(
        path="/<path:profile_id>/resend_invitation/",
        methods=["POST"],
        request=ResendInvitationRequestAuth,
        response=ResendInvitationResponse)   
    def resend_invitation(self, req: ResendInvitationRequestAuth, resp: ResendInvitationResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Invalid request")

        ap_repo = self.load_repository(AccessProfileModel)

        if last_resend := ap_repo.redis.get_by_key(["last_resend_invitation", str(req.profile_id)]):
            return resp(HTTPStatus.OK, last_resend, message="Profile has already been invited")
        
        if not (ap_model := ap_repo.db.get_by(profile_id=req.profile_id, load=["profile"])):
            return resp(HTTPStatus.NOT_FOUND, message="profile not found")
        
        ap_vo: AccessProfile = ap_model.to_vo()

        if not (user_guest_model := self.load_repository(UserGuestModel).db.get_by(profile_id=ap_vo.profile_id)):
            return resp(HTTPStatus.NOT_FOUND, message="User guest not found")
        
        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=ap_vo,
            aud=str(ap_vo.profile_id),
            exp_minutes=24 * 60
        )

        cta_url = self._get_cta_url(
            token=token_jwt.encode_token(self.settings), 
            id=str(user_guest_model.id), 
            registration_page_url=req.registration_page_url,
            is_new_person=True
        )

        self._send_email(
            access_profile=ap_vo,
            current_profile=req.current_profile,
            target_name=ap_vo.name,
            target_email=ap_vo.email,
            cta_url=cta_url,
            is_new_person=True
        )

        #TODO: Corrijido na nova versão do arcs-lib-pca
        now = DateTime.now()
        # 1. Calcula o momento de reenvio adicionando 15 minutos ao agora
        unlock_invitation_resending_at = now + timedelta(minutes=15)

        # 2. Calcula a diferença em segundos (valor absoluto)
        expired_seconds = int(abs((unlock_invitation_resending_at - now).total_seconds()))

        data = {
            "invited_by": req.current_profile.to_dict(),
            "unlock_invitation_resending_at": str(unlock_invitation_resending_at.strftime("%Y-%m-%d %H:%M:%S"))
        }


        ap_repo.redis.add(["last_resend_invitation", str(req.profile_id)], data, ex=expired_seconds)
        return resp(HTTPStatus.CREATED, data, message="Successfully")

    @BaseController.route(
        path="/generate_invite/",
        methods=["POST"],
        request=GenerateInviteRequestAuth,
        response=GenerateInviteResponse)   
    def generate_invite(self, req: GenerateInviteRequestAuth, resp: GenerateInviteResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Invalid request")

        ap_repo = self.load_repository(AccessProfileModel)
        
        if not (ap_model := ap_repo.db.get_by(email=req.email, load=["profile"])):
            return resp(HTTPStatus.NOT_FOUND, message="profile not found")
        
        ap_vo: AccessProfile = ap_model.to_vo()

        if not (user_guest_model := self.load_repository(UserGuestModel).db.get_by(profile_id=ap_vo.profile_id)):
            return resp(HTTPStatus.NOT_FOUND, message="User guest not found")
        
        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=ap_vo,
            aud=str(ap_vo.profile_id),
            exp_minutes=24 * 60
        )

        cta_url = self._get_cta_url(
            token=token_jwt.encode_token(self.settings), 
            id=str(user_guest_model.id), 
            registration_page_url=req.registration_page_url,
            is_new_person=True
        )

        return resp(HTTPStatus.OK, {"url": cta_url}, message="Successfully")

    def _create_person(self, person_model: PersonModel, person_data: dict, person_repo: Repositories[type[PersonModel]]) -> t.Optional[PersonModel]:
        full_name_parts = str(person_data['full_name']).split(' ')

        if not person_data['first_name']:
            person_data['first_name'] = full_name_parts[0] if full_name_parts else None

        if not person_data['last_name']:
            person_data['last_name'] = full_name_parts[-1] if len(full_name_parts) > 1 else None

        person_model.merge(person_data)

        if person_model.id:
            person_model = person_repo.db.update_by_id(id=person_model.id, data=person_model)
        else:
            person_model = person_repo.db.add(person_model)

        return person_model

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
    
    def _get_cta_url(self, token: str, id: str, registration_page_url: t.Union[str, HttpUrl], is_new_person: bool = False) -> str:
        # Parse a URL para verificar sua validade
        parsed_url = urlparse(str(registration_page_url))

        # Se não for uma nova pessoa, retorna apenas o domínio e esquema
        if not is_new_person:
            return f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Se for uma nova pessoa, adiciona os parâmetros à URL
        query_params = {
            "token": token,
            "user_guest_id": id,
            "open-app": True
        }
        query_string = urlencode(query_params)

        # Reconstrói a URL com os parâmetros adicionados
        new_url = ParseResult(
            scheme=parsed_url.scheme,
            netloc=parsed_url.netloc,
            path=parsed_url.path,
            params=parsed_url.params,
            query=query_string,
            fragment=parsed_url.fragment,
        )
        
        return urlunparse(new_url)