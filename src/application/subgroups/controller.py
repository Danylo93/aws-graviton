from http import HTTPStatus
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from arcs_lib_pca.use_case import execute_use_case
from arcs_lib_pca.application import BaseController

from src.infrastructure.models import (
    SubGroupModel,
    GroupModel,
    AccessProfileModel,
    ConfigModel,
    ProfileModel,
    ServiceSubgroupsPermissionsModel,
    UserGuestModel
)

from src.use_case.subgroup import LoadSubGroupUseCase
from arcs_lib_pca.domain.value_objects import ProfilePermissions, SubGroupPermissions

from .requests import (
    CreateSubGroupRequestAuth,
    SubGroupIdGetRequestAuth,
    UpdateSubGroupRequestAuth,
    DeleteSubGroupIdRequestAuth,
    SubGroupGetRequestAuth
)

from .responses import (
    SubGroupAllGetResponse,
    SubGroupGetResponse,
    SubGroupCreatedResponse,
    SubGroupUpdatedResponse,
    SubGroupDeletedResponse
)

class SubGroupController(BaseController):
    @BaseController.route(
        path="/",
        methods=["GET"],
        request=SubGroupGetRequestAuth,
        response=SubGroupAllGetResponse)
    def get_all_subgroups(self, req: SubGroupGetRequestAuth, resp: SubGroupAllGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")


        subgroup_repo = self.load_repository(SubGroupModel)
        subquery_params = QueryParamsUseCase.load(req.params)
        
        if req.group_name:
            group_model = self.load_repository(GroupModel).db.get_by(name=req.group_name)

            if group_model:
                subgroups = (
                    subgroup_repo.db
                        .with_query(subquery_params)
                        .paginate(
                            req.page,
                            req.per_page,
                            group_id=group_model.id,
                            load=["group", "services", "permissions"]
                        )
                )
                return resp(HTTPStatus.OK, subgroups, "Successfully")                

        subgroups = subgroup_repo.db.with_query(subquery_params).paginate(req.page, req.per_page, load=["group", "services", "permissions"])

        return resp(HTTPStatus.OK, subgroups, "Successfully")

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateSubGroupRequestAuth,
        response=SubGroupCreatedResponse)
    def create_subgroup(self, req: CreateSubGroupRequestAuth, resp: SubGroupCreatedResponse):
        
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        if not (group_model := self.load_repository(GroupModel).db.get_by_id(req.group_id, load=['app_client_groups_permissions'])):
            return resp(HTTPStatus.NOT_FOUND, message=f"Group ID: {req.group_id} not found")
        
        subgroup_model = execute_use_case(LoadSubGroupUseCase,
                                            group_model=group_model,
                                            subgroup_name=req.name,
                                            is_mandatory=req.is_mandatory,
                                            subgroup_description=req.description,
                                            subgroup_permissions=req.subgroup_permissions
                                        )

        return resp(HTTPStatus.CREATED, subgroup_model.to_dict(), "Created Succefully")

    @BaseController.route(
        path="/<subgroup_id_or_name>",
        methods=["GET"],
        request=SubGroupIdGetRequestAuth,
        response=SubGroupGetResponse)
    def get_subgroup(self, req: SubGroupIdGetRequestAuth, resp: SubGroupGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        subgroup_rep = self.load_repository(SubGroupModel)
        subgroup = None

        if req.has_id:
            subgroup = subgroup_rep.db.get_by_id(req.subgroup_id_or_name, load=["group", "services", "permissions"])
        else:
            subgroup = subgroup_rep.db.get_by(name=req.subgroup_id_or_name, load=["group", "services", "permissions"])

        if not subgroup:
            return resp(HTTPStatus.NOT_FOUND, message=f"SubGroup {req.subgroup_id_or_name} not found")

        return resp(HTTPStatus.OK, subgroup.to_dict(lazy_load=["group", "permissions", "services"]), "Successfully")

    @BaseController.route(
        path="/<subgroup_id>",
        methods=["PUT", "PATCH"],
        request=UpdateSubGroupRequestAuth,
        response=SubGroupUpdatedResponse
    )
    def update_subgroup(self, req: UpdateSubGroupRequestAuth, resp:SubGroupUpdatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        subgroup_model = self.load_repository(SubGroupModel).db.get_by_id(req.subgroup_id)
        
        if not subgroup_model:
            return resp(HTTPStatus.NOT_FOUND, message=f"SubGroup ID: {req.subgroup_id} not found")
        
        if subgroup_model.is_mandatory and subgroup_model.name != req.name:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message=f'In subgroup {subgroup_model.name} yout name cannot be updated')

        
        subgroup_model = execute_use_case(LoadSubGroupUseCase,
                                            group_model=subgroup_model.group,
                                            subgroup_id=subgroup_model.id,
                                            subgroup_name=req.name,
                                            is_mandatory=req.is_mandatory,
                                            subgroup_description=req.description,
                                            subgroup_permissions=req.subgroup_permissions
                                        )

        return resp(HTTPStatus.OK, subgroup_model.to_dict(), "Updated Succefully")

    @BaseController.route(
        path="/<subgroup_id>",
        methods=["DELETE"],
        request=DeleteSubGroupIdRequestAuth,
        response=SubGroupDeletedResponse
    )
    def delete_subgroup(self, req: DeleteSubGroupIdRequestAuth, resp:SubGroupDeletedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        subgroup_model : SubGroupModel = self.load_repository(SubGroupModel).db.get_by_id(req.subgroup_id, load=['services'])

        if not subgroup_model:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="SubGroup not found")

        if subgroup_model.is_mandatory:
            return resp(status_code=HTTPStatus.BAD_REQUEST, message=f'SubGroup {subgroup_model.name} cannot be deleted')

        self.load_repository(AccessProfileModel).db.delete(subgroup_id=req.subgroup_id)
        self.load_repository(ServiceSubgroupsPermissionsModel).db.remove(subgroup_id=req.subgroup_id)

        profiles = self.load_repository(ProfileModel).db.find(subgroup_id=req.subgroup_id)

        for profile in profiles:
            self.load_repository(ConfigModel).db.remove(profile_id=profile.id)
            self.load_repository(UserGuestModel).db.remove(profile_id=profile.id)

            for service in subgroup_model.services:
                ProfilePermissions.remove_in_redis(self.load_repository(ProfileModel).redis, profile.id, service.name)
        
        self.load_repository(ProfileModel).db.remove(subgroup_id=req.subgroup_id)
        
        self.load_repository(SubGroupModel).db.remove_by_id(req.subgroup_id)
        for service in subgroup_model.services:
            SubGroupPermissions.remove_of_redis(self.load_repository(SubGroupModel).redis, req.subgroup_id, service.name)
        
        return resp(status_code=HTTPStatus.OK, message="SubGroup deleted successfully")