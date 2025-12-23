import typing as t
from sqlalchemy import Boolean, Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import GroupPermissions
from src.infrastructure.models.app_client_groups_permissions_model import AppClientGroupsPermissionsModel

class GroupModel(PostgreSqlModel):
    __tablename__ = 'groups'
    __timestamp__ = True
    __userstamp__ = True

    id = ColumnId()
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    image_id = ColumnId(ForeignKey('files.id'), nullable=True)
    meta_data = Column(JSONB, nullable=True)
    is_mandatory = Column(Boolean, nullable=False, default=False, unique=False)

    # Relacionamento Many-to-Many com AppClientModel via AppClientGroupsPermissionsModel
    app_clients = relationship(
        'AppClientModel',
        secondary='app_client_groups_permissions',
        back_populates='groups'
    )

    # Relacionamento com SubGroupModel
    subgroups = relationship(
        'SubGroupModel', 
        back_populates='group',
        cascade="all, delete"
    )

    # Relacionamento com AppClientGroupsPermissionsModel
    app_client_groups_permissions = relationship(
        'AppClientGroupsPermissionsModel', 
        back_populates='group', 
        cascade="all, delete"
    )

    image = relationship(
        'FileModel',
        foreign_keys=[image_id]
    )

    def to_vo(self, permissions: t.List[AppClientGroupsPermissionsModel]) -> GroupPermissions:
        return GroupPermissions(
            id=self.id,
            name=self.name,
            description=self.description,
            image=self.image_id,
            app_clients=[perm.to_vo() for perm in permissions],
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            deleted_by=self.deleted_by
        )
        
    def __repr__(self):
        return (
            f"<GroupModel(id='{self.id}', name='{self.name}', "
            f"is_mandatory='{self.is_mandatory}', "
            f"description='{self.description}', image_id='{self.image_id}')>"
        )