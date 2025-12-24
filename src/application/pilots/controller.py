import typing as t

from urllib.parse import urlparse, urlencode, urlunparse, ParseResult
from http import HTTPStatus
from pydantic import HttpUrl, EmailStr
from datetime import timedelta

from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.tools.notify import Notification, TargetNotification, EmailDynamicData
from arcs_lib_pca.tools.security.repository import TokenJwt
from arcs_lib_pca.infrastructure.repository import Repositories
from arcs_lib_pca.domain import DateTime, AccessProfile, GenericUUID

from src.domain.value_objects import DefaultSubgroupNameEnum, PilotStatusEnum, UserMetadataVO, UserEmailRequest, \
    ErrorVO, MetaDataEmailVO
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
from src.infrastructure.models.config_model import ConfigModel
from src.infrastructure.models.pilot_model import PilotModel
from src.infrastructure.models.profile_model import ProfileModel
from src.use_case import LoadProfileUseCase
from src.use_case.access_profile import LoadAccessProfilesUseCase

from .requests import (
    CreatePilotRequestAuth,
    ResendInvitationPilotRequestAuth,
    UpdatePilotRequestAuth,
    DeletePilotRequestAuth,
    GetPilotByIdRequestAuth,
    GetPilotsRequestAuth,
    GetPilotsRequest, GetPilotByEmailRequestAuth
)

from .responses import (
    GetPilotResponse,
    GetPilotByIdResponse,
    CreatePilotResponse,
    ResendInvitationPilotResponse,
    UpdatePilotResponse,
    DeletePilotResponse, GetPilotByEmailResponse
)
from ...utils.user_utils import get_user_by_email


