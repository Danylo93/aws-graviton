import typing as t

import google.oauth2.id_token as google_id_token
import google.auth.transport.requests as google_requests
import requests

import jwt
from jwt.algorithms import RSAAlgorithm

from arcs_lib_pca.use_case import UseCase, execute_use_case
from arcs_lib_pca.domain.value_objects import AccessProfile, GenericUUID, DateTime
from arcs_lib_pca.infrastructure.repository import Repositories

from .access_profile import LoadAccessProfilesUseCase
from src.infrastructure.models import ProviderModel, UserModel, UserGuestModel


class TokenProvider:
    _is_valid: bool
    _user: t.Optional[UserModel]
    _user_guest: t.Optional[UserGuestModel]
    _access_profiles: t.Dict[GenericUUID, t.List[AccessProfile]]
    _last_access_profile: t.Optional[AccessProfile]

    provider_name: t.Optional[str]

    # Dados do token
    aud: t.Optional[str]
    user_object_id: t.Optional[str]
    group_object_id: t.Optional[str]
    email: t.Optional[str]
    email_verified: t.Optional[DateTime]
    full_name: t.Optional[str]
    first_name: t.Optional[str]
    last_name: t.Optional[str]
    profile_picture_url: t.Optional[str]
    exp: t.Optional[int]
    meta_data: t.Dict[str, t.Any]

    def __init__(self, **kwargs):
        self._is_valid = False
        self._user = None
        self._user_guest = None
        self._access_profiles = {}
        self._last_access_profile = None

        self.provider_name = None
        self.aud = None
        self.user_object_id = None
        self.group_object_id = None
        self.email = None
        self.email_verified = None
        self.full_name = None
        self.first_name = None
        self.last_name = None
        self.profile_picture_url = None
        self.exp = None
        self.meta_data = {}

    def is_valid(self) -> bool:
        return self._is_valid

    @property
    def user(self) -> t.Optional[UserModel]:
        if not self._is_valid:
            return None

        if self._user:
            return self._user

        provider_repo = Repositories(ProviderModel())
        user_repo = Repositories(UserModel())

        if self._last_access_profile:
            self._user = user_repo.db.get_by_id(self._last_access_profile.user_id, load=["person"])
            if not self._user:
                raise ValueError("ERROR INTERNAL in access token of user")
            return self._user

        if self.user_object_id:
            provider_model = provider_repo.db.get_by(user_object_id=self.user_object_id)
            if provider_model:
                self._user = provider_model.user
                if not self._user:
                    provider_repo.db.delete(id=provider_model.id)
                    raise ValueError("ERROR INTERNAL in access token of user")
                return self._user

        if self.email:
            if user_repo.db.contains(email=self.email):
                self._user = user_repo.db.get_by(email=self.email)
                return self._user

            if provider_repo.db.contains(email=self.email):
                provider_model = provider_repo.db.get_by(email=self.email)
                self._user = provider_model.user
                if not self._user:
                    provider_repo.db.delete(id=provider_model.id)
                    raise ValueError("ERROR INTERNAL in access token of user")
                return self._user

        return None

    @user.setter
    def user(self, user_model: UserModel):
        if isinstance(user_model, UserModel):
            self._user = user_model

    @property
    def user_guest(self) -> t.Optional[UserGuestModel]:
        if not self._is_valid:
            return None

        if self._user_guest:
            return self._user_guest

        guest_repo = Repositories(UserGuestModel())
        if self.email:
            guest = guest_repo.db.get_by(email=self.email, load=["profile"])
            if guest:
                self._user_guest = guest
                return self._user_guest

        return None

    @user_guest.setter
    def user_guest(self, user_guest_model: UserGuestModel):
        if isinstance(user_guest_model, UserGuestModel):
            self._user_guest = user_guest_model

    def upsert_token_provider(self) -> t.Optional[ProviderModel]:
        if not self.provider_name:
            return None

        repo = Repositories(ProviderModel())
        model = repo.model

        model.user_id = self.user.id if self.user else None
        model.user_guest_id = self.user_guest.id if self.user_guest else None
        model.user_object_id = self.user_object_id
        model.group_object_id = self.group_object_id
        model.provider_name = self.provider_name
        model.full_name = self.full_name
        model.first_name = self.first_name
        model.last_name = self.last_name
        model.email = self.email
        model.email_verified = DateTime.now() if self.email_verified else None
        model.picture_url = self.profile_picture_url
        model.meta_data = self.meta_data

        return repo.db.upsert(
            model,
            user_id=self.user.id if self.user else None,
            provider_name=self.provider_name,
            user_object_id=self.user_object_id
        )

    def get_last_access_profile(self) -> t.Optional[AccessProfile]:
        if self._last_access_profile:
            return self._last_access_profile

        if not self._access_profiles:
            if self.user:
                self._access_profiles = execute_use_case(
                    LoadAccessProfilesUseCase,
                    user_id=self.user.id,
                    insert_user_object_id=self.user_object_id,
                    insert_group_object_id=self.group_object_id
                )
            elif self.user_guest:
                self._access_profiles = execute_use_case(
                    LoadAccessProfilesUseCase,
                    user_guest_id=self.user_guest.id,
                    insert_user_object_id=self.user_object_id,
                    insert_group_object_id=self.group_object_id
                )
            elif self.user_object_id:
                self._access_profiles = execute_use_case(
                    LoadAccessProfilesUseCase,
                    user_object_id=self.user_object_id
                )
            else:
                return None

            for _, profiles in self._access_profiles.items():
                if profiles:
                    self._last_access_profile = profiles[0]
                    return self._last_access_profile

        return None

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {
            "user": self.user.to_dict() if self.user else None,
            "user_guest": self.user_guest.to_dict() if self.user_guest else None,
            "aud": self.aud,
            "user_object_id": self.user_object_id,
            "group_object_id": self.group_object_id,
            "email": str(self.email).lower().strip(),
            "email_verified": self.email_verified,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_picture_url": self.profile_picture_url,
            "exp": self.exp
        }


