import typing as t
from pydantic import Field, EmailStr, HttpUrl, field_validator

from arcs_lib_pca.domain import GenericUUID
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanWrite, CanDelete, CanUpdate

from src.domain.value_objects import PersonBase, ContactsRequest, ProfileRequest, AddressRequest

class CreateInviteRequest(RequestAuth):
    #Dados para criar um novo user_guest
    email: EmailStr = Field(..., description="Email of user")
    person: PersonBase = Field(..., description="Optional data to fill in the person table")
    subgroup_id: GenericUUID = Field(..., description="Indetification type user guest")
    registration_page_url: HttpUrl = Field(..., description="url to registration page")
    profile: t.Optional[ProfileRequest] = Field(None, description="Optional data to fill in the profile table")
    contacts: t.Optional[t.List[ContactsRequest]] = Field(None, description="Optional data to fill in the contacts table")
    address: t.Optional[AddressRequest] = Field(None, description="data to fill in the address table")

    #ids que podem ser passados em diferentes lugares que requer registro
    user_id: t.Optional[GenericUUID] = Field(default=None, description="identification type user guest")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()

    def permissions(self):
        return [CanWrite]
    
class ResendInvitationRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="id of profile")
    registration_page_url: HttpUrl = Field(..., description="url to registration page")
    def permissions(self):
        return [CanWrite]
    
class GenerateInviteRequestAuth(RequestAuth):
    email: EmailStr = Field(..., description="Email of user")
    registration_page_url: HttpUrl = Field(..., description="url to registration page")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()
    
    def permissions(self):
        return [CanWrite]
    
class DeleteInviteRequestAuth(RequestAuth):
    user_id: str = Field(..., description="Id of user accounts")

    def permissions(self):
        return [CanDelete]