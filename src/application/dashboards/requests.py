from pydantic import Field
from typing import Optional

from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead

class GetDashRequestAuth(RequestAuth):
    page: int = Field(default=1,ge=1, description="page")
    per_page: int = Field(default=10,ge=1, description="per_page")
    refresh: Optional[bool] = Field(default=False, description="refresh query")

    def permissions(self):
        return [CanRead]