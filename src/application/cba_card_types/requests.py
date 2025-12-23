import typing as t
from pydantic import Field
from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanDelete, CanWrite, CanUpdate

class GetCBACardTypeRequestAuth(RequestAuth):
    page: int = Field(default=1,ge=1, description="page")
    per_page: int = Field(default=10,ge=1, description="per_page")

    def permissions(self):
        return [CanRead]


class GetCBACardTypeIdRequestAuth(RequestAuth):
    cba_card_type_id: GenericUUID = Field(..., description="id of cba_card_type")

    def permissions(self):
        return [CanRead]

class CreateCBACardTypeIdRequestAuth(RequestAuth):
    type : str = Field(...)
    description : t.Optional[str] = Field(default=None, description="")
    
    def permissions(self):
        return [CanWrite]
    
class UpdateCBACardTypeIdRequestAuth(RequestAuth):
    cba_card_type_id: GenericUUID = Field(..., description="id of cba_card_type")

    type : str = Field(...)
    description : t.Optional[str] = Field(default=None, description="")
    
    def permissions(self):
        return [CanUpdate]
    
class DeleteCBACardTypeIdRequestAuth(RequestAuth):
    cba_card_type_id: GenericUUID = Field(..., description="id of cba_card_type")

    def permissions(self):
        return [CanDelete]