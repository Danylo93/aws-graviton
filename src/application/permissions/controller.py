from http import HTTPStatus
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.domain.value_objects import AppClientPermissions

from src.infrastructure.models import PermissionModel, AppClientModel, ServiceModel

from .requests import(
    GetAllPermissionsAuth,
    CreatePermissionAuth,
    GetPermissionAuth,
    UpdatePermissionAuth, 
    DeletePermissionAuth
)
from .responses import(
    PermissionAllGetResponse,
    PermissionCreatedResponse,
    PermissionGetResponse,
    PermissionUpdatedResponse,
    PermissionDeletedResponse,
)

class PermissionsController(BaseController):
    
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllPermissionsAuth,
        response=PermissionAllGetResponse)
    def get_all_permissions(self, req: GetAllPermissionsAuth, resp: PermissionAllGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        permission_repo = self.load_repository(PermissionModel)
        subquery = QueryParamsUseCase.load(req.params)
        data = permission_repo.db.with_query(subquery).paginate(page=req.page, per_page=req.per_page, load=["app_client", "service"])

        return resp(HTTPStatus.OK, data, "Request Succefully")

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreatePermissionAuth,
        response=PermissionCreatedResponse)
    def create_permission(self, req: CreatePermissionAuth, resp: PermissionCreatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        permission_repo = self.load_repository(PermissionModel)

        if permission_repo.db.contains(app_client_id=req.app_client_id, service_id=req.service_id):
            return resp(HTTPStatus.CONFLICT, message="Permission already exists")

        app_model = self.load_repository(AppClientModel).db.get_by_id(id=req.app_client_id)
        service_model = self.load_repository(ServiceModel).db.get_by_id(id=req.service_id)

        if not app_model or not service_model:
            return resp(HTTPStatus.NOT_FOUND, message="App client or Service not found") 

        permission_data = req.to_dict()
        permission_data["app_client_name"] = app_model.name
        permission_data["service_name"] = service_model.name
        permission_data["created_by"] = req.current_profile.profile_id

        permission_model = permission_repo.db.add(permission_data)
        
        if not permission_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Permission")
        
        app_client_permission_vo: AppClientPermissions = permission_model.to_vo()
        app_client_permission_vo.upsert_in_redis(permission_repo.redis, service_name=service_model.name, client_name=app_model.name)

        return resp(HTTPStatus.CREATED, permission_model.to_dict(), "Created Succefully")
    
    @BaseController.route(
        path="/<path:permission_id>",
        methods=["GET"],
        request=GetPermissionAuth,
        response=PermissionGetResponse)
    def get_permission(self, req: GetPermissionAuth, resp: PermissionGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        permission_model = self.load_repository(PermissionModel).db.get_by_id(id=req.permission_id)
        if not permission_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Not Found")

        return resp(HTTPStatus.OK, permission_model.to_dict(lazy_load=["app_client", "service"]), "Request Succefully")

    @BaseController.route(
        path="/<path:permission_id>",
        methods=["PUT", "PATCH"],
        request=UpdatePermissionAuth,
        response=PermissionUpdatedResponse)
    def update_permission(self, req: UpdatePermissionAuth, resp: PermissionUpdatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        permission_repo = self.load_repository(PermissionModel)

        if not permission_repo.db.contains(permission_id=req.permission_id):
            return resp(HTTPStatus.NOT_FOUND, message="Permission not found")

        permission_data = req.to_dict()
        permission_data["updated_by"] = req.current_profile.profile_id
        
        permission_id = permission_data.pop("permission_id")
        permission_model = permission_repo.db.update(permission_data, id=permission_id)

        if not permission_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating App client")

        app_client_permission_vo: AppClientPermissions = permission_model[0].to_vo()
        app_client_permission_vo.upsert_in_redis(permission_repo.redis, permission_model[0].service_name)

        return resp(HTTPStatus.OK, permission_model.to_dict(), "Updated Succefully")
    
    @BaseController.route(
        path="/<path:permission_id>",
        methods=["DELETE"],
        request=DeletePermissionAuth,
        response=PermissionDeletedResponse)
    def delete_permission(self, req: DeletePermissionAuth, resp: PermissionDeletedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        permission_repo = self.load_repository(PermissionModel)
        permission_model = permission_repo.db.get_by_id(req.permission_id)
        
        if not permission_model:
            return resp(HTTPStatus.NOT_FOUND, {}, "Permission not found")

        permission_repo.db.remove_by_id(req.permission_id)
        AppClientPermissions.remove_in_redis(permission_repo.redis, permission_model.app_client_name, permission_model.service_name)
        
        return resp(HTTPStatus.OK, permission_model, "Deleted successfully")