class PilotController(BaseController):
    @BaseController.route(
        path="/public/",
        methods=["GET"],
        request=GetPilotsRequest,
        response=GetPilotResponse
    )
    def get_all_public_data_of_pilots(self, req: GetPilotsRequest, resp: GetPilotResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        pilot_repo = self.load_repository(PilotModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        pilots = pilot_repo.db.with_query(subquery_params).paginate(
            per_page=req.per_page,
            page=req.page,
            load=["person", "profile", "creator", "deletor", "updator"],
            filters=[PilotModel.status == PilotStatusEnum.ACTIVE.value]
        )

        items = [{"id": item["profile_id"], "name": item["name"]} for item in pilots["items"]]

        pilots["items"] = items

        return resp(HTTPStatus.OK, pilots, "Successfully")

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetPilotsRequestAuth,
        response=GetPilotResponse)
    def get_all_pilots(self, req: GetPilotsRequestAuth, resp: GetPilotResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        pilot_repo = self.load_repository(PilotModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        pilots = pilot_repo.db.with_query(subquery_params).paginate(req.page, req.per_page,
                                                                    load=["person", "profile", "creator", "deletor",
                                                                          "updator"])

        return resp(HTTPStatus.OK, pilots, "Successfully")

    @BaseController.route(
        path="/email/<path:email>/",
        methods=["GET"],
        request=GetPilotByEmailRequestAuth,
        response=GetPilotByEmailResponse)
    def get_pilot_by_email(self, req: GetPilotByEmailRequestAuth, resp: GetPilotByEmailResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        user_repository = self.load_repository(UserModel)
        user = get_user_by_email(user_repository, req.email)

        if not user:
            return resp(HTTPStatus.NOT_FOUND, message="User for this not found")

        person: PersonModel = self.load_repository(PersonModel).db.get_by(id=user.person_id, load=["profiles"])

        if not person:
            return resp(HTTPStatus.NOT_FOUND, message="Person for this user not found")

        pilot_subgroup = self.load_repository(SubGroupModel).db.get_by(name=DefaultSubgroupNameEnum.MAIN_PILOT.value)

        if not pilot_subgroup:
            return resp(HTTPStatus.NOT_FOUND, message="Pilot subgroup not found")

        person: dict = person.to_dict(lazy_load=["profiles"])

        pilot_profile = next(
            (profile for profile in person.get("profiles", []) if profile.get("subgroup_id") == pilot_subgroup.id),
            None)

        if not pilot_profile:
            return resp(HTTPStatus.NOT_FOUND, message="Pilot profile for this person not found")

        pilot: PilotModel = self.load_repository(PilotModel).db.get_by(profile_id=pilot_profile.get("id"),
                                                                       load=["person", "profile", "creator", "deletor",
                                                                             "updator"])

        address_models = self.load_repository(AddressModel).db.find(person_id=pilot.person_id)
        contact_models = self.load_repository(ContactModel).db.find(person_id=pilot.person_id)

        pilot_data = {
            **pilot.to_dict(lazy_load=["person", "profile", "creator", "deletor", "updator"]),
            "addresses": [address.to_dict() for address in address_models or []],
            "contacts": [contact.to_dict() for contact in contact_models or []],
            "emails": user.meta_data.get("emails", []) if user.meta_data else [],
        }

        return resp(HTTPStatus.OK, pilot_data, "Successfully")

    @BaseController.route(
        path="/<path:pilot_id>",
        methods=["GET"],
        request=GetPilotByIdRequestAuth,
        response=GetPilotByIdResponse)
    def get_pilot_by_id(self, req: GetPilotByIdRequestAuth, resp: GetPilotByIdResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        pilot_repo = self.load_repository(PilotModel)
        pilot_model: PilotModel = pilot_repo.db.get_by_id(id=req.pilot_id,
                                              load=["person", "profile", "creator", "deletor", "updator"])

        if not pilot_model:
            return resp(HTTPStatus.NOT_FOUND, message="Pilot not found")

        user = self.load_repository(UserModel).db.get_by(person_id=pilot_model.person_id)

        secondary_emails  = user.meta_data.get("emails", []) if user and user.meta_data else []

        address_models = self.load_repository(AddressModel).db.find(person_id=pilot_model.person_id)
        contact_models = self.load_repository(ContactModel).db.find(person_id=pilot_model.person_id)

        pilot_data = {
            **pilot_model.to_dict(lazy_load=["person", "profile", "creator", "deletor", "updator"]),
            "addresses": [address.to_dict() for address in address_models or []],
            "contacts": [contact.to_dict() for contact in contact_models or []],
            "emails": secondary_emails
        }

        return resp(HTTPStatus.OK, pilot_data, "Successfully")

    @BaseController.route(
        path="/<path:pilot_id>/resend_invitation/",
        methods=["POST"],
        request=ResendInvitationPilotRequestAuth,
        response=ResendInvitationPilotResponse)
    def resend_invitation_pilot(self, req: ResendInvitationPilotRequestAuth, resp: ResendInvitationPilotResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Invalid request")

        ap_repo = self.load_repository(AccessProfileModel)

        if last_resend := self.get_redis().get_by_key(["last_resend_invitation", str(req.pilot_id)]):
            return resp(HTTPStatus.OK, last_resend, message="Pilot has already been invited")

        if not (ap_model := ap_repo.db.get_by(profile_id=req.pilot_id, load=["profile"])):
            return resp(HTTPStatus.NOT_FOUND, message="Pilot not found")

        ap_vo: AccessProfile = ap_model.to_vo()
        if not ap_vo:
            return resp(HTTPStatus.NOT_FOUND, message="Pilot not found")

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

        # TODO: Corrijido na nova versão do arcs-lib-pca
        now = DateTime.now()
        # 1. Calcula o momento de reenvio adicionando 15 minutos ao agora
        unlock_invitation_resending_at = now + timedelta(minutes=15)

        # 2. Calcula a diferença em segundos (valor absoluto)
        expired_seconds = int(abs((unlock_invitation_resending_at - now).total_seconds()))

        data = {
            "invited_by": req.current_profile.to_dict(),
            "unlock_invitation_resending_at": str(unlock_invitation_resending_at.strftime("%Y-%m-%d %H:%M:%S"))
        }

        self.get_redis().add(["last_resend_invitation", str(req.pilot_id)], data, ex=expired_seconds)
        return resp(HTTPStatus.CREATED, data, message="Successfully")

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreatePilotRequestAuth,
        response=CreatePilotResponse)
    def create_pilot(self, req: CreatePilotRequestAuth, resp: CreatePilotResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Invalid request")

        if self.load_repository(PilotModel).db.contains(identifier=req.identifier):
            return resp(HTTPStatus.CONFLICT, message=f"Pilot identifier {req.identifier} already in use")

        is_new_person = False

        user_guest_repo = self.load_repository(UserGuestModel)
        user_repo = self.load_repository(UserModel)
        person_repo = self.load_repository(PersonModel)
        subgroup_repo = self.load_repository(SubGroupModel)

        user_guest_model: UserGuestModel = user_guest_repo.model
        user_model: UserModel = user_repo.model
        person_model: PersonModel = person_repo.model

        # SUBGROUP VALIDATION
        subgroup_model = subgroup_repo.db.get_by(name=DefaultSubgroupNameEnum.MAIN_PILOT.value)

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

                self.load_repository(ContactModel).db.add(contact_data)

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
                                           subgroup_id=subgroup_model.id,
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
            'code': user_guest_model.generate_code()
        }

        if not is_new_person:
            # TODO: Esse delete deve ser mantido até o front desenvolver as telas para confirmação de convites
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

        # self._send_email(
        #     access_profile=access_profile,
        #     current_profile=req.current_profile,
        #     target_name=person_model.full_name,
        #     target_email=req.email,
        #     cta_url=cta_url,
        #     is_new_person=is_new_person
        # )

        pilot_data = {
            "profile_id": access_profile.profile_id,
            "person_id": access_profile.person_id,
            "name": access_profile.name,
            "identifier": req.identifier,
            "status": req.status.value,
            "bop": req.bop
        }

        pilot_model = self.load_repository(PilotModel).db.add(pilot_data)

        if not pilot_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error to add a new pilot")

        return resp(
            HTTPStatus.OK,
            access_profile.to_dict(),
            "User registered successfully"
        )

    @BaseController.route(
        path="/<path:pilot_id>",
        methods=["PUT"],
        request=UpdatePilotRequestAuth,
        response=UpdatePilotResponse)
    def update_pilot(self, req: UpdatePilotRequestAuth, resp: UpdatePilotResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Invalid request")

        subgroup_repo = self.load_repository(SubGroupModel)
        pilot_repo = self.load_repository(PilotModel)

        pilot_model = pilot_repo.db.get_by_id(req.pilot_id)

        if not pilot_model:
            return resp(HTTPStatus.NOT_FOUND, message="Pilot not found")

        subgroup_model = subgroup_repo.db.get_by(name=DefaultSubgroupNameEnum.MAIN_PILOT.value)

        if not subgroup_model:
            return resp(HTTPStatus.NOT_FOUND, message='Subgroup not found')

        if pilot_model.identifier != req.identifier and self.load_repository(PilotModel).db.contains(
                identifier=req.identifier):
            return resp(HTTPStatus.CONFLICT, message="Already exists a pilot with this identifier")

        person_model = self.load_repository(PersonModel).db.get_by_id(pilot_model.person_id)

        if not person_model:
            return resp(HTTPStatus.NOT_FOUND, message="Person not found")

        was_updated = person_model.merge_person_base(req.person)

        if not was_updated:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error to update person")

        person_model = self.load_repository(PersonModel).db.update_by_id(id=person_model.id, data=person_model)

        pilot_data = {
            "name": person_model.full_name,
            "identifier": req.identifier,
            "status": req.status.value,
            "bop": req.bop,
        }

        pilot_model = self.load_repository(PilotModel).db.update_by_id(id=pilot_model.id, data=pilot_data)

        # ADDRESS CREATION
        if req.address:
            address_repo = Repositories(AddressModel())
            address_data = req.address.model_dump()
            address_data['person_id'] = person_model.id

            if req.address.id and address_repo.db.contains(id=req.address.id):
                address_repo.db.update_by_id(id=req.address.id, data=address_data)
            else:
                address_repo.db.add(address_data)

        # CONTACTS CREATION
        if req.contacts:
            for contact in req.contacts:
                if not contact:
                    continue

                contact_data = contact.model_dump()
                contact_data['person_id'] = person_model.id
                if not self.load_repository(ContactTypeModel).db.contains(id=contact_data['contact_type_id']):
                    contact_type_others = self.load_repository(ContactTypeModel).db.get_by(name="Others")

                    if not contact_type_others:
                        continue

                    contact_data['contact_type_id'] = contact_type_others.id

                if not contact.id or (contact.id and not self.load_repository(ContactModel).db.get_by_id(contact.id)):
                    self.load_repository(ContactModel).db.add(contact_data)
                else:
                    self.load_repository(ContactModel).db.update_by_id(id=contact.id, data=contact_data)

        profile_description = None
        profile_picture = None
        profile_permissions = None

        if req.profile:
            profile_description = req.profile.description
            profile_picture = req.profile.pictures
            profile_permissions = req.profile.permissions

        profile = self.load_repository(ProfileModel).db.get_by_id(pilot_model.profile_id)

        profile_model = self.exec_use_case(LoadProfileUseCase,
                                           person=person_model,
                                           profile_id=profile.id,
                                           profile_description=profile_description,
                                           profile_picture=profile_picture,
                                           profile_permissions=profile_permissions
                                           )
        if not profile_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error to update profile")

        error = self._update_user_emails(req.emails, person_model.id)

        if error:
            return resp(error.status, message=error.message)

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, profile_id=profile_model.id)

        access_profile: AccessProfile = access_profiles[person_model.id][0]

        # Atualiza o email principal do access profile
        main_email = next((email for email in req.emails if email.is_main),None)
        if main_email:
            access_profile.email = main_email.email

        Repositories(AccessProfileModel()).db.upsert(access_profile.to_dict(), profile_id=profile_model.id)

        access_profile.upsert_in_redis(self.get_redis())

        return resp(HTTPStatus.OK, pilot_model.to_dict(), message="Pilot successfully updated")

    @BaseController.route(
        path="/<path:pilot_id>",
        methods=["DELETE"],
        request=DeletePilotRequestAuth,
        response=DeletePilotResponse
    )
    def delete_pilot(self, req: DeletePilotRequestAuth, resp: DeletePilotResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        pilot_repo = self.load_repository(PilotModel)

        pilot_model = pilot_repo.db.get_by_id(req.pilot_id)
        if not pilot_model:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")

        profile_repo = self.load_repository(ProfileModel)

        profile_model = profile_repo.db.get_by_id(pilot_model.profile_id)
        if not profile_model:
            return resp(HTTPStatus.NOT_FOUND, message="Profile not found")

        self.load_repository(AccessProfileModel).db.delete(profile_id=pilot_model.profile_id)
        self.load_repository(ConfigModel).db.remove(profile_id=pilot_model.profile_id)
        self.load_repository(UserGuestModel).db.remove(profile_id=pilot_model.profile_id)

        self.load_repository(ProfileModel).db.delete(id=pilot_model.profile_id)
        self.load_repository(PilotModel).db.delete(id=pilot_model.id)

        return resp(HTTPStatus.OK, {}, message="Request Sucessfully")

    def _create_person(self, person_model: PersonModel, person_data: dict,
                       person_repo: Repositories[type[PersonModel]]) -> t.Optional[PersonModel]:
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

        subject = "Bem-vindo ao ARCS!"
        body_text = f"<p>Olá {access_profile.name}, seja bem-vindo ao <strong>ARCS</strong>, o aplicativo oficial da <strong><em>Porsche Cup!</em></strong></p> <p>Estamos muito felizes em tê-lo conosco. Este é o primeiro passo para uma nova experiência em sua jornada no automobilismo.</p> <p><strong>O que é o ARCS?</strong><br> O ARCS é a nova plataforma oficial da Porsche Cup, desenvolvida para centralizar e facilitar todos os processos essenciais da sua participação na categoria. A partir de agora, será por meio dela que você realizará diversas ações importantes.</p> <p><strong>O que fazer agora?</strong><br> Para garantir seu acesso e utilizar todas as funcionalidades do ARCS, conclua seu cadastro agora mesmo. Se precisar de qualquer ajuda, estamos à disposição. Nos vemos na pista!</p> <p><em>🏁 Disclaimer:</em> Você está recebendo este e-mail porque foi convidado a participar da nossa plataforma.<br> Para mais informações, entre em contato através de <a href='mailto:relacionamento@porschegt3cup.com.br'>relacionamento@porschegt3cup.com.br</a>.</p> <p><em>Este e-mail foi enviado automaticamente, por favor, não responda a esta mensagem.</em></p>"
        cta_label = "Clique aqui para ativar sua conta"

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

    def _get_cta_url(self, token: str, id: str, registration_page_url: t.Union[str, HttpUrl],
                     is_new_person: bool = False) -> str:
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

    def _update_user_emails(self, emails: t.List[UserEmailRequest], person_id: GenericUUID) -> t.Optional[ErrorVO]:
        main_emails_count = sum(1 for email in emails if email.is_main)

        if main_emails_count > 1:
            return ErrorVO(status=HTTPStatus.BAD_REQUEST, message="Can't have more than one main email")

        if main_emails_count == 0:
            return ErrorVO(status=HTTPStatus.BAD_REQUEST, message="Must have one main email")

        user_repository = self.load_repository(UserModel)
        user = user_repository.db.get_by(person_id=person_id)

        if not user:
            return ErrorVO(status=HTTPStatus.NOT_FOUND, message="User for pilot not found")

        for email in emails:
            user_by_email = get_user_by_email(user_repository, email.email)

            if user_by_email and user_by_email.id != user.id:
                return ErrorVO(status=HTTPStatus.CONFLICT, message="Email is already in use")

        metadata = UserMetadataVO(**user.meta_data)

        main_email = next((email for email in emails if email.is_main))

        metadata.emails = [MetaDataEmailVO(email=user_email.email)  for user_email in emails if not user_email.is_main]

        self.load_repository(UserModel).db.update_by_id(id=user.id, data={'email': main_email.email,
                                                                          'meta_data': metadata.model_dump()})
        return None