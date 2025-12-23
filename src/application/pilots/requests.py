import typing as t
from pydantic import Field, EmailStr, HttpUrl, field_validator

from arcs_lib_pca.domain import GenericUUID
from arcs_lib_pca.application import RequestAuth, Request
from arcs_lib_pca.tools.security.permissions import CanRead, CanWrite, CanDelete, CanUpdate

from src.domain.value_objects import PersonBase, ContactsRequest, PilotStatusEnum, ProfileRequest, AddressRequest, UserEmailRequest


class GetPilotsRequest(Request):
    per_page: t.Optional[int] = Field(default=10, description="Total items per page")
    page: t.Optional[int] = Field(default=1, description="Page")

class GetPilotsRequestAuth(RequestAuth):
    per_page: t.Optional[int] = Field(default=10, description="Total items per page")
    page: t.Optional[int] = Field(default=1, description="Page")


    def permissions(self):
        return [CanRead]

class GetPilotByEmailRequestAuth(RequestAuth):
    email: str = Field(..., description="Email of pilot")

    def permissions(self):
        return [CanRead]

class GetPilotByIdRequestAuth(RequestAuth):
    pilot_id : GenericUUID = Field(..., description="Unique pilot indentifier")
    
    def permissions(self):
        return [CanRead]
    
class ResendInvitationPilotRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    registration_page_url: HttpUrl = Field(..., description="url to registration page")
    def permissions(self):
        return [CanWrite]

class CreatePilotRequestAuth(RequestAuth):
    # Dados do piloto
    identifier: str = Field(..., description="Internal Pilot Identifier")
    status: PilotStatusEnum = Field(..., description="Pilot status")
    bop: t.Optional[float] = Field(None, description="Pilot BOP")

    #Dados para criar um novo user_guest
    email: EmailStr = Field(..., description="Email of user")
    person: PersonBase = Field(..., description="Optional data to fill in the person table")
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
    
class UpdatePilotRequestAuth(RequestAuth):
    pilot_id : GenericUUID = Field(..., description="Unique pilot indentifier")

    # Dados do piloto
    identifier: str = Field(..., description="Internal Pilot Identifier")
    status: PilotStatusEnum = Field(..., description="Pilot status")
    bop: t.Optional[float] = Field(None, description="Pilot BOP")

    #Dados para criar um novo user_guest
    emails: t.List[UserEmailRequest] = Field(min=1, description="List of user emails")
    person: PersonBase = Field(..., description="Optional data to fill in the person table")
    contacts: t.Optional[t.List[ContactsRequest]] = Field(None, description="Optional data to fill in the contacts table")
    address: t.Optional[AddressRequest] = Field(None, description="data to fill in the address table")
    profile: t.Optional[ProfileRequest] = Field(None, description="Optional data to fill in the profile table")

    def permissions(self):
        return [CanUpdate]    
    
class DeletePilotRequestAuth(RequestAuth):
    pilot_id : GenericUUID = Field(..., description="Unique pilot indentifier")

    def permissions(self):
        return [CanDelete]