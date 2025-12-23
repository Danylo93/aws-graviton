import typing as t

from pydantic import Field, BaseModel

from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanWrite, CanDelete, CanUpdate
from arcs_lib_pca.domain.value_objects import GenericUUID

from src.domain.value_objects import KeyContactRole


class GetAllKeyContactRequestAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1, description="Page")
    per_page: t.Optional[int] = Field(default=10, description="total items per Page")

    def permissions(self):
        return [CanRead]

class CreateKeyContactRequestAuth(RequestAuth):

    name: str = Field(..., description="name", min_length=1)
    contact: str = Field(..., description="contact", min_length=1)
    role: KeyContactRole = Field(..., description="role")

    def permissions(self):
        return [CanWrite]

class GetKeyContactRequestAuth(RequestAuth):
    key_contact_id: GenericUUID = Field(..., description="id of key_contact")

    def permissions(self):
        return [CanRead]


class UpdateKeyContactRequestAuth(RequestAuth):
    key_contact_id: GenericUUID = Field(..., description="id of key_contact")
    name: str = Field(..., description="name", min_length=1)
    contact: str = Field(..., description="contact", min_length=1)
    role: KeyContactRole = Field(..., description="role")

    def permissions(self):
        return [CanUpdate]

class DeleteKeyContactRequestAuth(RequestAuth):
    key_contact_id: GenericUUID = Field(..., description="id of key_contact")

    def permissions(self):
        return [CanDelete]

# Key Contact Role

class GetAllKeyContactRoleRequestAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1, description="Page")
    per_page: t.Optional[int] = Field(default=10, description="total items per Page")


    def permissions(self):
        return [CanRead]


class CreateKeyContactRoleRequestAuth(RequestAuth):
    name: str = Field(..., description="name", min_length=1)

    def permissions(self):
        return [CanWrite]

class UpdateKeyContactRoleRequestAuth(RequestAuth):
    key_contact_role_id: GenericUUID = Field(..., description="id of key_contact_role")
    name: str = Field(..., description="name", min_length=1)

    def permissions(self):
        return [CanUpdate]


class DeleteKeyContactRoleRequestAuth(RequestAuth):
    key_contact_role_id: GenericUUID = Field(..., description="id of key_contact_role")

    def permissions(self):
        return [CanDelete]