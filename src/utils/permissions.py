import typing as t
from src.domain.value_objects import BasePermission, ProfilePermission, SubGroupPermission
from src.infrastructure.models import PersonModel, ProfileModel
from arcs_lib_pca.domain.value_objects import ProfilePermissions, DateTime, GenericUUID

def merge_subgroup_permissions(current: t.List[t.Optional[SubGroupPermission]], new: t.List[t.Optional[SubGroupPermission]]) -> t.Dict[str, SubGroupPermission]:
    # Cria um dicionário para acesso rápido a cada SubGroupPermission usando o nome do serviço como chave
    permission_dict = {perm.service.name: perm for perm in current} if current else {}
    
    if not new:
        return permission_dict

    # Itera sobre cada permissão em 'new' e mescla com as permissões existentes
    for new_perm in new:
        if new_perm.service.name in permission_dict:
            # Recupera a permissão existente
            existing_perm = permission_dict[new_perm.service.name]
            
            # Mescla as permissões de 'service'
            existing_perm.service = merge_base_permission(existing_perm.service, new_perm.service)
            
            # Mescla as permissões de 'controllers'
            existing_perm.controllers = merge_base_permissions_list(existing_perm.controllers, new_perm.controllers)
        else:
            # Adiciona a nova permissão se não existir
            permission_dict[new_perm.service.name] = new_perm

    # Retorna os valores do dicionário como uma lista
    return permission_dict

def merge_base_permission(current: BasePermission, new: BasePermission) -> BasePermission:
    # Mescla cada campo, usando o valor de 'new' quando ele estiver presente
    return BasePermission(
        name=current.name,  # 'name' é mantido do original, pois identifica a permissão
        get=new.get if not new.get is None else current.get,
        post=new.post if not new.post is None else current.post,
        put=new.put if not new.put is None else current.put,
        delete=new.delete if not new.delete is None else current.delete
    )

def merge_base_permissions_list(current: t.List[BasePermission], new: t.List[BasePermission]) -> t.List[BasePermission]:
    # Cria um dicionário de permissões a partir de 'current' para acesso rápido
    permissions_dict = {perm.name: perm for perm in current} if current else {}

    # Mescla ou adiciona cada permissão de 'new'
    for new_perm in new:
        if new_perm.name in permissions_dict:
            # Mescla permissões existentes
            permissions_dict[new_perm.name] = merge_base_permission(permissions_dict[new_perm.name], new_perm)
        else:
            # Adiciona nova permissão se não existir
            permissions_dict[new_perm.name] = new_perm

    # Retorna os valores do dicionário como uma lista
    return list(permissions_dict.values())

def convert_profile_permission(
    profile_permission : ProfilePermission, 
    profile_model: ProfileModel, 
    person: PersonModel, 
    executed_by: GenericUUID
) -> ProfilePermissions:
    perm = profile_model.get_permission_by_service(service_name=profile_permission.service.name)
    
    return profile_permission.to_vo(
        profile_id=profile_model.id,
        profile_name=person.full_name,
        created_at=perm.created_at if perm else DateTime.now() ,
        created_by=perm.created_by if perm else executed_by,
        updated_at=DateTime.now() if perm else None,
        updated_by=executed_by if perm else None,
        deleted_at=None,
        deleted_by=None
    )
