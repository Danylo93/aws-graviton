import typing as t 

from arcs_lib_pca.use_case import UseCase
from arcs_lib_pca.infrastructure.repository import Repositories
from arcs_lib_pca.domain.value_objects import (
    AccessProfile, 
    GenericUUID, 
    DateTime, 
    AppClientPermissions,
    AccessProfilePicture
)

from src.infrastructure.models import (
    ProfileModel, 
    UserGuestModel, 
    UserModel, 
    PersonModel, 
    GroupModel, 
    SubGroupModel, 
    ProviderModel, 
    AppClientModel
)

def merge_dicts_unique_list(dict1: t.Dict[GenericUUID, t.List[AccessProfile]], dict2: t.Dict[GenericUUID, t.List[AccessProfile]]) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
    """Combines two dictionaries with lists of AccessProfile and removes duplicates.

    :param dict1: first dictionary with lists of AccessProfile
    :param dict2: second dictionary with lists of AccessProfile
    :return: a dictionary with the combined lists and without duplicates"""
    result = {}
    for key in set(dict1) | set(dict2):  # Combina todas as chaves dos dois dicionários
        list1 = dict1.get(key, [])       # Obtém a lista do dict1 ou lista vazia se não existir
        list2 = dict2.get(key, [])       # Obtém a lista do dict2 ou lista vazia se não existir
        result[key] = list(set(list1 + list2))  # Combina as listas e remove duplicatas
    return result

