from http import HTTPStatus
import typing as t

from urllib.parse import urlparse, urlencode, urlunparse, ParseResult
from pydantic import HttpUrl, EmailStr

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.tools.security.repository import TokenJwt
from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.domain import DateTime, AppClientPermissions, GenericUUID, AccessProfile
from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.tools.notify import Notification, TargetNotification, EmailDynamicData

from src.infrastructure.models import UserModel, ProfileModel, AccessProfileModel
from src.use_case import LoadAccessProfilesUseCase, TokenProviderUseCase, TokenProvider, RegisterUserUseCase
from src.domain.value_objects import PersonBase

from .requests import (
    EmailPassAuthRequest,
    ProviderAuthRequest,
    RegisterProviderRequestAuth
)

from .responses import (
    AuthResponse,
    RegisterProviderResponse
)
from ...utils.user_utils import get_user_by_email


class AuthController(BaseController):
    _DEFAULT_EXPIRATION_TOKEN_TIME = 24 * 60

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=EmailPassAuthRequest,
        response=AuthResponse)
    def auth_email_pass(self, req: EmailPassAuthRequest, resp: AuthResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        # Carrega o repositório de usuários e tenta encontrar o usuário pelo e-mail
        user_repo = self.load_repository(UserModel)

        app_client = req.header.get("X-App-Client")

        if not app_client:
            return resp(HTTPStatus.BAD_REQUEST, message="client app undefined")

        app_client = to_snake_case(app_client)

        if not (app_client_permissions := AppClientPermissions.get_of_redis(user_repo.redis, app_client,
                                                                            self.app.settings.microservice_name)):
            return resp(HTTPStatus.BAD_REQUEST, message="client app not found")

        user_model = get_user_by_email(self.load_repository(UserModel), req.email)

        if not user_model or not user_model.verify_password(req.password):
            # TODO: Adicionar que a partir de 3 tentativas bloquear o usuário
            # Retorna erro se o usuário não existir ou a senha não for válida
            return resp(HTTPStatus.UNAUTHORIZED, message="Invalid email or password")

        access_profiles = execute_use_case(LoadAccessProfilesUseCase, self, user_id=user_model.id,
                                           app_client_permissions=app_client_permissions)

        if not access_profiles:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        person_id, access_profiles_list = next(iter(access_profiles.items()))

        if not access_profiles_list:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        # Seleciona o primeiro perfil diferente de "public", ou o primeiro da lista
        last_profile_user_logged_in = next(
            (ap for ap in access_profiles_list if ap.group_name != "public"),
            access_profiles_list[0]
        )

        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=last_profile_user_logged_in,
            aud=app_client,
            exp_minutes=self._DEFAULT_EXPIRATION_TOKEN_TIME if app_client != "arcs_pilot_mobile" else self._DEFAULT_EXPIRATION_TOKEN_TIME * 7
        )

        ap_repo = self.load_repository(AccessProfileModel, last_profile_user_logged_in.to_dict())
        ap_repo.db.upsert(profile_id=last_profile_user_logged_in.profile_id)
        last_profile_user_logged_in.upsert_in_redis(ap_repo.redis)

        self.load_repository(ProfileModel).db.update_by_id(
            id=last_profile_user_logged_in.profile_id,
            data={"last_access": DateTime.now()}
        )

        return resp(200, {
            "user_guest_id": None,
            "required_register": False,
            "token": token_jwt.encode_token(self._app.settings)
        })

    @BaseController.route(
        path="/<provider_name>/",
        methods=['POST'],
        request=ProviderAuthRequest,
        response=AuthResponse
    )
    def auth_provider(self, req: ProviderAuthRequest, resp: AuthResponse):
        # Validação do request
        if not req or req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request payload")

        # Recupera o client ID da requisição
        app_client = req.header.get("X-App-Client")
        if not app_client:
            return resp(HTTPStatus.BAD_REQUEST, message="Missing required header: X-App-Client")

        app_client = to_snake_case(app_client)

        # Executa o caso de uso para validar o token do provedor
        token_provider = execute_use_case(
            TokenProviderUseCase,
            self,
            provider_name=req.provider_name,
            token=req.token
        )

        if not token_provider or not token_provider.is_valid():
            return resp(HTTPStatus.BAD_REQUEST, message=f"Provider {req.provider_name} or token unauthorized")

        # Se o usuário já existir
        if token_provider.user:
            return self._handle_existing_user(token_provider, app_client, resp)

        # Se um convite ativo estiver disponível
        if token_provider.user_guest:
            return self._handle_user_with_invite(token_provider, app_client, req, resp)

        # Registro de novo usuário
        return self._register_new_user(token_provider, app_client, resp, req)

    def _handle_existing_user(self, token_provider: TokenProvider, app_client: str, resp: AuthResponse):
        if not token_provider.is_valid():
            return resp(HTTPStatus.UNAUTHORIZED, message="Auth invalid")

        last_profile_user_logged_in = token_provider.get_last_access_profile()
        if not last_profile_user_logged_in:
            return resp(HTTPStatus.UNAUTHORIZED, message="You do not have access to the application, contact the admin")

        if not token_provider.upsert_token_provider():
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to upsert token provider")

        token_jwt = TokenJwt.from_access_profile(
            settings=self.settings,
            access_profile=last_profile_user_logged_in,
            aud=app_client,
            exp_minutes=self._DEFAULT_EXPIRATION_TOKEN_TIME
        )

        ap_repo = self.load_repository(AccessProfileModel, last_profile_user_logged_in.to_dict())
        ap_repo.db.upsert(profile_id=last_profile_user_logged_in.profile_id)
        last_profile_user_logged_in.upsert_in_redis(ap_repo.redis,
                                                    expire_in_minutes=self._DEFAULT_EXPIRATION_TOKEN_TIME)

        self.load_repository(ProfileModel).db.update_by_id(
            id=last_profile_user_logged_in.profile_id,
            data={"last_access": DateTime.now()}
        )

        return resp(HTTPStatus.OK, {
            "user_guest_id": None,
            "required_register": False,
            "token": token_jwt.encode_token(self.settings)
        })

    def _handle_user_with_invite(self, token_provider: TokenProvider, app_client: str, req: ProviderAuthRequest,
                                 resp: AuthResponse):
        person = PersonBase(
            full_name=token_provider.full_name,
            first_name=token_provider.first_name,
            last_name=token_provider.last_name,
        )

        user_guest_id = token_provider.user_guest.id
        profile: ProfileModel = token_provider.user_guest.profile

        register = execute_use_case(
            RegisterUserUseCase,
            email=token_provider.email,
            person=person,
            password=GenericUUID.next_id(),
            user_guest_id=user_guest_id,
            subgroup_id=profile.subgroup_id,
            email_verified=True
        )

        if not register.access_profile:
            return resp(register.http_status, message=register.message)

        token_provider._last_access_profile = register.access_profile

        if not token_provider.upsert_token_provider():
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to upsert token provider")

        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=register.access_profile,
            aud=app_client,
            exp_minutes=self._DEFAULT_EXPIRATION_TOKEN_TIME
        )

        # Envia e-mail de boas-vindas
        self._send_welcome_email(token_provider, req)

        return resp(HTTPStatus.CREATED, {
            "user_guest_id": user_guest_id,
            "required_register": False,
            "token": token_jwt.encode_token(self.settings)
        })

    def _register_new_user(self, token_provider: TokenProvider, app_client: str, req: ProviderAuthRequest,
                           resp: AuthResponse):
        person = PersonBase(
            full_name=token_provider.full_name,
            first_name=token_provider.first_name,
            last_name=token_provider.last_name,
        )

        register = execute_use_case(
            RegisterUserUseCase,
            email=token_provider.email,
            person=person,
            password=GenericUUID.next_id(),
            email_verified=True
        )

        if not register.access_profile:
            return resp(register.http_status, message=register.message)

        token_provider._last_access_profile = register.access_profile

        if not token_provider.upsert_token_provider():
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Failed to upsert token provider")

        token_jwt = TokenJwt.from_access_profile(
            settings=self._app.settings,
            access_profile=register.access_profile,
            aud=app_client,
            exp_minutes=self._DEFAULT_EXPIRATION_TOKEN_TIME
        )

        # Envia e-mail de boas-vindas
        self._send_welcome_email(token_provider, req)

        return resp(HTTPStatus.CREATED, {
            "user_guest_id": None,
            "required_register": False,
            "token": token_jwt.encode_token(self.settings)
        })

    def _send_welcome_email(self,
                            access_profile: AccessProfile,
                            target_name: str,
                            target_email: str,
                            cta_url: str,
                            is_new_person: bool = False
                            ):

        subject = "(Porsche CUP) Welcome!!"
        if is_new_person:
            body_text = f"Você se cadastrou como {access_profile.subgroup_name} na plataforma da Porsche CUP Brasil. Acesse agora mesmo e descubra as novidades do seu novo perfil!."
            cta_label = "ACESSAR AGORA"
        else:
            body_text = f"Vocês recebeu um convite e ativou a criação da conta como {access_profile.subgroup_name} na Porsche CUP Brasil.  Acesse agora mesmo e descubra as novidades do seu novo perfil! "
            cta_label = "ACCESSAR AGORA"

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

    @BaseController.route(
        path="/<provider_name>/register/",
        methods=['POST'],
        request=RegisterProviderRequestAuth,
        response=RegisterProviderResponse
    )
    def provider_register(self, req: RegisterProviderRequestAuth, resp: RegisterProviderResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        token_provider = execute_use_case(TokenProviderUseCase, self, provider_name=req.provider_name, token=req.token)

        if not token_provider.is_valid():
            return resp(HTTPStatus.UNAUTHORIZED, message=f"Provider {req.provider_name} or TOKEN unauthorized")

        user_model = self.load_repository(UserModel).db.get_by_id(req.current_profile.user_id)

        token_provider.user = user_model

        if not token_provider.upsert_token_provider():
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message=f"Error upsert TOKEN")

        return resp(HTTPStatus.CREATED, token_provider.to_dict())

    def _get_user_by_email(self, email: EmailStr) -> t.Optional[UserModel]:
        user = self.load_repository(UserModel).db.get_by(email=email)

        if not user:
            user = self.load_repository(UserModel).db.get_by(
                filters=[UserModel.meta_data['emails'].contains([{"email": email}])])

        return user
