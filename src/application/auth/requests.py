from pydantic import Field, HttpUrl, field_validator, EmailStr
from arcs_lib_pca.domain.value_objects import Email, GenericUUID
from arcs_lib_pca.application import Request, RequestAuth


class EmailPassAuthRequest(Request):
    email: EmailStr = Field(..., description="Email of the user")
    password: str = Field(..., description="Password for the user's account")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()


class ProviderAuthRequest(Request):
    provider_name: str = Field(..., description="Provider name (GOOGLE, MICROSOFT, APPLE)")
    token: str = Field(..., description="Provider-issued JWT token")


class RegisterProviderRequestAuth(RequestAuth):
    provider_name: str = Field(..., description="name of provider")
    token: str = Field(..., description="Provider-issued JWT token")
