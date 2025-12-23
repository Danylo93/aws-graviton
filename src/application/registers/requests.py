import typing as t
from pydantic import Field, EmailStr, HttpUrl, field_validator

from arcs_lib_pca.domain import GenericUUID
from arcs_lib_pca.application import Request

from src.domain.value_objects import PersonBase, ContactsRequest, ProfileRequest, AddressRequest

class RegisterAccountRequest(Request):
    #Dados para criar um novo user_guest
    email: EmailStr = Field(..., description="Email of user")
    person: PersonBase = Field(..., description="Optional data to fill in the person table")
    password: str = Field(..., min_length=6, description="Password of user")
    registration_page_url: HttpUrl = Field(..., description="URL to registration page")

    #ids que podem ser passados em diferentes lugares que requer registro
    user_guest_id: t.Optional[GenericUUID] = Field(default=None, description="Identification type user guest")
    subgroup_id: t.Optional[GenericUUID] = Field(default=None, description="Identification type user guest")

    profile: t.Optional[ProfileRequest] = Field(default=None, description="Optional data to fill in the profile table")
    contacts: t.Optional[t.List[ContactsRequest]] = Field(default=None, description="Optional data to fill in the contacts table")
    address: t.Optional[AddressRequest] = Field(default=None, description="Optional data to fill in the address table")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()