class TokenProviderUseCase(UseCase[TokenProvider]):

    def decode_token_google(self, token_provider: TokenProvider, token: str) -> TokenProvider:
        try:
            # Decodifica e extrai dados do token do Google
            data = google_id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                audience=self.app.settings.google_app_id
            )
            token_provider._is_valid = True

            token_provider.aud = data.get("aud")
            token_provider.user_object_id = data.get("sub")
            token_provider.group_object_id = data.get("iss")
            token_provider.email = data.get("email")
            token_provider.email_verified = DateTime.now()
            token_provider.full_name = data.get("name")
            token_provider.first_name = data.get("given_name")
            token_provider.last_name = data.get("family_name")
            token_provider.profile_picture_url = data.get("picture")
            token_provider.exp = data.get("exp")
            token_provider.meta_data = data

            return token_provider
        except Exception:
            return token_provider

    def decode_token_microsoft(self, token_provider: TokenProvider, token: str) -> TokenProvider:
        try:
            # Carrega as chaves públicas da Microsoft
            def get_microsoft_public_keys(kid: str):
                url = f"https://login.microsoftonline.com/{self.app.settings.azure_tenant_id}/discovery/v2.0/keys"
                response = requests.get(url)
                response.raise_for_status()
                for key in response.json().get("keys", []):
                    if key.get("kid") == kid:
                        return RSAAlgorithm.from_jwk(key)
                return None

            header = jwt.get_unverified_header(token)
            public_key = get_microsoft_public_keys(header.get("kid"))
            if not public_key:
                raise ValueError("Chave pública não encontrada.")

            data = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.app.settings.microsoft_app_id
            )

            token_provider._is_valid = True
            token_provider.aud = data.get("aud")
            token_provider.user_object_id = data.get("oid")
            token_provider.group_object_id = data.get("appid")
            token_provider.email = data.get("upn")
            token_provider.email_verified = DateTime.now()
            token_provider.full_name = data.get("name")
            token_provider.first_name = data.get("given_name")
            token_provider.last_name = data.get("family_name")
            token_provider.profile_picture_url = data.get("picture")
            token_provider.exp = data.get("exp")
            token_provider.meta_data = data

            return token_provider
        except Exception:
            return token_provider

    def decode_token_apple(self, token_provider: TokenProvider, token: str) -> TokenProvider:
        try:
            # Obtém chaves da Apple
            resp = requests.get(self.app.settings.apple_keys_url)
            resp.raise_for_status()
            keys = resp.json().get("keys", [])

            headers = jwt.get_unverified_header(token)
            public_key = None
            for key in keys:
                if key.get("kid") == headers.get("kid"):
                    public_key = RSAAlgorithm.from_jwk(key)
                    break
            if not public_key:
                raise ValueError("Chave pública não encontrada.")

            data = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.app.settings.apple_app_id
            )

            token_provider._is_valid = True
            token_provider.aud = data.get("aud")
            token_provider.user_object_id = data.get("sub")
            token_provider.group_object_id = data.get("iss")
            token_provider.email = data.get("email")
            token_provider.email_verified = DateTime.now()
            token_provider.full_name = data.get("name")
            token_provider.first_name = data.get("given_name")
            token_provider.last_name = data.get("family_name")
            token_provider.profile_picture_url = data.get("picture")
            token_provider.exp = data.get("exp")
            token_provider.meta_data = data

            return token_provider
        except Exception:
            return token_provider

    def execute(self,
                 provider_name: t.Literal["GOOGLE", "MICROSOFT", "APPLE"],
                 token: str
            ) -> TokenProvider:
        token_provider = TokenProvider()
        pn = provider_name.upper()
        if pn == "GOOGLE":
            token_provider.provider_name = "GOOGLE"
            return self.decode_token_google(token_provider, token)
        if pn == "MICROSOFT":
            token_provider.provider_name = "MICROSOFT"
            return self.decode_token_microsoft(token_provider, token)
        if pn == "APPLE":
            token_provider.provider_name = "APPLE"
            return self.decode_token_apple(token_provider, token)
        return token_provider
