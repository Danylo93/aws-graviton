import typing as t

from pydantic import Field, field_validator

from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.domain import File, GenericUUID
from arcs_lib_pca.tools.security.permissions import CanEverything, CanRead
from arcs_lib_pca.utils.string import to_snake_case

class GetAllServicesAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1, description="Page")
    per_page: t.Optional[int] = Field(default=10, description="Total items per page")

    def permissions(self): 
        return [CanEverything]  # Acesso amplo a todos os serviços

class CreateServiceAuth(RequestAuth):
    name: str = Field(..., description="Unique name of the service")
    internal_url: str = Field(..., description="url for internal use between microservices")
    external_url: str = Field(..., description="url for external use through APIM")
    namespaces: t.List[str] = Field(..., description="List of namespaces associated with the service")
    
    icon: t.Optional[File] = Field(default=None, description="Icon of the service")
    name_friendly: t.Optional[str] = Field(default="", description="Human-readable name of the service")
    domain: t.Optional[str] = Field(default="", description="Logical domain of the microservice, referring to the business rule")
    description: t.Optional[str] = Field(default="", description="Service description")
    version: t.Optional[str] = Field(default="", description="Service version")
    port: t.Optional[str] = Field(default="", description="HTTP port referenced in the app container ingress")
    
    def permissions(self):
        return [CanEverything]  # Acesso total para criar serviços
    
    @field_validator('name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name

class GetServiceAuth(RequestAuth):
    service_id: GenericUUID = Field(..., description="ID of the service OR Unique name of the service")
    
    def permissions(self): 
        return [CanRead]  # Permissão de leitura para visualizar informações do serviço

class UpdateServiceAuth(RequestAuth):
    id: GenericUUID = Field(..., description="ID of the service")
    icon: t.Optional[File] = Field(None, description="Icon of the service")
    name: t.Optional[str] = Field(None, description="Unique name of the service")
    name_friendly: t.Optional[str] = Field(default="", description="Human-readable name of the service")
    domain: t.Optional[str] = Field(default="", description="Logical domain of the microservice, referring to the business rule")
    description: t.Optional[str] = Field(default="", description="Service description")
    version: t.Optional[str] = Field(default="", description="Service version")
    host: t.Optional[str] = Field(default="", description="url for internal use between microservices")
    url: t.Optional[str] = Field(default="", description="url for external use through APIM")
    port: t.Optional[str] = Field(default="", description="HTTP port referenced in the app container ingress")
    namespaces: t.Optional[t.List[str]] = Field(None, description="List of namespaces associated with the service")
    
    def permissions(self): 
        return [CanEverything]  # Acesso total para atualizar os dados de um serviço
    
    @field_validator('name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name

class DeleteServiceAuth(RequestAuth):
    service_id: GenericUUID = Field(..., description="ID of the service")

    def permissions(self): 
        return [CanEverything]  # Acesso total para excluir logicamente um serviço
