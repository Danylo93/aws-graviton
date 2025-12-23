import typing as t
from http import HTTPStatus

from pydantic import EmailStr, HttpUrl

from arcs_lib_pca.use_case import UseCase
from arcs_lib_pca.domain.value_objects import GenericUUID, AccessProfile, DateTime
from arcs_lib_pca.infrastructure.repository import Repositories
from arcs_lib_pca.use_case.base import execute_use_case
from sqlalchemy import or_

from src.domain.value_objects import ErrorRegisterUserVO, PersonBase, ContactsRequest, ProfileRequest, AddressRequest, ResponseRegisterUseCase
from src.infrastructure.models import (
    PersonModel, 
    UserModel, 
    UserGuestModel, 
    ProfileModel, 
    AccessProfileModel,
    AddressModel,
    ContactModel,
    ContactTypeModel
)
from src.use_case import LoadProfileUseCase, LoadAccessProfilesUseCase

class RegisterUserUseCase(UseCase[ResponseRegisterUseCase]):

    def get_user_guest_by_email_or_person(
        self,
        email: str,
        person_model: PersonModel,
        user_guest_repo: Repositories[UserGuestModel],
        ) -> t.List[UserGuestModel]:
        access_profiles : t.List[AccessProfile] = execute_use_case(LoadAccessProfilesUseCase, person_id=person_model.id)
        profile_ids = []

        for ap_list in access_profiles.values():
            for ap in ap_list:
                profile_ids.append(ap.profile_id)

        return user_guest_repo.db.find(
            filters=[or_(
                UserGuestModel.email == email,
                UserGuestModel.profile_id.in_(profile_ids)
            )]
        )

    def execute(
        self,
        email: EmailStr,
        person: PersonBase,
        password: str,
        registration_page_url: HttpUrl,
        user_guest_id: t.Optional[GenericUUID],
        subgroup_id: t.Optional[GenericUUID],
        profile: t.Optional[ProfileRequest],
        contacts: t.List[t.Optional[ContactsRequest]],
        address: t.Optional[AddressRequest],
        email_verified: t.Optional[bool] = False
    ):
        user_guest_repo = Repositories(UserGuestModel())
        user_repo = Repositories(UserModel())
        person_repo = Repositories(PersonModel())
        profile_repo = Repositories(ProfileModel())
        contacts_repo = Repositories(ContactModel())
        contact_type_repo = Repositories(ContactTypeModel())
        address_repo = Repositories(AddressModel())

        user_guest_model: UserGuestModel = user_guest_repo.model
        user_model: UserModel = user_repo.model
        person_model: PersonModel = person_repo.model
        profile_model: ProfileModel = profile_repo.model
        email = str(email).lower().strip()

        if user_repo.db.contains(email=email):
            return ResponseRegisterUseCase(
                http_status=HTTPStatus.CONFLICT, 
                access_profile=None,  
                message="User already registered"
            )

        #######################
        #Caso tenha um convite ativo, obtém os dados de profile e person
        #######################
        if user_guest_id:
            if not (user_guest_model := Repositories(UserGuestModel()).db.get_by_id(id=user_guest_id, load=["profile"])):
                return ResponseRegisterUseCase(
                    http_status=HTTPStatus.BAD_REQUEST,
                    access_profile=None,
                    message="Guest code is not valid"
                )
            profile_model = user_guest_model.profile
            person_model = person_repo.db.get_by_id(profile_model.person_id)

        person_by_doc = person_repo.db.get_by(doc=person.doc) 
        person_model = person_by_doc or person_model

        #######################
        #Cria ou atualiza um person
        #######################
        person_data = person.model_dump()
        full_name_parts = person_data['full_name'].split(' ')

        if not person_data['first_name']:
            person_data['first_name'] = full_name_parts[0] if full_name_parts else None

        if not person_data['last_name']:
            person_data['last_name'] = full_name_parts[-1] if len(full_name_parts) > 1 else None

        if person_model.id: #Caso tenha o id então representa o registro de um usuário que recebeu um convite
            person_model = person_model.merge(person_data)
            person_model = person_repo.db.update_by_id(id=person_model.id, data=person_model)
        else:
            person_model = person_repo.db.add(person_data)

        if not user_guest_id and not subgroup_id and person_model:
            user_guest_model = self.get_user_guest_by_email_or_person(
                email=email,
                person_model=person_model,
                user_guest_repo=user_guest_repo
            )

            if user_guest_model:
                return ResponseRegisterUseCase(
                    http_status=HTTPStatus.CONFLICT, 
                    data=ErrorRegisterUserVO(email=email).to_dict(),  
                    message="E-mail or person already registered in user guest"
                )


        if not person_model.id:
            return ResponseRegisterUseCase(
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
                access_profile=None,
                message="Error add person"
            )
            
        #######################
        #Cria ou atualiza um novo usuário
        #######################
        user_model = user_model.set_password(password)
        user_model.person_id = person_model.id
        user_model.email = email
        user_model.email_verified = DateTime.now() if email_verified else None
        user_model.meta_data = {}

        user_model = user_repo.db.upsert(user_model, email=user_model.email)

        if not user_model:
            if not user_guest_id:
                person_repo.db.remove_by_id(person_model.id)
            return ResponseRegisterUseCase(
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR, 
                access_profile=None,  
                message="Error add user"
            )

        ######################
        # Cria um perfil para a pessoa
        ######################
        profile_id = None
        profile_description = None
        profile_picture = None
        profile_permissions = None

        if profile:
            profile_description = profile.description
            profile_picture = profile.pictures
            profile_permissions = profile.permissions

        if profile_model.id:
            profile_id = profile_model.id

        profile_model = execute_use_case(LoadProfileUseCase,                  
                                        person=person_model,
                                        subgroup_id=subgroup_id,
                                        profile_id=profile_id,
                                        profile_description=profile_description,
                                        profile_picture=profile_picture,
                                        profile_permissions=profile_permissions,
                                        is_invite=False
                                    )

        if not profile_model.id:
            user_repo.db.remove_by_id(user_model.id)
            if not user_guest_id:
                person_repo.db.remove_by_id(person_model.id)

            return ResponseRegisterUseCase(
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR, 
                access_profile=None,  
                message="Error add profile"
            )

        ########################
        # Aqui já pegou o profile do user_guest ou criou um novo
        ########################
        access_profiles = execute_use_case(LoadAccessProfilesUseCase,
                                            profile_id=profile_model.id)

        access_profile: AccessProfile = access_profiles[person_model.id][0]

        ap_model = None
        if Repositories(AccessProfileModel()).db.contains(profile_id=profile_model.id, person_id=person_model.id):
            ap_model = Repositories(AccessProfileModel()).db.update(data=access_profile.to_dict(), profile_id=profile_model.id)
        else:
            ap_model = Repositories(AccessProfileModel()).db.add(access_profile.to_dict())

        if not ap_model:
            user_repo.db.remove_by_id(user_model.id)
            if not user_guest_id:
                profile_repo.db.remove_by_id(person_model.id)
                person_repo.db.remove_by_id(person_model.id)

            return ResponseRegisterUseCase(
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR, 
                access_profile=None,  
                message="Error add access profile"
            )

        access_profile.upsert_in_redis(profile_repo.redis)

        # ADDRESS CREATION
        if address:
            address_data = address.model_dump()
            address_data['person_id'] = access_profile.person_id

            address_repo.db.add(address_data)

        # CONTACTS CREATION
        if contacts:
            #TODO: centralizar o processo de criação de contatos, para ser possível validar cada contato adicionado
            contacts_data = []
            for contact in contacts:
                if not contact:
                    continue

                contact_data = contact.model_dump()
                contact_data['person_id'] = access_profile.person_id
                if not contact_type_repo.db.contains(id=contact_data['contact_type_id']):
                    contact_type_others = contact_type_repo.db.get_by(type_contact="Others")

                    if not contact_type_others:
                        continue

                    contact_data['contact_type_id'] = contact_type_others.id

                contacts_data.append(contact_data)

            contacts_repo.db.add_all(contacts_data)
        
        # A deleção do convite está sendo feita aqui, para garantir que o usuário não perca o convite sem ter os devidos acessos definidos
        if user_guest_id:
            user_guest_repo.db.delete(id=user_guest_id)
        
        # TODO: Adicionar email de boas vindas

        return ResponseRegisterUseCase(
            http_status=HTTPStatus.CREATED, 
            access_profile=access_profile, 
            message="User registered successfully"
        )