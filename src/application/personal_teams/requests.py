import typing as t
from src.domain.value_objects import ProfilePermission
from pydantic import EmailStr, Field, HttpUrl, field_validator
from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanUpdate, CanDelete, CanWrite


class GetAPersonalTeamsByPilotIdRequestAuth(RequestAuth):
    page: int = Field(default=1, ge=1, description="page")
    per_page: int = Field(default=10, ge=1, description="per_page")
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    subgroup_name : t.Optional[str] = Field(None, description="Name of the subgroup")
    
    def permissions(self):
        return [CanRead]


class CreatePersonalTeamByPilotIdRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    
    subgroup_id: GenericUUID = Field(..., description="ID of the subgroup")
    name: str = Field(..., min_length=1, description="Name of the member")
    email: EmailStr = Field(..., description="Email of the member")
    contact: str = Field(..., description="Contact information", min_length=5)
    registration_page_url: HttpUrl = Field(..., description="URL from registration redirect")
    acceptance_page_url: HttpUrl = Field(..., description="URL from acceptance redirect")
    member_permissions: t.List[ProfilePermission] = Field(
        ..., description="List of controllers identified by their namespace and respective access rules"
    )

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()
    
    def permissions(self):
        return [CanWrite]


class DeletePersonalTeamIdWithMemberIdRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    member_id: GenericUUID = Field(..., description="id of member")

    def permissions(self):
        return [CanDelete]


class GetPersonalTeamIdWithMemberIdRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    member_id: GenericUUID = Field(..., description="id of member")

    def permissions(self):
        return [CanRead]

class GetPersonalTeamByMemberIdRequestAuth(RequestAuth):
    member_id: GenericUUID = Field(..., description="id of member")

    def permissions(self):
        return [CanRead]


class UpdatePersonalTeamIdWithMemberIdRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    member_id: GenericUUID = Field(..., description="id of member")
    subgroup_id: GenericUUID = Field(..., description="ID of the subgroup")
    name: str = Field(..., min_length=1, description="Name of the member")
    email: EmailStr = Field(..., description="Email of the member")

    member_permissions: t.List[ProfilePermission] = Field(
        ..., description="List of controllers identified by their namespace and respective access rules"
    )

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()

    def permissions(self):
        return [CanWrite, CanUpdate]

class UpdateMemberAcceptanceRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="id of pilot")
    member_id: GenericUUID = Field(..., description="id of member")

    def permissions(self):
        return [CanUpdate]