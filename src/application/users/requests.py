import typing as t

from pydantic import EmailStr, Field, HttpUrl, field_validator

from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanUpdate, CanWrite
from arcs_lib_pca.domain.value_objects import GenericUUID

from src.domain.value_objects import AddressRequest, ContactsRequest, PersonBase, ProfileRequest, UserEmailRequest


class PilotGetUserRequestAuth(RequestAuth):
    user_id: GenericUUID = Field(..., description="Id of user")
    profile_id: GenericUUID = Field(..., description="id of profile")

    def permissions(self):
        return [CanRead]
    
class PilotUpdateUserRequestAuth(RequestAuth):
    user_id: GenericUUID = Field(..., description="Id of user")
    profile_id: GenericUUID = Field(..., description="id of profile")    

    email: EmailStr = Field(..., description="Email of user")
    person: PersonBase = Field(..., description="Optional data to fill in the person table")
    subgroup_id: GenericUUID = Field(..., description="Indetification type user guest")
    profile: t.Optional[ProfileRequest] = Field(None, description="Optional data to fill in the profile table")
    contacts: t.Optional[t.List[ContactsRequest]] = Field(None, description="Optional data to fill in the contacts table")
    address: t.Optional[AddressRequest] = Field(None, description="data to fill in the address table")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()

    def permissions(self): 
        return [CanUpdate]
    
class GetUserRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="id of profile")
    
    def permissions(self):
        return [CanRead]
    
class UpdateUserRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="id of profile")    

    email: t.Optional[EmailStr] = Field(None, description="Email of user")
    person: PersonBase = Field(..., description="Optional data to fill in the person table")
    subgroup_id: GenericUUID = Field(..., description="Indetification type user guest")
    profile: t.Optional[ProfileRequest] = Field(None, description="Optional data to fill in the profile table")
    contacts: t.Optional[t.List[ContactsRequest]] = Field(None, description="Optional data to fill in the contacts table")
    address: t.Optional[AddressRequest] = Field(None, description="data to fill in the address table")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: t.Optional[str]) -> t.Optional[str]:
        if value is None:
            return value
        return str(value).lower().strip()
    
    def permissions(self): 
        return [CanUpdate]

class GetUserByEmailRequestAuth(RequestAuth):
    email: str = Field(..., description="Email of user")

    def permissions(self):
        return [CanRead]

class UpsertUserEmailsRequestAuth(RequestAuth):
    user_id: GenericUUID = Field(..., description="Id of user")
    emails: t.List[UserEmailRequest] = Field(..., min=1, description="List of emails to add")

    def permissions(self):
        return [CanWrite]

class GetUserEmailsRequestAuth(RequestAuth):
    user_id: GenericUUID = Field(..., description="Id of user")

    def permissions(self):
        return [CanRead]
