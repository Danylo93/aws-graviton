from http import HTTPStatus
import typing as t

from arcs_lib_pca.application import BaseController
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.domain.value_objects import ArcsAppClients

from src.infrastructure.models import AppClientModel, ConfigModel, PermissionModel, ServiceModel
from .requests import (
    GetAppClientAuth,
    GetAllAppClientAuth,
    CreateAppClientAuth,
    UpdateAppClientAuth,
    DeleteAppClientAuth,
    GetConfigAuth,
    UpsertConfigAuth, GetAppClientEnvsAuth
)
from .responses import (
    AppClientAllGetResponse,
    AppClientCreatedResponse,
    AppClientGetResponse,
    AppClientUpdatedResponse,
    AppClientDeletedResponse,
    ConfigResponse, AppClientGetEnvsResponse
)

class AppClientsController(BaseController):
    
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllAppClientAuth,
        response=AppClientAllGetResponse)
    def get_all_app_client(self, req: GetAllAppClientAuth, resp: AppClientAllGetResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")
        
        app_repo = self.load_repository(AppClientModel)
        subquery = QueryParamsUseCase.load(req.params)
        data = app_repo.db.with_query(subquery).paginate(page=req.page, per_page=req.per_page, load=["image", "services", "permissions", "app_client_groups_permissions"])

        return resp(HTTPStatus.OK, data, "Request Succefully")

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateAppClientAuth,
        response=AppClientCreatedResponse)
    def create_app_client(self, req: CreateAppClientAuth, resp: AppClientCreatedResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")
        
        app_repo = self.load_repository(AppClientModel)
        if app_repo.db.contains(name=req.name):
            return resp(status_code=HTTPStatus.CONFLICT, message=f"{req.name}: Resource already exists")

        app_client_data = req.to_dict()

        image = app_client_data.pop("image", None)
        if image:
            image = app_repo.storage.add(image)
            app_client_data["image_id"] = image.id

        app_model = app_repo.db.add(app_client_data)
        if not app_model:
            if image:
                app_repo.storage.remove(image.filename)
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating App client")

        arcs_app_client: ArcsAppClients = app_model.to_vo()
        if not arcs_app_client.upsert_in_redis(app_repo.redis):
            if req.image:
                app_repo.storage.remove_by_id(app_client_data["image_id"])
            app_repo.db.remove_by_id(app_model.id)
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error add App client in Redis")
            
        return resp(HTTPStatus.CREATED, app_model.to_dict(lazy_load=["image", "services", "permissions", "app_client_groups_permissions"]), "Created Succefully")
    
    @BaseController.route(
        path="/<path:client_name>",
        methods=["GET"],
        request=GetAppClientAuth,
        response=AppClientGetResponse)
    def get_app_client(self, req: GetAppClientAuth, resp: AppClientGetResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")

        app_repo = self.load_repository(AppClientModel)
        app_model = app_repo.db.get_by(name=req.client_name)
        
        if not app_model:
            return resp(HTTPStatus.NOT_FOUND, {}, f"App client: {req.client_name} not found")
        
        return resp(HTTPStatus.OK, app_model.to_dict(lazy_load=["image", "permissions", "app_client_groups_permissions"]), "Request Succefully")

    @BaseController.route(
        path="/<path:client_name>/envs/",
        methods=["GET"],
        request=GetAppClientAuth,
        response=AppClientGetResponse)
    def get_app_client_envs(self, req: GetAppClientEnvsAuth, resp: AppClientGetEnvsResponse):

        if req.has_errors():
            return resp(status_code=400, message="Invalid request")

        envs = {
            "prod": {
                "APP_CLIENT": "arcs-pilot-mobile",
                "APIM_BASE_URL": "https://arcs-apim-hml.azure-api.net",
                "APIM_SUBSCRIPTION_KEY": "4340e555f57949e28bb8b209f074f759",
                "CDN_BASE_URL": "https://cdn-files-porschecup-ahgchkdnh9ehcba8.z02.azurefd.net",
                "AZURE_CLIENT_ID": "4bd1d8b0-6da1-4ae8-9b66-c32a9e07a7cf",
                "AZURE_TENANT_ID": "ae4e6f79-dec3-4e70-98c6-b7a76242029f",
                "AZURE_CLIENT_SECRET": "TjM8Q~qB~X63MMmY.irhS3pOZHdHHu2xwSJYQbxC",
                "AZURE_KEY_VAULT_BASE_URL": "https://arcs-kv-hml.vault.azure.net/"
            },
            "hml": None,
            "dev": None
        }

        return resp(HTTPStatus.OK, envs, "Request Succefully")
    
    @BaseController.route(
        path="/<path:client_name>",
        methods=["PUT", "PATCH"],
        request=UpdateAppClientAuth,
        response=AppClientUpdatedResponse)
    def update_app_client(self, req: UpdateAppClientAuth, resp: AppClientUpdatedResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")

        app_repo = self.load_repository(AppClientModel)
        app_model = app_repo.db.get_by(name=req.client_name)

        if not app_model:
            return resp(HTTPStatus.NOT_FOUND, {}, "App client not found")

        app_data = {
            "id": app_model.id,
            "name": req.name if req.name else app_model.name,
            "name_friendly": req.name_friendly if req.name_friendly else app_model.name_friendly,
            "description": req.description if req.description else app_model.description
        }

        image_model = None
        if req.image:
            image_model = app_repo.storage.update(req.image)
            app_data["image_id"] = image_model.id

        app_model = app_repo.db.update_by_id(app_model.id, app_data)

        if not app_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating App client")

        arcs_app_client = app_model.to_vo()

        if not arcs_app_client.upsert_in_redis(app_repo.redis):
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, {}, "Application client not updated")

        return resp(HTTPStatus.OK, app_model.to_dict(), "Updated Succefully")
    
    @BaseController.route(
        path="/<path:client_name>",
        methods=["DELETE"],
        request=DeleteAppClientAuth,
        response=AppClientDeletedResponse)
    def delete_app_client(self, req: DeleteAppClientAuth, resp: AppClientDeletedResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")

        app_repo = self.load_repository(AppClientModel)
        app_model = app_repo.db.get_by(name=req.client_name)
        
        if not app_model:
            return resp(HTTPStatus.NOT_FOUND, {}, "App client not found")

        app_repo.db.remove(name=req.client_name)

        if app_model.image_id:
            app_repo.storage.remove_by_id(app_model.image_id)

        ArcsAppClients.remove_in_redis(app_repo.redis, req.client_name)
        
        self.load_repository(PermissionModel).db.remove(app_client_id=app_model.id)

        return resp(HTTPStatus.OK, app_model, "Deleted successfully")
    
    @BaseController.route(
        path="/<path:client_name>/profile_config",
        methods=["GET"],
        request=GetConfigAuth,
        response=ConfigResponse)
    def get_config_of_profile(self, req: GetConfigAuth, resp: ConfigResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")
        
        profile_id = req.profile_id if req.profile_id else req.current_profile.profile_id

        config_repo = self.load_repository(ConfigModel)
        config_model = config_repo.db.get_by(profile_id=profile_id, client_name=req.client_name)

        return resp(HTTPStatus.OK, config_model.to_dict(lazy_load=["profile"]), "Request Succefully")

    @BaseController.route(
        path="/<path:client_name>/profile_config",
        methods=["PUT", "PATCH", "POST"],
        request=UpsertConfigAuth,
        response=ConfigResponse)
    def upsert_config_of_profile(self, req: UpsertConfigAuth, resp: ConfigResponse):
        if req.has_errors():
            return resp(status_code=400, message="Invalid request")

        app_repo = self.load_repository(AppClientModel)
        app_model = app_repo.db.get_by(name=req.client_name)

        if not app_model:
            return resp(HTTPStatus.NOT_FOUND, message="App client not found")

        profile_id = req.profile_id if req.profile_id else req.current_profile.profile_id
        config_data = req.to_dict()
        config_data["profile_id"] = profile_id

        contract_repo = self.load_repository(ConfigModel)
        data = contract_repo.db.upsert(config_data, profile_id=profile_id, client_name=req.client_name)

        return resp(HTTPStatus.OK, data, "Request Succefully")