import typing as t
import re
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import DateTime, AccessProfile, ProfilePicture
from arcs_lib_pca.infrastructure.repository.dynamic_sync import RedisDynamicSync

class AccessProfileModel(PostgreSqlModel):
    __tablename__ = "access_profiles"
    __timestamp__ = True
    __dynamic_sync__ = RedisDynamicSync('profile_id')

    profile_id = ColumnId(default=None)
    profile_picture = Column(JSONB, nullable=True, default=None)
    user_id = ColumnId(unique=False, primary_key=False, nullable=True)
    user_object_id = Column(String, nullable=True, default=None)
    email = Column(String, nullable=False, default=None)
    person_id = ColumnId(unique=False, primary_key=False, default=None)
    name = Column(String, nullable=False, default=None)
    group_id = ColumnId(unique=False, primary_key=False, default=None)
    group_name = Column(String, nullable=False, default=None)
    group_object_id = Column(String, nullable=True, default=None)
    subgroup_id = ColumnId(unique=False, primary_key=False, default=None)
    subgroup_name = Column(String, nullable=False, default=None)
    meta_data = Column(JSONB, nullable=True, default=None)

    # Método para validar o nome completo da pessoa
    def validate_name(self) -> bool:
        return bool(self.name and len(self.name.strip()) > 0)

    # Método para validar o e-mail da pessoa
    def validate_email(self) -> bool:
        email_regex = r"[^@]+@[^@]+\.[^@]+"
        return bool(re.match(email_regex, self.email))

    # Método para atualizar o e-mail da pessoa com validação
    def update_email(self, new_email: str):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            raise ValueError("O e-mail fornecido não é válido.")
        self.email = new_email
        self.updated_at = DateTime.now()

    # Método para verificar se a pessoa tem uma foto de perfil associada
    def has_profile_picture(self) -> bool:
        return bool(self.profile_picture)

    # Método para associar ou atualizar a foto de perfil da pessoa
    def upsert_profile_picture(self, key: str, profile_picture: ProfilePicture):
        pictures = self.profile_picture or {}

        pictures[key] = profile_picture.to_dict()

        self.profile_picture = pictures

    # Método para retornar uma representação amigável do tipo de usuário
    def get_user_type(self) -> str:
        return f"Tipo de usuário: {self.subgroup_name}"

    # Conversão de AccessProfileModel para AccessProfile value object
    def to_vo(self) -> AccessProfile:
        ap_data = self.to_dict()
        return AccessProfile(**ap_data)
        
    # Override do __repr__ para fornecer uma representação clara e útil do modelo
    def __repr__(self):
        return (
            f"<AccessProfileModel(profile_id='{self.profile_id}', "
            f"profile_picture='{self.profile_picture}', "
            f"user_id='{self.user_id}', "
            f"user_object_id='{self.user_object_id}', "
            f"email='{self.email}', "
            f"person_id='{self.person_id}', "
            f"full_name='{self.name}', "
            f"group_id='{self.group_id}', "
            f"group_name='{self.group_name}', "
            f"group_object_id='{self.group_object_id}', "
            f"subgroup_id='{self.subgroup_id}', "
            f"subgroup_name='{self.subgroup_name}', "
            f"meta_data='{self.meta_data}')>"
        )

    # Override do __str__ para fornecer uma descrição amigável da pessoa
    def __str__(self):
        return f"{self.subgroup_name}: {self.name} <{self.email}>"