class LoadAccessProfilesUseCase(UseCase[t.Dict[GenericUUID, t.List[AccessProfile]]]):  

    app_client_permissions: t.Optional[AppClientPermissions] = None

    def can_access_app_client(self, app_clients: t.List[AppClientModel]) -> bool:
        """
        Checks if the profile has access to the given app client.

        If either app_client_id or app_client_name are None, assume the profile has access to all app clients.

        :param app_clients: list of AppClientModel
        :return: boolean indicating whether the profile has access to the app client
        """
        if not self.app_client_permissions: #Representa que a validação do app_client não foi requerida do invocador
            return True

        for app_client in app_clients:
            if app_client.name == self.app_client_permissions.client_name or app_client.id == self.app_client_permissions.id:
                return True
        return False

    def get_by_profile(self, repo: Repositories[ProfileModel], profile_id: GenericUUID) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
        """
        Gets all access profiles associated with the given profile.

        :param repo: ProfileModel Repository
        :param profile_id: Profile identifier
        :return: Dictionary with access profiles
        """
        profile_model = repo.db.get_by_id(profile_id, load=['person', 'subgroup'])
        ap: t.Dict[GenericUUID, t.List[AccessProfile]] = {}

        if not profile_model:
            return ap

        group_repo = Repositories(GroupModel())

        user_model : UserModel = Repositories(UserModel()).db.get_by(person_id=profile_model.person_id)
        if not user_model:
            user_guest_model: t.Optional[UserGuestModel] = Repositories(UserGuestModel()).db.get_by(profile_id=profile_model.id)
            if not user_guest_model:
                return ap

        subgroup_model: SubGroupModel = profile_model.subgroup
        group_model: GroupModel = group_repo.db.get_by_id(subgroup_model.group_id)

        if not self.can_access_app_client(group_model.app_clients):
            return ap

        if not group_model:
            return ap

        pics = profile_model.pictures or {}

        ap[profile_model.person_id] = [
            AccessProfile(
                profile_id=profile_model.id,
                profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                user_id=user_model.id if user_model else None,
                email=user_model.email if user_model else user_guest_model.email,
                user_object_id=self.insert_user_object_id,
                person_id=profile_model.person_id,
                name=profile_model.person.full_name,
                group_id=group_model.id,
                group_name=group_model.name,
                group_object_id=self.insert_group_object_id,
                subgroup_id=profile_model.subgroup_id,
                subgroup_name=profile_model.subgroup.name,
                meta_data={},
                updated_at=DateTime.now()
            )
        ]
        return ap

    def get_by_user_guest(self, repo: Repositories[UserGuestModel], user_guest_id: GenericUUID = None) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
        """
        Retrieves all access profiles that the user guest has.

        :param repo: UserGuestModel repository
        :param user_guest_id: User guest identifier
        :return: Dictionary with access profiles
        """
        
        user_guest_model: t.Optional[UserGuestModel] = repo.db.get_by_id(user_guest_id)
        ap: t.Dict[GenericUUID, t.List[AccessProfile]] = {}

        if not user_guest_model:
            return ap
        
        profile_model: ProfileModel = Repositories(ProfileModel()).db.get_by_id(user_guest_model.profile_id, load=['person', 'subgroup'])

        if not profile_model:
            return ap

        subgroup_model: SubGroupModel = profile_model.subgroup
        group_model: GroupModel = Repositories(GroupModel()).db.get_by_id(subgroup_model.group_id)

        if not group_model:
            return ap

        if not self.can_access_app_client(group_model.app_clients):
            return ap

        if profile_model:
            pics = profile_model.pictures or {}

            ap[profile_model.person_id] = [
                AccessProfile(
                    profile_id=profile_model.id,
                    profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                    user_id=None,
                    email=user_guest_model.email,
                    user_object_id=self.insert_user_object_id,
                    person_id=profile_model.person_id,
                    name=profile_model.person.full_name,
                    group_id=group_model.id,
                    group_name=group_model.name,
                    group_object_id=self.insert_group_object_id,
                    subgroup_id=subgroup_model.id,
                    subgroup_name=subgroup_model.name,
                    meta_data={},
                    updated_at=DateTime.now()
                )
            ]
        return ap

    def get_by_user(self, repo: Repositories[UserModel], user_id: GenericUUID = None, email: str = None) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
        
        """
        Retrieves access profiles associated with a user based on user ID or email.

        This function fetches all access profiles for a given user by searching
        for the user using either their unique user ID or email. It returns a
        dictionary mapping the person ID to a list of access profiles.

        :param repo: Repository for UserModel to query user data.
        :param user_id: Optional; Unique identifier of the user.
        :param email: Optional; Email of the user.
        :return: A dictionary where keys are person IDs and values are lists of AccessProfile instances.
        """

        if user_id:
            user_model = repo.db.get_by_id(user_id, load=["person"])
        elif email:
            user_model = repo.db.get_by(email=email, load=["person"])
        else:
            return {}

        group_repo = Repositories(GroupModel())
        profile_repo = Repositories(ProfileModel())

        aps: t.Dict[GenericUUID, t.List[AccessProfile]] = {}
        if user_model and user_model.person:
            person: PersonModel = user_model.person
            profiles_model: t.List[ProfileModel] = profile_repo.db.find(person_id=person.id, load=["subgroup"])
            aps[person.id] = []
            
            if profiles_model:
                profiles_model: t.List[ProfileModel] = sorted(
                    profiles_model, key=lambda profile: (profile.last_access is not None, profile.last_access), reverse=True
                )  # Ordena por last_access em ordem decrescente
                for profile_model in profiles_model:
                    subgroup_model: SubGroupModel = profile_model.subgroup
                    group_model: GroupModel = group_repo.db.get_by_id(subgroup_model.group_id)

                    if not group_model:
                        continue

                    if not self.can_access_app_client(group_model.app_clients):
                        continue
                    
                    pics = profile_model.pictures or {}

                    aps[person.id].append(
                        AccessProfile(
                            profile_id=profile_model.id,
                            profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                            user_id=user_model.id,
                            email=user_model.email,
                            user_object_id=self.insert_user_object_id,
                            person_id=person.id,
                            name=person.full_name,
                            group_id=group_model.id,
                            group_name=group_model.name,
                            group_object_id=self.insert_group_object_id,
                            subgroup_id=subgroup_model.id,
                            subgroup_name=subgroup_model.name,
                            meta_data={},
                            updated_at=DateTime.now()
                        ))
        return aps

    def get_by_person(self, repo: Repositories[PersonModel], person_id: GenericUUID = None, name: str = None) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
        """
        Fetches all access profiles for a given person by searching for the person
        using either their unique person ID or name. It returns a dictionary mapping
        the person ID to a list of access profiles.

        :param repo: Repository for PersonModel to query person data.
        :param person_id: Optional; Unique identifier of the person.
        :param name: Optional; Name of the person.
        :return: A dictionary where keys are person IDs and values are lists of AccessProfile instances.
        """
        if person_id:
            person_model = repo.db.get_by_id(person_id, load=['profiles', 'user'])
        elif name:
            person_model = repo.db.get_by(name=name, load=['profiles', 'user'])
        else:
            return {}
        
        group_repo = Repositories(GroupModel())
        subgroup_repo = Repositories(SubGroupModel())

        aps: t.Dict[GenericUUID, t.List[AccessProfile]] = {}
        if person_model:
            aps[person_model.id] = []
            profiles_model: t.List[ProfileModel] = person_model.profiles
            if profiles_model:
                profiles_model: t.List[ProfileModel] = sorted(
                    profiles_model, key=lambda profile: (profile.last_access is not None, profile.last_access), reverse=True
                )  # Ordena por last_access em ordem decrescente

                for profile_model in profiles_model:                            
                    subgroup_model: t.Optional[SubGroupModel] = subgroup_repo.db.get_by_id(profile_model.subgroup_id)
                    
                    if not subgroup_model:
                        continue
                    
                    group_model: t.Optional[GroupModel] = group_repo.db.get_by_id(subgroup_model.group_id)
                    
                    if not group_model:
                        continue
                    
                    if not self.can_access_app_client(group_model.app_clients):
                        continue
                    
                    pics = profile_model.pictures or {}

                    user_guest_model: t.Optional[UserGuestModel] = Repositories(UserGuestModel()).db.get_by(profile_id=profile_model.id)

                    email = person_model.user.email if person_model.user else (user_guest_model.email if user_guest_model else None)

                    aps[person_model.id].append(AccessProfile(
                        profile_id=profile_model.id,
                        profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                        user_id=person_model.user.id if person_model.user else None,
                        email=email,
                        user_object_id=self.insert_user_object_id,
                        person_id=person_model.id,
                        name=person_model.full_name,
                        group_id=group_model.id,
                        group_name=group_model.name,
                        group_object_id=self.insert_group_object_id,
                        subgroup_id=subgroup_model.id,
                        subgroup_name=subgroup_model.name,
                        meta_data={},
                        updated_at=DateTime.now()
                    ))
        return aps

    def get_by_group(self, repo: Repositories[GroupModel], group_id: GenericUUID = None, group_name: str = None) -> t.Dict[GenericUUID, t.List[AccessProfile]]:       
        """
        Retrieves access profiles associated with a group by searching for the group
        using either their unique group ID or name. It returns a dictionary mapping
        the person ID to a list of access profiles.

        :param repo: Repository for GroupModel to query group data.
        :param group_id: Optional; Unique identifier of the group.
        :param group_name: Optional; Name of the group.
        :return: A dictionary where keys are person IDs and values are lists of AccessProfile instances.
        """
        if group_id:
            group_model = repo.db.get_by_id(group_id)
        elif group_name:
            group_model = repo.db.get_by(name=group_name)
        else:
            return {}
        
        if not group_model.id:
            return {}
                    
        if not self.can_access_app_client(group_model.app_clients):
            return {}

        profile_repo = Repositories(ProfileModel())
        user_repo = Repositories(UserModel())

        aps: t.Dict[GenericUUID, t.List[AccessProfile]] = {}
        if group_model:
            for subgroup in group_model.subgroups:
                profiles = profile_repo.db.find(subgroup_id=subgroup.id, load=['person'])                    
                if profiles:
                    profiles_model: t.List[ProfileModel] = sorted(
                        profiles, key=lambda profile: (profile.last_access is not None, profile.last_access), reverse=True
                    )  # Ordena por last_access em ordem decrescente
                    for profile_model in profiles_model:
                        if not profile_model.person.id in aps:
                            aps[profile_model.person.id] = []
                        
                        user_model: t.Optional[UserModel] = user_repo.db.get_by(person_id=profile_model.person.id)

                        if not user_model:
                            continue
                        
                        pics = profile_model.pictures or {}
                        
                        aps[profile_model.person.id].append(
                            AccessProfile(
                                profile_id=profile_model.id,
                                profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                                user_id=user_model.id,
                                email=user_model.email,
                                user_object_id=self.insert_user_object_id,
                                person_id=profile_model.person.id,
                                name=profile_model.person.full_name,
                                group_id=group_id,
                                group_name=group_model.name,
                                group_object_id=self.insert_group_object_id,
                                subgroup_id=subgroup.id,
                                subgroup_name=subgroup.name,
                                meta_data={},
                                updated_at=DateTime.now()
                            )
                        )
        return aps

    def get_by_subgroup(self, repo: Repositories[SubGroupModel], subgroup_id: GenericUUID = None, subgorup_name: str = None) ->t.Dict[GenericUUID, t.List[AccessProfile]]:
        """
        Fetches all access profiles for a given subgroup by searching for the subgroup
        using either the subgroup ID or name. It returns a dictionary mapping
        the person ID to a list of access profiles.

        :param repo: Repository for SubGroupModel to query subgroup data.
        :param subgroup_id: Optional; Unique identifier of the subgroup.
        :param subgorup_name: Optional; Name of the subgroup.
        :return: A dictionary where keys are person IDs and values are lists of AccessProfile instances.
        """
        if subgroup_id:
            subgroup_model = repo.db.get_by_id(subgroup_id, load=["group"])
        elif subgorup_name:
            subgroup_model = repo.db.get_by(name=subgorup_name, load=["group"])
        else:
            return {}

        if not subgroup_model.id:
            return {}
        
        profile_repo = Repositories(ProfileModel())

        aps: t.Dict[GenericUUID, t.List[AccessProfile]] = {}
        if subgroup_model:
            profiles = profile_repo.db.find(subgroup_id=subgroup_model.id, load=['person'])
            profile_models: t.List[ProfileModel] = sorted(
                        profiles, key=lambda profile: (profile.last_access is not None, profile.last_access), reverse=True
            )  # Ordena por last_access em ordem decrescente
            for profile_model in profile_models:
                if not profile_model.person.id in aps:
                    aps[profile_model.person.id] = []

                person_model: PersonModel = profile_model.person
                user_model: t.Optional[UserModel] = Repositories(UserModel()).db.get_by_id(person_id=person_model.id)
                
                if not user_model:
                    continue

                if not self.can_access_app_client(subgroup_model.group.app_clients):
                    continue
                
                pics = profile_model.pictures or {}

                aps[profile_model.person.id].append(
                    AccessProfile(
                        profile_id=profile_model.id,
                        profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                        user_id=user_model.id,
                        email=user_model.email,
                        user_object_id=self.insert_user_object_id,
                        person_id=person_model.id,
                        name=person_model.full_name,
                        group_id=subgroup_model.group_id,
                        group_name=subgroup_model.group.name,
                        group_object_id=self.insert_group_object_id,
                        subgroup_id=subgroup_model.id,
                        subgroup_name=subgroup_model.name,
                        meta_data={},
                        updated_at=DateTime.now()
                ))
        return aps

    def get_by_provider(self, repo: Repositories[ProviderModel], user_object_id: str = None, group_object_id: str = None) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
        """
        Fetches all access profiles associated with a user or group based on the
        object ID of the user or group provider. It returns a dictionary mapping
        the person ID to a list of access profiles.

        :param repo: Repository for ProviderModel to query provider data.
        :param user_object_id: Optional; Object ID of the user provider.
        :param group_object_id: Optional; Object ID of the group provider.
        :return: A dictionary where keys are person IDs and values are lists of AccessProfile instances.
        """
        if user_object_id:
            provider_model = repo.db.get_by(user_object_id=user_object_id, load=["user"])
            user_model: UserModel = provider_model.user

        elif group_object_id:
            provider_model = repo.db.get_by(group_object_id=group_object_id, load=["user"])
            user_model: UserModel = provider_model.user
        else:
            return {}

        aps: t.Dict[GenericUUID, t.List[AccessProfile]] = {}
        if user_model and user_model.person:
            person: PersonModel = Repositories(PersonModel()).db.get_by_id(id=user_model.person_id, load=["profiles"])
            profiles_model: t.List[ProfileModel] =  Repositories(ProfileModel()).db.find(person_id=person.id, load=["subgroup"])
            aps[person.id] = []
            
            if profiles_model:
                profiles_model: t.List[ProfileModel] = sorted(
                    profiles_model, key=lambda profile: (profile.last_access is not None, profile.last_access), reverse=True
                )  # Ordena por last_access em ordem decrescente
                for profile_model in profiles_model:
                    subgroup_model: SubGroupModel = profile_model.subgroup
                    if not subgroup_model:
                        continue

                    group_model: GroupModel = Repositories(GroupModel()).db.get_by_id(id=subgroup_model.group_id)

                    if not group_model:
                        continue

                    if not self.can_access_app_client(group_model.app_clients):
                        continue
                    
                    pics = profile_model.pictures or {}
                    
                    aps[person.id].append(
                        AccessProfile(
                            profile_id=profile_model.id,
                            profile_picture={key: AccessProfilePicture(**value) for key, value in pics.items()},
                            user_id=user_model.id,
                            user_object_id=provider_model.user_object_id,
                            email=user_model.email,
                            person_id=person.id,
                            name=person.full_name,
                            group_id=group_model.id,
                            group_name=group_model.name,
                            group_object_id=provider_model.group_object_id,
                            subgroup_id=subgroup_model.id,
                            subgroup_name=subgroup_model.name,
                            meta_data={},
                            updated_at=DateTime.now()
                        ))
        return aps
    
    def execute(self,
        profile_id: t.Optional[GenericUUID] = None,
        user_guest_id: t.Optional[GenericUUID] = None,
        user_id: t.Optional[GenericUUID] = None,
        user_object_id: t.Optional[str] = None,
        email: t.Optional[str] = None,
        person_id: t.Optional[GenericUUID] = None,
        name: t.Optional[str] = None,
        group_id: t.Optional[GenericUUID] = None,
        group_name: t.Optional[str] = None,
        group_object_id: t.Optional[str] = None,
        subgroup_id: t.Optional[GenericUUID] = None,
        subgroup_name: t.Optional[str] = None,
        insert_user_object_id: t.Optional[str] = None, # Este campo só deve ser preenchido caso queira referenciar o access_profile para uma autenticação via Provider
        insert_group_object_id: t.Optional[str] = None, # Este campo só deve ser preenchido caso queira referenciar o access_profile para uma autenticação via Provider
        app_client_permissions: t.Optional[AppClientPermissions] = None
    ) -> t.Dict[GenericUUID, t.List[AccessProfile]]:
        """
        Retrieve access profiles based on various identifiers and criteria.

        This method allows fetching access profiles by providing different parameters
        such as profile ID, user guest ID, user ID, email, person ID, name, group ID,
        group name, subgroup ID, subgroup name, and other related identifiers. It
        constructs a dictionary of access profiles by aggregating results from
        different repository queries based on the provided parameters.

        Args:
            profile_id (Optional[GenericUUID]): The unique identifier of the profile.
            user_guest_id (Optional[GenericUUID]): The unique identifier of the user guest.
            user_id (Optional[GenericUUID]): The unique identifier of the user.
            user_object_id (Optional[str]): An optional object ID for the user.
            email (Optional[str]): The email address of the user.
            person_id (Optional[GenericUUID]): The unique identifier of the person.
            name (Optional[str]): The full name of the person.
            group_id (Optional[GenericUUID]): The unique identifier of the group.
            group_name (Optional[str]): The name of the group.
            group_object_id (Optional[str]): An optional object ID for the group.
            subgroup_id (Optional[GenericUUID]): The unique identifier of the subgroup.
            subgroup_name (Optional[str]): The name of the subgroup.
            insert_user_object_id (Optional[str]): Used to reference the access profile for 
                authentication via Provider.
            insert_group_object_id (Optional[str]): Used to reference the access profile for 
                authentication via Provider.
            app_client_permissions (Optional[AppClientPermissions]): The permissions for app clients.

        Returns:
            Dict[GenericUUID, List[AccessProfile]]: A dictionary mapping person IDs to lists
            of access profiles.
        """

        access_profiles: t.Dict[GenericUUID, t.List[AccessProfile]] = {}
        self.insert_user_object_id = insert_user_object_id
        self.insert_group_object_id = insert_group_object_id
        self.app_client_permissions = app_client_permissions

        if profile_id:
            repo = Repositories(ProfileModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_profile(repo, profile_id)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)

        if user_guest_id:
            repo = Repositories(UserGuestModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_user_guest(repo, user_guest_id)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)

        if user_id or email:
            repo = Repositories(UserModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_user(repo,  user_id, email)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)

        if person_id or name:
            repo = Repositories(PersonModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_person(repo, person_id, name)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)

        if group_id or group_name:
            repo = Repositories(GroupModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_group(repo, group_id, group_name, group_object_id)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)

        if subgroup_id or subgroup_name:
            repo = Repositories(SubGroupModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_subgroup(repo, subgroup_id, subgroup_name)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)

        if user_object_id or group_object_id:
            repo = Repositories(ProviderModel())
            aps: t.Dict[GenericUUID, t.List[AccessProfile]] = self.get_by_subgroup(repo, subgroup_id, subgroup_name)
            access_profiles = merge_dicts_unique_list(access_profiles, aps)
        
        return access_profiles