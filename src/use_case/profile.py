import typing as t
from enum import Enum

from arcs_lib_pca.use_case import UseCase, execute_use_case
from arcs_lib_pca.domain.value_objects import DateTime, GenericUUID
from arcs_lib_pca.infrastructure.repository import Repositories

# Definindo enums locais para substituir os que não existem mais em arcs_lib_pca
class MandatoryGroup(Enum):
    PUBLIC = "Public"

class MandatorySubgroup(Enum):
    MAIN_PUBLIC = "Public User"
from arcs_lib_pca.infrastructure.repository.redis_repository import RedisRepository
from arcs_lib_pca.utils.json import data_decode
from arcs_lib_pca.arcs import get_instance_app

from src.infrastructure.models import (
    ProfileModel, 
    PersonModel, 
    SubGroupModel, 
    ConfigModel, 
    AppClientGroupsPermissionsModel
)
from src.domain.value_objects import ProfilePermission, ProfilePicture
from src.infrastructure.models.access_profile_model import AccessProfileModel
from src.use_case.access_profile import LoadAccessProfilesUseCase
from src.utils.permissions import convert_profile_permission
from .group import LoadGroupUseCase
from .subgroup import LoadSubGroupUseCase
from .permissions import LoadProfilePermissionsUseCase, ProfilePermissionStructure
from arcs_lib_pca.domain.value_objects import File
class LoadProfileUseCase(UseCase[t.Optional[ProfileModel]]):

    def execute(self, 
                person: PersonModel,
                profile_id: t.Optional[GenericUUID] = None,
                profile_description: t.Optional[str] = None,
                profile_picture: t.Optional[t.Dict[str, File]] = None,
                profile_permissions: t.List[ProfilePermission] = None,
                subgroup_id: t.Optional[GenericUUID] = None,
                is_invite: t.Optional[bool] = True,
                merge: t.Optional[bool] = True,
                **kwargs
            ) -> t.Optional[ProfileModel]:
        """
        Método responsável por implementar a lógica de criação ou atualização de um profile.

        Este método recebe informações relacionadas a um profile e decide se deve criar um novo 
        ou atualizar um existente, com base no parâmetro `profile_id`. Se `profile_id` for fornecido, 
        o método buscará o profile correspondente e o atualizará com os novos valores. Caso contrário, 
        um novo profile será criado utilizando as informações fornecidas.

        Args:
            person (PersonModel): O modelo da pessoa associada ao profile.
            profile_id (Optional[GenericUUID]): O ID único do profile a ser atualizado, caso exista. 
                Se não for fornecido, um novo profile será criado.
            profile_description (Optional[str]): Uma descrição opcional para o profile.
            profile_picture (Optional[ProfilePicture]): Uma imagem de perfil opcional.
            profile_permission (Optional[ProfilePermission]): As permissões associadas ao profile.
            subgroup_id (Optional[GenericUUID]): O ID do subgrupo ao qual o profile pertence, se aplicável.
            **kwargs: Parâmetros adicionais que podem ser utilizados pela lógica interna.

        Returns:
            Optional[ProfileModel]: O modelo do profile criado ou atualizado, ou `None` se a operação 
            não for concluída.

        Raises:
            ValueError: Caso os parâmetros fornecidos sejam inválidos ou inconsistentes.
            ProfileNotFoundError: Caso o `profile_id` seja fornecido, mas não corresponda a um profile existente.

        Example:
            Criar um novo profile:
                >>> use_case = LoadProfileUseCase()
                >>> new_profile = use_case.execute(
                ...     person=person_instance,
                ...     subgroup_id=<uuid_admin>,
                ...     profile_description="Admin Profile",
                ...     profile_permission=permissions_instance
                ... )

            Atualizar um profile existente:
                >>> updated_profile = use_case.execute(
                ...     person=person_instance,
                ...     profile_id="123e4567-e89b-12d3-a456-426614174000",
                ...     profile_description="Updated Description"
                ... )
        """
        profile_repo = Repositories(ProfileModel())
        profile_model : ProfileModel = profile_repo.model
        subgroup_repo = Repositories(SubGroupModel())

        subgroup_model = subgroup_repo.model
        is_new_profile = False 

        ## Se for passado um profile_id válido será uma atualização caso contrário uma criação
        if profile_id and (p_model := profile_repo.db.get_by(id=profile_id, person_id=person.id)):
            profile_model = p_model
        else:
            profile_model.person_id = person.id

        ##Defini a qual subgrupo esse perfil pertence
        if subgroup_id and (subgroup_model := subgroup_repo.db.get_by_id(subgroup_id)):
            profile_model.subgroup_id = subgroup_model.id

        if not profile_model.subgroup_id:
            group_model = execute_use_case(LoadGroupUseCase, group_name=str(MandatoryGroup.PUBLIC.value).lower(), is_mandatory=True)
            subgroup_model = execute_use_case(LoadSubGroupUseCase, group_model=group_model, subgroup_name=str(MandatorySubgroup.MAIN_PUBLIC.value).lower(), is_mandatory=True)

            if not subgroup_model:
                raise RuntimeError("Subgroup not found")
            profile_model.subgroup_id = subgroup_model.id

        ##Defini uma descrição para aparecer na tela perfil do usuário
        if profile_description:
            profile_model.description = profile_description

        if not profile_model.description:
            profile_model.description = f"Perfil do tipo {subgroup_model.name} com acesso as aplicações da Porschecup Brasil"

        ##Define a imagem `default` do perfil caso seja passada
        if profile_picture:
            for key, value in profile_picture.items():
                profile_repo.storage.add(value)
                profile_model = profile_model.set_picture(key, value)

        if not profile_model.id:
            profile_model.permissions = []
            profile_model = profile_repo.db.add(profile_model)
            is_new_profile = True

            if not profile_model:
                raise ValueError("Failed to create profile")
        
        req = get_instance_app().service.request
        
        # Atualiza ou gera uma nova permissions
        prof_permissions = [
            convert_profile_permission(
                profile_model=profile_model,
                person=person,
                profile_permission=perm,
                executed_by=req.current_profile.profile_id
            ) for perm in profile_permissions
        ] if req.is_auth() and profile_permissions else []

        permission_structure = execute_use_case(
            LoadProfilePermissionsUseCase, 
            profile_model=profile_model,
            profile_permissions=prof_permissions,
            subgroup_model=subgroup_model,
            merge=merge
        )

        if permission_structure and permission_structure.profile_permissions:
            profile_model.permissions = self._update_profile_permissions_on_redis_and_convert_to_dict(permission_structure, profile_repo.redis)

        profile_model = profile_repo.db.update_by_id(id=profile_model.id, data=profile_model)

        if not is_invite:
            self._create_public_profile(person)
        
        if not is_new_profile:
    
            return profile_model

        apps_of_group_models = Repositories(AppClientGroupsPermissionsModel()).db.find(group_id=subgroup_model.group_id, load=["app_client"])

        
        self._create_default_config(profile_model, apps_of_group_models)

        return profile_model
    
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

    def _create_default_config(self, profile_model: ProfileModel, apps_of_group_models: t.List[AppClientGroupsPermissionsModel]):
        for ag_model in apps_of_group_models:
            Repositories(ConfigModel()).db.add(data={
                "profile_id": profile_model.id,
                "client_name": ag_model.app_client.name, #TODO: substituir de app_client.name para ag_model.app_client_id
                "allow_notifications": True,
                "face_id": True,
                "biometrics": True,
                "location": True
            })

    def _create_public_profile(self, person: PersonModel):
        public_subgroup : SubGroupModel | None = Repositories(SubGroupModel()).db.get_by(name=str(MandatorySubgroup.MAIN_PUBLIC.value).lower())

        if not public_subgroup:
            return

        public_profile = Repositories(ProfileModel()).db.get_by(person_id=person.id, subgroup_id=public_subgroup.id)

        if public_profile:
            return
        
        public_user_data = {
            "description": f"Perfil do tipo {public_subgroup.name} com acesso as aplicações da Porschecup Brasil",
            "person_id": person.id,
            "subgroup_id": public_subgroup.id,
            "last_access": DateTime.now(),
        }

        public_profile = Repositories(ProfileModel()).db.add(public_user_data)

        permission_structure = execute_use_case(
            LoadProfilePermissionsUseCase,
            profile_model=public_profile,
            subgroup_id=public_subgroup.id
            )
        
        data = public_profile.to_dict()

        data['permissions'] = []

        if permission_structure and permission_structure.profile_permissions:
            data['permissions'] = self._update_profile_permissions_on_redis_and_convert_to_dict(permission_structure, Repositories(ProfileModel()).redis)

        public_profile = Repositories(ProfileModel()).db.update_by_id(id=public_profile.id, data=data)

        access_profile = execute_use_case(LoadAccessProfilesUseCase, profile_id=public_profile.id).get(person.id)

        if access_profile:
            access_profile = access_profile[0]

            Repositories(AccessProfileModel()).db.upsert(data=access_profile.to_dict(), profile_id=public_profile.id)
            
            access_profile.upsert_in_redis(Repositories(ProfileModel()).redis)

        apps_of_group_models = Repositories(AppClientGroupsPermissionsModel()).db.find(group_id=public_subgroup.group_id, load=["app_client"])
        
        self._create_default_config(public_profile, apps_of_group_models)