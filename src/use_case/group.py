import typing as t

from arcs_lib_pca.use_case import UseCase
from arcs_lib_pca.domain.value_objects import File, GenericUUID, AppClientPermissions, ArcsAppClients
from arcs_lib_pca.infrastructure.repository import Repositories
from arcs_lib_pca.utils.string import to_snake_case

from src.infrastructure.models import GroupModel
from src.domain.value_objects import BasePermission
from src.infrastructure.models.app_client_groups_permissions_model import AppClientGroupsPermissionsModel
from src.infrastructure.models.app_client_model import AppClientModel
from src.utils.permissions import merge_base_permissions_list

class LoadGroupUseCase(UseCase[t.Optional[GroupModel]]):

    def execute(self, 
                group_id: t.Optional[GenericUUID] = None,
                group_name: t.Optional[str] = None,
                group_description: t.Optional[str] = None,
                group_image: t.Optional[File] = None,
                group_app_clients: t.Optional[t.List[BasePermission]] = None,
                group_meta_data: t.Optional[t.Dict] = None,
                is_mandatory: t.Optional[bool] = False,
                **kwargs 
            ) -> t.Optional[GroupModel]:
        
        group_repo = Repositories(GroupModel())
        group_model : GroupModel = None

        app_client_groups_permissions_repo = Repositories(AppClientGroupsPermissionsModel())
        
        if group_app_clients:
            for app_client_permission in group_app_clients:
                if not ArcsAppClients.contains_in_redis(group_repo.redis, app_client_permission.name):
                    raise ValueError(f"Group {group_model.name}: cannot bind to app_client {app_client_permission.name} as it is not defined")


        if not group_id and not group_name:
            raise ValueError("Requires id or name to define a group")
        
        if group_id:
            group_model = group_repo.db.get_by_id(group_id, load=["subgroups"])

        ## Renomear um grupo
        if group_model and group_name and group_model.name != group_name:
            group_model.name = group_name
        
        ## Obtém ou inicializa um novo grupo através do nome
        if not group_model and group_name:
            if not (group_model := group_repo.db.get_by(name=group_name, load=["subgroups"])):
                group_model = group_repo.model
                group_model.name = group_name

        ## upsert descrição do grupo
        if group_description:
            group_model.description = group_description
        
        ## upsert a imagem do grupo
        if group_image:
            file_model : File = group_repo.storage.add(group_image)
            group_model.image_id = file_model.id

        group_model.is_mandatory = is_mandatory
        
        if group_meta_data:
            group_model.meta_data = {**group_model.meta_data, **group_meta_data}

        if group_model.id:
            if not (group_model := group_repo.db.update_by_id(group_model.id, group_model)):
                raise RuntimeError("Error when updating the database")

        if not group_model.id and not (group_model := group_repo.db.upsert(group_model, name=group_model.name)):
                raise RuntimeError("Error when upsert the database")
        
        if group_app_clients:
            app_client_groups_permissions_models = app_client_groups_permissions_repo.db.find(group_id=group_model.id, load=['app_client'])


            if app_client_groups_permissions_models:
                base_permissions : list[BasePermission] = [app_client_group_permission.to_vo() for app_client_group_permission in app_client_groups_permissions_models]    

                permissions = merge_base_permissions_list(base_permissions, group_app_clients)

                for permission in permissions:
                    app_client_groups_permissions_repo = Repositories(AppClientGroupsPermissionsModel())
                    app_client_model = Repositories(AppClientModel).db.get_by(name=permission.name)
                    app_client_groups_permissions_repo.db.upsert(group_model, group_id=group_model.id, app_client_id=app_client_model.id)

                group_permissions = group_model.to_vo(permissions)
                group_permissions.upsert_in_redis(group_repo.redis)

        return group_model
            
        