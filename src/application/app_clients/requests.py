import typing as t

from pydantic import Field, field_validator

from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanEverything, CanRead, CanWrite, CanUpdate
from arcs_lib_pca.domain.value_objects import GenericUUID, File
from arcs_lib_pca.utils.string import to_snake_case


class GetAppClientAuth(RequestAuth):
    client_name: str = Field(..., description="Name of the application client")
    
    @field_validator('client_name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name
    
    def permissions(self):
        return [CanRead]

class GetAppClientEnvsAuth(RequestAuth):
    client_name: str = Field(..., description="Name of the application client")

    @field_validator('client_name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name

    def permissions(self):
        return [CanRead]
    
class GetAllAppClientAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1, description="Page")
    per_page: t.Optional[int] = Field(default=10, description="total items per Page")
    
    def permissions(self): 
        return [CanEverything]

class CreateAppClientAuth(RequestAuth):
    name: str = Field(..., description="Name unique of App Client")
    name_friendly: t.Optional[str] = Field(None, description="Name humanized of App Client")
    image: t.Optional[File] = Field(None, description="Image or Icon of App client")
    description: t.Optional[str] = Field(None, description="Details humanized of App Client")
    
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
    
class UpdateAppClientAuth(RequestAuth):
    client_name: str = Field(..., description="Name of the application client")

    image: t.Optional[File] = Field(None, description="Image or Icon of App client")
    name: t.Optional[str] = Field(None, description="Name unique of App Client")
    name_friendly: t.Optional[str] = Field(None, description="Name humanized of App Client")
    description: t.Optional[str] = Field(None, description="Details humanized of App Client")
    
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

class DeleteAppClientAuth(RequestAuth):
    client_name: str = Field(..., description="Name of the application client")
    
    @field_validator('client_name', mode='before')
    def transform_name_to_snake_case(cls, client_name: str) -> str:
        """
        Valida e transforma o campo 'client_name' para o formato snake_case.
        """
        if client_name:
            return to_snake_case(client_name)
        return client_name
    
    def permissions(self): 
        return [CanEverything]
    
class GetConfigAuth(RequestAuth):
    profile_id: t.Optional[GenericUUID] = Field(..., description="")
    client_name: str = Field(..., description="Name of the application client")
    
    @field_validator('client_name', mode='before')
    def transform_name_to_snake_case(cls, client_name: str) -> str:
        """
        Valida e transforma o campo 'client_name' para o formato snake_case.
        """
        if client_name:
            return to_snake_case(client_name)
        return client_name
    
    def permissions(self): 
        return [
            CanRead
        ]

class UpsertConfigAuth(RequestAuth):
    client_name: str = Field(..., description="Name of the application client")
    profile_id: t.Optional[GenericUUID] = Field(default=None, description="")
    allow_notifications: t.Optional[bool] = Field(default=False, description="")
    face_id: t.Optional[bool] = Field(default=False, description="")
    biometrics: t.Optional[bool] = Field(default=False, description="")
    location: t.Optional[bool] = Field(default=False, description="")
    
    @field_validator('client_name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name
    
    def permissions(self): 
        return [
            CanRead, 
            CanWrite, 
            CanUpdate
        ]

