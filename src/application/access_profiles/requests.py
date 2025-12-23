import typing as t

from pydantic import Field

from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead
from arcs_lib_pca.domain.value_objects import GenericUUID

class GetAccessProfileAuth(RequestAuth):
    profile_id: GenericUUID = Field(..., description="id of profile")
    def permissions(self):
        return [CanRead]
    
class GetAllAccessProfileAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1, description="Page")
    per_page: t.Optional[int] = Field(default=10, description="total items per Page")
    
    def permissions(self): 
        return [CanRead]
    
class GetAccessProfilesByUserIDRequestAuth(RequestAuth):
    user_id: GenericUUID = Field(..., description="Unique identifier of user")

    def permissions(self):
        return [CanRead]