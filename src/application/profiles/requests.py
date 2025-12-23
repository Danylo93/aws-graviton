import typing as t
from pydantic import Field
from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanUpdate, CanDelete, CanWrite

from src.domain.value_objects import ProfilePermission, File


class GetProfileRequestAuth(RequestAuth):
    page: int = Field(default=1,ge=1, description="page")
    per_page: int = Field(default=10,ge=1, description="per_page")
    group_name: t.Optional[str] = Field(None, description="Filter by group_name")
    subgroup_name: t.Optional[str] = Field(None, description="Filter by subgroup_name")

    def permissions(self):
        return [CanRead]


class GetProfileIdRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="id of profile")

    def permissions(self):
        return [CanRead]


class GetProfilePermissionRequestAuth(RequestAuth):
    page: int = Field(default=1,ge=1, description="page")
    per_page: int = Field(default=10,ge=1, description="per_page")

    def permissions(self):
        return [CanRead]


class UpdateProfileRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="Profile ID that's should be deleted")

    description: t.Optional[str] = Field(default=None, description="Description of profile")
    pictures: t.Optional[t.Dict[str, File]] = Field(default={}, description="key and image of profile")
    profile_permissions: t.Optional[t.List[ProfilePermission]] = Field(default=None, description="permissions of profile")

    def permissions(self):
        return [CanUpdate]

class DeleteProfileRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="Profile ID that's should be deleted")

    def permissions(self):
        return [CanDelete]

class GenerateTokenRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="Unique identifier of the profile that you want a token to be generated")

    def permissions(self):
        return [CanWrite]

class DeleteProfilePictureRequestAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="Profile ID that's should be deleted")
    key: str = Field(..., description="Unique identifier of the profile that you want to delete")

    def permissions(self):
        return [CanDelete]