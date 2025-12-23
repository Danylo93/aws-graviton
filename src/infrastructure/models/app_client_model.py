from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import ArcsAppClients


class AppClientModel(PostgreSqlModel):
    __tablename__ = 'app_clients'
    __timestamp__ = True

    id = ColumnId()
    name = Column(String, unique=True, nullable=False)
    image_id = ColumnId(ForeignKey('files.id'), nullable=True)
    name_friendly = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Relacionamento com FileModel
    image = relationship('FileModel', foreign_keys=[image_id])

    # Relacionamento Many-to-Many com GroupModel via AppClientGroupsPermissionsModel
    groups = relationship(
        'GroupModel',
        secondary='app_client_groups_permissions',
        back_populates='app_clients'
    )

    # Relacionamento Many-to-Many com ServiceModel via PermissionModel
    services = relationship(
        'ServiceModel',
        secondary='permissions',  # Tabela associativa
        back_populates='app_clients',
        overlaps="permissions,app_client"
    )

    # Relacionamento com PermissionModel
    permissions = relationship(
        'PermissionModel', 
        back_populates='app_client', 
        cascade="all, delete-orphan",
        overlaps="services"
    )

    # Relacionamento com AppClientGroupsPermissionsModel
    app_client_groups_permissions = relationship(
        'AppClientGroupsPermissionsModel', 
        back_populates='app_client', 
        cascade="all, delete"
    )

    def to_vo(self) -> ArcsAppClients:
        return ArcsAppClients(
            id=self.id,
            name=self.name,
            name_friendly=self.name_friendly,
            image_id=self.image_id,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at
        )
    
    def __repr__(self):
        return f"<AppClient(name='{self.name}', name_friendly='{self.name_friendly}')>"
