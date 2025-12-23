import typing as t

from pydantic import Field

from arcs_lib_pca.application import RequestAuth, Request
from arcs_lib_pca.domain import File, GenericUUID
from arcs_lib_pca.tools.security.permissions import CanEverything, CanRead

class GetAllPermissionsAuth(RequestAuth):
    page: t.Optional[int] = Field(default=1, description="Page")
    per_page: t.Optional[int] = Field(default=10, description="Total items per page")
    
    def permissions(self): 
        return [CanEverything]  # Acesso amplo a todos os serviços

class CreatePermissionAuth(RequestAuth):
    app_client_id: GenericUUID = Field(..., description="Foreing Key for AppClient")
    service_id: GenericUUID = Field(..., description="Foreing Key for Service")
    
    get: t.Optional[bool] = Field(default=False, description="Permission to get/read data from the service")
    post: t.Optional[bool] = Field(default=False, description="Permission to create/write data to the service")
    put: t.Optional[bool] = Field(default=False, description="Permission to update/change service data")
    delete: t.Optional[bool] = Field(default=False, description="Permission to delete data from the service")
    
    def permissions(self): 
        return [CanEverything]  # Acesso total para criar serviços

class GetPermissionAuth(RequestAuth):
    permission_id: t.Union[GenericUUID, str] = Field(..., description="ID of the permission")
    
    def permissions(self): 
        return [CanRead]  # Permissão de leitura para visualizar informações do serviço

class UpdatePermissionAuth(RequestAuth):
    permission_id: GenericUUID = Field(..., description="ID of the permission")
    get: t.Optional[str] = Field(default=False, description="Permission to get/read data from the service")
    post: t.Optional[bool] = Field(default=False, description="Permission to create/write data to the service")
    put: t.Optional[bool] = Field(default=False, description="Permission to update/change service data")
    delete: t.Optional[bool] = Field(default=False, description="Permission to delete data from the service")
    
    def permissions(self): 
        return [CanEverything]  # Acesso total para atualizar os dados de um serviço

class DeletePermissionAuth(RequestAuth):
    permission_id: GenericUUID = Field(..., description="ID of the permission")
    
    def permissions(self): 
        return [CanEverything]  # Acesso total para excluir logicamente um serviço
