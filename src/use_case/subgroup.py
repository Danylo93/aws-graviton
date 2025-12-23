import typing as t

from arcs_lib_pca.use_case import UseCase, execute_use_case
from arcs_lib_pca.domain.value_objects import GenericUUID, AppClientPermissions, ArcsServices
from arcs_lib_pca.infrastructure.repository import Repositories
from arcs_lib_pca.infrastructure.repository.redis_repository import RedisRepository
from arcs_lib_pca.utils.json import data_decode

from src.infrastructure.models import SubGroupModel, GroupModel, AppClientGroupsPermissionsModel
from src.domain.value_objects import SubGroupPermission
from src.infrastructure.models.profile_model import ProfileModel
from src.infrastructure.models.service_model import ServiceModel
from src.infrastructure.models.service_subgroups_permissions_model import ServiceSubgroupsPermissionsModel
from src.use_case.permissions import LoadProfilePermissionsUseCase, ProfilePermissionStructure
from src.utils.permissions import merge_subgroup_permissions

class LoadSubGroupUseCase(UseCase[t.Optional[SubGroupModel]]):
    
    def execute(self,
                group_model: GroupModel,
                subgroup_id: t.Optional[GenericUUID] = None,
                subgroup_name: t.Optional[str] = None,
                is_mandatory: t.Optional[bool] = False,
                subgroup_description: t.Optional[str] = None,
                subgroup_permissions: t.Optional[t.List[SubGroupPermission]] = None,
                **kwargs
            ) -> t.Optional[SubGroupModel]:
        
        if not subgroup_id and not subgroup_name:
            raise ValueError("Requires id or name to define a subgroup")

        subgroup_repo = Repositories(SubGroupModel())
        init_model = subgroup_model = self._get_or_create_subgroup(subgroup_repo, group_model, subgroup_id, subgroup_name, is_mandatory)

        is_new_subgroup = init_model.id is None 

        # Renomeia subgrupo, se fornecido um novo nome
        if subgroup_name and subgroup_model.name != subgroup_name:
            subgroup_model.name = subgroup_name

        # Define ou atualiza a descrição do subgrupo, se fornecida
        if subgroup_description:
            subgroup_model.description = subgroup_description

        # Atualiza permissões do subgrupo, garantindo que as permissões sempre estejam atualizadas
        permissions = self._update_permissions(subgroup_repo, group_model, subgroup_model, subgroup_permissions)

        subgroup_model.group_id = group_model.id

        # Caso não ocorra alterações retorna o subgroup_model
        if not (init_model.id and init_model == subgroup_model):
            subgroup_model = self._save_subgroup(subgroup_repo, subgroup_model)

        service_subgroups_permissions_models: t.List[ServiceSubgroupsPermissionsModel] = []
        
        for permission in permissions:

            service = permission["service"]

            service_model = Repositories(ServiceModel()).db.get_by(name=service['name'])

            if not service_model:
                raise RuntimeError('Service not found')

            permission_data = {
                "service_id": service_model.id,
                "subgroup_id": subgroup_model.id,
                "get": service['get'],
                "post": service['post'],
                "put": service['put'],
                "delete": service['delete'],
                "controllers": permission['controllers'],
            }

            ss_perm = Repositories(ServiceSubgroupsPermissionsModel()).db.upsert(data=permission_data, subgroup_id=subgroup_model.id, service_id=service_model.id)

            if type(ss_perm) == list:
                ss_perm = ss_perm[0]
            
            if ss_perm:
                ss_perm = Repositories(ServiceSubgroupsPermissionsModel()).db.get_by(service_id=ss_perm.service_id, subgroup_id=ss_perm.subgroup_id, load=['service'])
                service_subgroups_permissions_models.append(ss_perm)
        
        ss_perm_vos = subgroup_model.to_vo(service_subgroups_permissions_models)
        for ss_perm_vo in ss_perm_vos:
            ss_perm_vo.upsert_in_redis(subgroup_repo.redis)

        Repositories(SubGroupModel()).db.update_by_id(id=subgroup_model.id, data=subgroup_model)

        
        if is_new_subgroup:
            self._update_profile_permissions(subgroup_model)

        return subgroup_model
    
    def _update_profile_permissions_on_redis_and_convert_to_dict(
            self, 
            permission_structure: ProfilePermissionStructure, 
            redis: RedisRepository 
        ) -> t.List[dict]:
        
        permissions = []
        
        for perm in permission_structure.profile_permissions:
            service_name = perm.service.name
            if perm.upsert_in_redis(redis, service_name): 
                permissions.append(data_decode(perm.to_dict()))

        return permissions

    def _update_profile_permissions(self, subgroup_model: SubGroupModel):
        profile_models = Repositories(ProfileModel()).db.find(subgroup_id=subgroup_model.id)
        
        for profile in profile_models:
            permission_structure = execute_use_case(
                LoadProfilePermissionsUseCase,
                profile_model=profile,
                subgroup_id=subgroup_model.id
                )
            
            if permission_structure and permission_structure.profile_permissions:
                profile.permissions = self._update_profile_permissions_on_redis_and_convert_to_dict(permission_structure, Repositories(SubGroupModel()).redis)

            Repositories(ProfileModel()).db.update_by_id(id=profile.id, data=profile)
            


    def _get_or_create_subgroup(self, repo: Repositories[SubGroupModel], group_model: GroupModel, subgroup_id: t.Optional[GenericUUID], name: t.Optional[str], is_mandatory: t.Optional[bool] = False) -> SubGroupModel:
        """Obtém ou cria um subgrupo a partir do ID ou nome."""
        if subgroup_id:
            if subgroup_model := repo.db.get_by_id(subgroup_id, load=["group"]):
                return subgroup_model
            raise ValueError(f"Subgroup with id {subgroup_id} not found.")

        if name:
            if subgroup_model := repo.db.get_by(name=name, group_id=group_model.id, load=["group"]):
                return subgroup_model

            new_subgroup = repo.model
            new_subgroup.name = name
            new_subgroup.group_id = group_model.id
            new_subgroup.is_mandatory = is_mandatory
            return new_subgroup
        
        raise ValueError("A valid subgroup_id or name must be provided.")

    def _update_permissions(
            self,
            repo: Repositories[SubGroupModel],
            group_model: GroupModel,
            subgroup_model: SubGroupModel,
            subgroup_permissions: t.Optional[t.List[SubGroupPermission]]
        ) -> t.List[t.Dict[str, t.Any]]:
        """Atualiza as permissões do subgrupo, garantindo integridade com permissões de app clients."""
        subgroup_model = Repositories(SubGroupModel()).db.get_by_id(subgroup_model.id, load=['permissions'])
                
        if subgroup_model:
            permissions = Repositories(ServiceSubgroupsPermissionsModel()).db.find(subgroup_id=subgroup_model.id, load=['service'])

            merged_permissions = merge_subgroup_permissions(subgroup_model.to_vo(permissions), subgroup_permissions)
        else:
            merged_permissions = merge_subgroup_permissions([], subgroup_permissions)    

        updated_permissions = []
        app_client_group_permissions_repo = Repositories(AppClientGroupsPermissionsModel())

        app_client_group_permissions = app_client_group_permissions_repo.db.find(group_id=group_model.id, load=['app_client'])

        if not app_client_group_permissions:
            raise RuntimeError('Error to load AppClientGroupPermissions')

        app_clients = [
            app_client_group_permission.app_client for app_client_group_permission in app_client_group_permissions
        ]

        for app_client in app_clients:
            # Obter permissões do app client
            ac_permissions = AppClientPermissions.list_by_client_in_redis(repo.redis, app_client.name)
            ac_permission_dict = {ac_perm.service_name: ac_perm for ac_perm in ac_permissions or []}

            for service_name, sub_perm in list(merged_permissions.items()):
                # Verifica se o serviço está presente nas permissões do app client
                if service_name not in ac_permission_dict:
                    # Remove o serviço se não estiver autorizado
                    merged_permissions.pop(service_name)
                    continue

                # Atualiza os controllers de acordo com as permissões no Redis
                arcs_services = ArcsServices.get_of_redis(repo.redis, service_name)

                if not arcs_services:
                    raise RuntimeError(f"Service {service_name} not found")

                ctrl_permission_dict = {ctrl.name: ctrl for ctrl in sub_perm.controllers}

                valid_controllers = [
                    ctrl
                    for ctrl_name, ctrl in ctrl_permission_dict.items()
                    if ctrl_name in arcs_services.namespaces
                ]

                sub_perm.controllers = valid_controllers

                updated_permissions.append(sub_perm.model_dump())

        result = updated_permissions
        return result 
    
    def _save_subgroup(self, repo: Repositories[SubGroupModel], subgroup_model: SubGroupModel) -> SubGroupModel:
        """Salva ou atualiza o subgrupo no banco de dados e Redis."""
        if subgroup_model.id:
            subgroup_model = repo.db.update_by_id(subgroup_model.id, subgroup_model)
            if not subgroup_model:
                raise RuntimeError("Failed to update subgroup in the database.")
        else:
            subgroup_model = repo.db.add(subgroup_model)
            if not subgroup_model:
                raise RuntimeError("Failed to upsert subgroup in the database.")

        subgroup_model = repo.db.get_by_id(subgroup_model.id, load=['permissions', 'group'])
        
        return subgroup_model
