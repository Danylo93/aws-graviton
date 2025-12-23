import typing as t
from http import HTTPStatus

from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.application import BaseController
from arcs_lib_pca.domain.value_objects import ArcsAppClients, GroupPermissions, ProfilePermissions, SubGroupPermissions

from src.infrastructure.models import (
    GroupModel,
    AppClientGroupsPermissionsModel,
    AccessProfileModel,
    ConfigModel,
    AppClientModel,
    ProfileModel,
    ServiceSubgroupsPermissionsModel,
    SubGroupModel,
    UserGuestModel,
)


from .requests import (
    CreateGroupRequestAuth,
    GroupIdOrNameGetRequestAuth,
    UpdateGroupRequestAuth,
    DeleteGroupIdRequestAuth,
    GroupGetRequestAuth,
    GetServicesByGroupIdOrNameRequestAuth
)

from .responses import (
    GroupAllGetResponse,
    GroupGetResponse,
    GroupCreatedResponse,
    GroupUpdatedResponse,
    GroupDeletedResponse,
    GetServicesByGroupIdResponse
)

class GroupController(BaseController):
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GroupGetRequestAuth,
        response=GroupAllGetResponse)
    def get_all_groups(self, req: GroupGetRequestAuth, resp: GroupAllGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        group_repo = self.load_repository(GroupModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        groups = group_repo.db.with_query(subquery_params).paginate(req.page, req.per_page, load=["subgroups", "app_clients", "app_client_groups_permissions", "image"])

        return resp(HTTPStatus.OK, groups, "Successfully")

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateGroupRequestAuth,
        response=GroupCreatedResponse)
    def create_group(self, req: CreateGroupRequestAuth, resp: GroupCreatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        group_repo = self.load_repository(GroupModel)
        gp_repo = self.load_repository(AppClientGroupsPermissionsModel)

        if group_repo.db.contains(name=req.name):
            return resp(HTTPStatus.BAD_REQUEST, message=f"Group {req.name} already exists")

        for app_client in req.app_clients:
            if not ArcsAppClients.contains_in_redis(group_repo.redis, app_client.name):
                return resp(HTTPStatus.NOT_FOUND, message=f"Client App: {app_client.name} not found")

        group_model : GroupModel = group_repo.model

        if req.image:
            image_vo = group_repo.storage.add(req.image)
            group_model.image_id = image_vo.id

        group_model.name = req.name
        group_model.description = req.description
        group_model.meta_data = req.meta_data
        group_model.is_mandatory = req.is_mandatory

        group_model = group_repo.db.add(group_model)

        if not group_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating group client")

        for app_client in req.app_clients:
            gp_repo = self.load_repository(AppClientGroupsPermissionsModel)
            app = ArcsAppClients.get_of_redis(group_repo.redis, app_client.name)
            gp_model = gp_repo.model

            gp_model.group_id = group_model.id
            gp_model.app_client_id = app.id
            gp_model.get = app_client.get
            gp_model.post = app_client.post 
            gp_model.put = app_client.put
            gp_model.delete = app_client.delete

            gp_model = gp_repo.db.add(gp_model)
            if not gp_model:
                return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating group permissions client")

        permissions = self.load_repository(AppClientGroupsPermissionsModel).db.find(group_id=group_model.id, load=['app_client'])

        group_permission = group_model.to_vo(permissions)
        
        if not group_permission.upsert_in_redis(group_repo.redis):
            group_repo.db.remove_by_id(group_model.id)
            gp_repo.db.remove(group_id=group_model.id)
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error internal create Group")

        return resp(HTTPStatus.CREATED, group_model, "Created Successfully")

    @BaseController.route(
        path="/<group_id_or_name>",
        methods=["GET"],
        request=GroupIdOrNameGetRequestAuth,
        response=GroupGetResponse)
    def get_group(self, req: GroupIdOrNameGetRequestAuth, resp: GroupGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        g_model : GroupModel = None

        if req.has_id:
            g_model = self.load_repository(GroupModel).db.get_by_id(req.group_id_or_name)
        else:
            g_model = self.load_repository(GroupModel).db.get_by(name=req.group_id_or_name)

        if not g_model:
            return resp(HTTPStatus.NOT_FOUND, message="Group not found")

        return resp(HTTPStatus.OK, g_model.to_dict(lazy_load=["subgroups", "app_clients", "app_client_groups_permissions", "image"]), message="Successfully")

    @BaseController.route(
        path="/<group_id>",
        methods=["PUT", "PATCH"],
        request=UpdateGroupRequestAuth,
        response=GroupUpdatedResponse
    )
    def update_group(self, req: UpdateGroupRequestAuth, resp:GroupUpdatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        group_model : GroupModel = self.load_repository(GroupModel).db.get_by_id(req.group_id)

        if not (group_model):
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Group not found")
        
        if group_model.is_mandatory and group_model.name != req.name:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message=f'In group {group_model.name} your name cannot be updated')

        for app_client in req.app_clients:
            if not ArcsAppClients.contains_in_redis(self.get_redis(), app_client.name):
                return resp(HTTPStatus.NOT_FOUND, message=f"Client App: {app_client.name} not found")

        old_image_id = group_model.image_id
        new_image_id = None

        if req.image:
            image_vo = self.load_repository(GroupModel).storage.add(req.image)
            new_image_id = image_vo.id

        group_data = {
            "name": req.name if req.name else group_model.name,
            "description": req.description if req.description else group_model.description,
            "meta_data": req.meta_data if req.meta_data else group_model.meta_data,
            "is_mandatory": req.is_mandatory if req.is_mandatory is not None else group_model.is_mandatory
        }

        if new_image_id:
            group_data["image_id"] = new_image_id

        group_model = self.load_repository(GroupModel).db.update_by_id(id=req.group_id, data=group_data)

        if not group_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating group client")

        for app_client in req.app_clients:
            app = self.load_repository(AppClientModel).db.get_by(name=app_client.name)

            if not app:
                continue

            data = {
                "group_id" : req.group_id,
                "app_client_id" : app.id,
                "get" : app_client.get or False,
                "post" : app_client.post or False,
                "put" : app_client.put or False,
                "delete" : app_client.delete or False
            }

            permission_model = self.load_repository(AppClientGroupsPermissionsModel).db.get_by(group_id=req.group_id, app_client_id=app.id)

            if not permission_model:
                perm = self.load_repository(AppClientGroupsPermissionsModel).db.add(data)
                if not perm:
                    return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating group permissions client")
            else:
                perm = self.load_repository(AppClientGroupsPermissionsModel).db.update(group_id=req.group_id, app_client_id=app.id, data=data)
                if not perm:
                    return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating group permissions client")
                

        permissions = self.load_repository(AppClientGroupsPermissionsModel).db.find(group_id=group_model.id, load=['app_client'])

        group_permission : GroupPermissions = group_model.to_vo(permissions)

        if not group_permission.upsert_in_redis(self.get_redis()):
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error internal create Group")

        app_clients : t.List[AppClientModel] = self.load_repository(AppClientModel).db.find()

        for app_client in app_clients:
            if not req.has_app_client(app_client.name):
                self.load_repository(AppClientGroupsPermissionsModel).db.remove(group_id=req.group_id, app_client_id=app_client.id)

        if new_image_id and old_image_id != new_image_id:
            self.load_repository(GroupModel).storage.remove_by_id(old_image_id)

        return resp(HTTPStatus.OK, group_model, "Updated Succesfully")

    @BaseController.route(
        path="/<group_id>",
        methods=["DELETE"],
        request=DeleteGroupIdRequestAuth,
        response=GroupDeletedResponse
    )
    def delete_group(self, req: DeleteGroupIdRequestAuth, resp:GroupDeletedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        group_repo = self.load_repository(GroupModel)
        
        group_model : GroupModel = group_repo.db.get_by_id(req.group_id, load=['subgroups'])

        if not group_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Group not found")
        
        if group_model.is_mandatory:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message=f'Group {group_model.name} cannot be deleted')

        self.load_repository(AccessProfileModel).db.delete(group_id=req.group_id)
        self.load_repository(AppClientGroupsPermissionsModel).db.remove(group_id=req.group_id)
        
        subgroup_models : t.List[SubGroupModel] = self.load_repository(SubGroupModel).db.find(group_id=req.group_id, load=['services'])

        for subgroup in subgroup_models:
            profiles = self.load_repository(ProfileModel).db.find(subgroup_id=subgroup.id)

            for profile in profiles:
                self.load_repository(ConfigModel).db.remove(profile_id=profile.id)
                self.load_repository(UserGuestModel).db.remove(profile_id=profile.id)    
            
                for service in subgroup.services:
                    ProfilePermissions.remove_in_redis(self.load_repository(ProfileModel).redis, profile.id, service.name)

            self.load_repository(ProfileModel).db.remove(subgroup_id=subgroup.id)
            self.load_repository(ServiceSubgroupsPermissionsModel).db.remove(subgroup_id=subgroup.id)
            self.load_repository(SubGroupModel).db.remove_by_id(subgroup.id)
            for service in subgroup.services:
                SubGroupPermissions.remove_of_redis(self.load_repository(SubGroupModel).redis, subgroup.id, service.name)

        self.load_repository(GroupModel).db.remove_by_id(id=req.group_id)
        
        GroupPermissions.remove_in_redis(group_repo.redis, req.group_id)
        
        return resp(status_code=HTTPStatus.OK, message="Group deleted successfully")
    
    @BaseController.route(
        path="/<group_id_or_name>/services/",
        methods=["GET"],
        request=GetServicesByGroupIdOrNameRequestAuth,
        response=GetServicesByGroupIdResponse
    )
    def get_services_by_group(self, req: GetServicesByGroupIdOrNameRequestAuth, resp:GetServicesByGroupIdResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        g_model : GroupModel = None

        if req.has_id:
            g_model = self.load_repository(GroupModel).db.get_by_id(req.group_id_or_name)
        else:
            g_model = self.load_repository(GroupModel).db.get_by(name=req.group_id_or_name)

        if not g_model:
            return resp(HTTPStatus.NOT_FOUND, message="Group not found")

        app_clients: t.List[AppClientModel] = g_model.app_clients
        service_models = set()
        
        for app_client in app_clients:
            for service in app_client.services:
                service_models.add(service)

        return resp(HTTPStatus.OK, list(service_models), "Group deleted successfully")