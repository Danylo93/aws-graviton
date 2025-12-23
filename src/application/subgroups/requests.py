import typing as t
from pydantic import Field, field_validator

from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.domain.value_objects import GenericUUID
from arcs_lib_pca.tools.security.permissions import CanRead, CanEverything

from src.domain.value_objects import SubGroupPermission

class CreateSubGroupRequestAuth(RequestAuth):
    group_id: GenericUUID = Field(..., description="id for group")
    name: str = Field(..., description="Name of the user")
    description: str = Field(..., description="Description of subgroup")
    subgroup_permissions: t.List[SubGroupPermission] = Field(None, description="Services, which this subgroup has permission to")
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

class SubGroupGetRequestAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1,ge=1, description="page")
    per_page: t.Optional[int] = Field(default=10,ge=1, description="per_page")
    group_name: t.Optional[str] = Field(default=None, description="Group name to filter subgroups")

    def permissions(self):
        return [CanRead]

class SubGroupIdGetRequestAuth(RequestAuth):
    subgroup_id_or_name: str = Field(..., description="id for subgroup")

    @property
    def has_id(self) -> bool:
        try:
            GenericUUID.validate(self.subgroup_id_or_name)
            return True
        except:
            return False

    def permissions(self):
        return [CanRead]

class UpdateSubGroupRequestAuth(RequestAuth):
    subgroup_id: GenericUUID = Field(..., description="id for subgroup")
    name: t.Optional[str] = Field(None, description="Name of the user")
    description: t.Optional[str] = Field(None, description="Description of subgroup")
    subgroup_permissions: t.Optional[t.List[SubGroupPermission]] = Field(None, description="Services, which this subgroup has permission to")
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

class DeleteSubGroupIdRequestAuth(RequestAuth):
    subgroup_id: str = Field(..., description="id for subgroup")

    def permissions(self):
        return [CanEverything]
