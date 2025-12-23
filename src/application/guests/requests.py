import typing as t
from pydantic import Field
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.tools.security.permissions import CanRead

class GetAllGuestRequestAuth(RequestAuth):
    page: int = Field(default=1,ge=1, description="page")
    per_page: int = Field(default=10,ge=1, description="per_page")

    def permissions(self):
        return [CanRead]

class GetGuestRequestAuth(RequestAuth):
    guest_id: GenericUUID = Field(..., description="guest_id")

    def permissions(self):
        return [CanRead]
