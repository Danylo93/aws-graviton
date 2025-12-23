import typing as t

from arcs_lib_pca.use_case import UseCase
from arcs_lib_pca.infrastructure.repository import Repositories

from arcs_lib_pca.domain.value_objects import (
    GenericUUID, 
    SubGroupPermissions, 
    ProfilePermissions, 
    BasePermissions
)

from src.domain.value_objects import ProfilePermission
from src.infrastructure.models import (
    ProfileModel,
    SubGroupModel,
    PersonModel
)
from src.infrastructure.models.service_subgroups_permissions_model import ServiceSubgroupsPermissionsModel

class ProfilePermissionStructure(object):
    subgroup: t.Optional[SubGroupModel] = None
    subgroup_permissions: t.Optional[t.List[SubGroupPermissions]] = None
    profile: ProfileModel = None
    profile_permissions: t.Optional[t.List[ProfilePermissions]] = None
    
    def __init__(self, 
                 profile: ProfileModel,
                 subgroup: t.Optional[SubGroupModel] = None,
                 subgroup_permissions: t.Optional[t.List[SubGroupPermissions]] = None,
                 profile_permissions: t.Optional[t.List[ProfilePermissions]] = None,
                 merge: t.Optional[bool] = True,
                 **kwargs 
                ):
        self.subgroup = subgroup
        self.subgroup_permissions = subgroup_permissions
        self.profile = profile
        self.profile_permissions = profile_permissions
        
        if merge:
            self._merge_profile_subgroup_permissions()
        
        self._cast_profile_permisions()

    def _cast_profile_permisions(self):        
        """
        Casts all SubGroupPermissions to ProfilePermissions, based on the profile id and its person id.

        This method is used to transform a list of SubGroupPermissions and ProfilePermissions into a
        list of ProfilePermissions, which makes it easier to work with permissions in the codebase.

        It also updates the self.profile_permissions attribute with the new list of permissions.

        Returns:
            None
        """
        person_model: PersonModel = Repositories(PersonModel()).db.get_by_id(id=self.profile.person_id)

        if not person_model or not self.profile or not self.profile_permissions:
            return
        
        new_perms = []

        for perm in self.profile_permissions:
            if isinstance(perm, SubGroupPermissions):
                profile_permission = ProfilePermissions(
                    id=self.profile.id,
                    name=person_model.full_name,
                    service=perm.service,
                    controllers=perm.controllers,
                    created_at=perm.created_at,
                    updated_at=perm.updated_at,
                    deleted_at=perm.deleted_at,
                    created_by=perm.created_by,
                    updated_by=perm.updated_by,
                    deleted_by=perm.deleted_by,
                )

                new_perms.append(profile_permission)

                continue

            new_perms.append(perm)
        
        self.profile_permissions = new_perms

    def _merge_profile_subgroup_permissions(self):
        """
        Merges the profile's permissions with the subgroup's permissions.
        
        If the profile doesn't have any permissions, it creates a new list of permissions
        with the subgroup's permissions.
        
        If the profile has permissions, it merges the subgroup's permissions with the profile's permissions.
        If a permission is already present in the profile's permissions, it updates the permission
        with the subgroup's permission. If a permission is not present in the profile's permissions,
        it adds the subgroup's permission to the profile's permissions.
        
        The method uses a dictionary to keep track of the permissions and their indexes in the list.
        It uses this dictionary to update the permissions in the list.
        
        Returns:
            None
        """
        if not self.subgroup_permissions:
            return
        
        if not self.profile_permissions:
            person_model: PersonModel = Repositories(PersonModel()).db.get_by_id(id=self.profile.person_id)

            self.profile_permissions = [
                ProfilePermissions(
                    id=self.profile.id,
                    name=person_model.full_name,
                    service=subperm.service,
                    controllers=subperm.controllers,
                    created_at=subperm.created_at,
                    updated_at=subperm.updated_at,
                    deleted_at=subperm.deleted_at,
                    created_by=subperm.created_by,
                    updated_by=subperm.updated_by,
                    deleted_by=subperm.deleted_by,
                ) for subperm in self.subgroup_permissions
            ]
            return
        
        profile_permissions_dict = {
            self.profile_permissions[index].service.name: {
                'permission': self.profile_permissions[index],
                'index': index
                } for index in range(len(self.profile_permissions))
            }

        for i in range(len(self.subgroup_permissions)):
            subgroup_permission = self.subgroup_permissions[i]
            
            profile_permission = profile_permissions_dict.get(subgroup_permission.service.name)

            if not profile_permission:
                self.profile_permissions.append(subgroup_permission)
                continue

            self.profile_permissions[profile_permission['index']].service = self._merge(old=profile_permission['permission'].service, new=subgroup_permission.service)

            profile_namespaces_permissions_dict = {
                profile_permission['permission'].controllers[index].name: {
                    'permission': profile_permission['permission'].controllers[index], 
                    'index': index
                    } for index in range(len(profile_permission['permission'].controllers))
                }

            for j in range(len(subgroup_permission.controllers)):
                subgroup_namespace_permission = subgroup_permission.controllers[j]

                profile_namespace_permission = profile_namespaces_permissions_dict.get(subgroup_namespace_permission.name)

                if not profile_namespace_permission:
                    self.profile_permissions[i].controllers.append(
                        subgroup_namespace_permission
                    )
                    continue

                self.profile_permissions[profile_permission['index']].controllers[profile_namespace_permission['index']] = self._merge(
                    old=profile_namespace_permission['permission'],
                    new=subgroup_namespace_permission
                )

    def _merge(self, old: BasePermissions, new: BasePermissions) -> BasePermissions:
        if old.name != new.name:
            return old
        
        if new.get:
            old.get = True
        
        if new.post:
            old.post = True

        if new.put:
            old.put = True

        if new.delete:
            old.delete = True

        return old

class LoadProfilePermissionsUseCase(UseCase[t.Optional[ProfilePermissionStructure]]):
    def execute(self, 
                profile_model: ProfileModel,
                profile_permissions: t.List[ProfilePermissions] = None,
                subgroup_model: SubGroupModel = None,
                subgroup_id: t.Optional[GenericUUID] = None,
                subgroup_name: t.Optional[str] = None,
                subgroup_permissions: t.List[SubGroupPermissions] = None,
                merge: t.Optional[bool] = True
            ) -> ProfilePermissionStructure:
        
        subgroup_repo = Repositories(SubGroupModel())
        service_subgroups_permissions_repo = Repositories(ServiceSubgroupsPermissionsModel())

        if not profile_model.id:
            return None

        if not subgroup_id:
            subgroup_id = profile_model.subgroup_id

        if not subgroup_model or not subgroup_model.id:
            if subgroup_id:
                subgroup_model = subgroup_repo.db.get_by_id(subgroup_id, load=['permissions'])

            if subgroup_name:
                subgroup_model = subgroup_repo.db.get_by(name=subgroup_name, load=['permissions'])
        else:
            subgroup_model = subgroup_repo.db.get_by_id(subgroup_model.id, load=['permissions'])

        if not subgroup_permissions:
            sub_perms = service_subgroups_permissions_repo.db.find(subgroup_id=subgroup_model.id, load=['service'])
            
            if sub_perms:
                subgroup_permissions = subgroup_model.to_vo(sub_perms)

        permissions_structure = ProfilePermissionStructure(
            subgroup=subgroup_model,
            subgroup_permissions=subgroup_permissions,
            profile=profile_model,
            profile_permissions=profile_permissions,
            merge=merge
        )

        return permissions_structure
