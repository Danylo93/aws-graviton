import typing as t
from pydantic import Field, field_validator

from arcs_lib_pca.domain.value_objects import File
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.tools.security.permissions import CanRead, CanEverything

from src.domain.value_objects import BasePermission

class CreateGroupRequestAuth(RequestAuth):
    name: str = Field(..., description="Name of group")
    description: str = Field(..., description="Description of group")
    meta_data: t.Optional[dict]= Field(None, description="Meta Data of group")
    image: t.Optional[File] = Field(None, description="Image of group")
    app_clients: t.List[BasePermission] = Field(None, description="App Clients, which this group has permission to")
    is_mandatory: t.Optional[bool] = Field(False, description="Is mandatory")

    @field_validator('name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name
    
    def permissions(self):
        return [CanEverything]

class GroupGetRequestAuth(RequestAuth):
    page: int = Field(default=1,ge=1, description="page")
    per_page: int = Field(default=10,ge=1, description="per_page")

    def permissions(self):
        return [CanRead]


class GroupIdOrNameGetRequestAuth(RequestAuth):
    group_id_or_name: str = Field(..., description="id for group")

    @property
    def has_id(self) -> bool:
        try:
            GenericUUID.validate(self.group_id_or_name)
            return True
        except:
            return False

    def permissions(self):
        return [CanRead]

class GetServicesByGroupIdOrNameRequestAuth(RequestAuth):
    group_id_or_name: t.Union[GenericUUID, str] = Field(..., description="id for group")
    
    @property
    def has_id(self) -> bool:
        try:
            GenericUUID.validate(self.group_id_or_name)
            return True
        except:
            return False

    def permissions(self):
        return [CanRead]

class UpdateGroupRequestAuth(RequestAuth):
    group_id: GenericUUID = Field(..., description="id for group")
    name: t.Optional[str] = Field(None, description="Name of the user")
    description: t.Optional[str] = Field(None, description="Description of group")
    image: t.Optional[File] = Field(None, description="Image of group")
    meta_data: t.Optional[t.Dict[str, t.Any]] = Field(None, description="Metadata associated with the group")
    app_clients: t.Optional[t.List[BasePermission]] = Field(None, description="App Clients, which this group has permission to")
    is_mandatory: t.Optional[bool] = Field(False, description="Is mandatory")


    @field_validator('name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name
    
    def has_app_client(self, app_client_name: str) -> bool:
        for app_client in self.app_clients:
            if app_client.name == app_client_name:
                return True
        return False
    
    def permissions(self):
        return [CanEverything]

class DeleteGroupIdRequestAuth(RequestAuth):
    group_id: str = Field(..., description="id for group")

    def permissions(self):
        return [CanEverything]