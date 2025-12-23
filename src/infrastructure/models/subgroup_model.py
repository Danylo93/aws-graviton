from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import SubGroupPermissions

from src.infrastructure.models.service_subgroups_permissions_model import ServiceSubgroupsPermissionsModel

class SubGroupModel(PostgreSqlModel):
    __tablename__ = 'subgroups'
    __timestamp__ = True
    __userstamp__ = True

    id = ColumnId()
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    group_id = Column(ForeignKey('groups.id'), nullable=False, unique=False)
    is_mandatory = Column(Boolean, nullable=False, default=False, unique=False)

    # Relacionamento com GroupModel
    group = relationship('GroupModel', back_populates='subgroups')

    # Relacionamento com ProfileModel
    profiles = relationship('ProfileModel', back_populates='subgroup', cascade="all, delete")

    # Relacionamento com ServiceSubgroupsPermissionsModel
    permissions = relationship(
        'ServiceSubgroupsPermissionsModel',
        back_populates='subgroup',
        cascade="all, delete-orphan"
    )

    # Relacionamento Many-to-Many com ServiceModel
    services = relationship(
        'ServiceModel',
        secondary='service_subgroups_permissions',
        back_populates='subgroups'
    )

    def to_vo(self, permissions: List[ServiceSubgroupsPermissionsModel]) -> List[SubGroupPermissions]:
        return [
            SubGroupPermissions(
                id = self.id,
                name = self.name,
                service = {
                    "name": permission.service.name,
                    "get": permission.get,
                    "post": permission.post,
                    "put": permission.put,
                    "delete": permission.delete
                },
                controllers = permission.controllers,
                created_at = self.created_at,
                updated_at = self.updated_at,
                deleted_at = self.deleted_at,
                created_by = self.created_by,
                updated_by = self.updated_by,
                deleted_by = self.deleted_by,
            ) for permission in permissions 
        ]

    def __repr__(self):
        return (
            f"<SubGroupModel(id='{self.id}', name='{self.name}', "
            f"is_mandatory='{self.is_mandatory}', "
            f"description='{self.description}')>"
        )