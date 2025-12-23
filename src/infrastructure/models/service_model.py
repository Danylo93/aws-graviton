from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model.postgresql_model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import ArcsServices

class ServiceModel(PostgreSqlModel):
    __tablename__ = 'services'
    __timestamp__ = True
    
    id = ColumnId()
    name = Column(String, unique=True, nullable=False)
    namespaces = Column(JSONB, nullable=False)
    name_friendly = Column(String, nullable=True)
    icon_id = ColumnId(ForeignKey('files.id'), nullable=True)
    domain = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    internal_url = Column(String, nullable=True)
    external_url = Column(String, nullable=True)
    port = Column(String, nullable=True)
    
    # Relacionamento com FileModel
    icon = relationship('FileModel', foreign_keys=[icon_id])
    
    # Relacionamento direto com PermissionModel
    permissions = relationship(
        'PermissionModel', 
        back_populates='service', 
        cascade="all, delete-orphan", 
        overlaps="app_clients"
    )

    app_clients = relationship(
        'AppClientModel',
        secondary='permissions',
        back_populates='services',
        overlaps="permissions,service"
    )
    
    # Relacionamento com ServiceSubgroupsPermissionsModel
    service_subgroups = relationship(
        'ServiceSubgroupsPermissionsModel',
        back_populates='service',
        cascade="all, delete-orphan"
    )

    # Relacionamento Many-to-Many com SubGroupModel via tabela intermediária
    subgroups = relationship(
        'SubGroupModel',
        secondary='service_subgroups_permissions',
        back_populates='services',
        overlaps="service_subgroups"
    )

    def to_vo(self) -> ArcsServices:
        return ArcsServices(
            id= self.id,
            name= self.name,
            name_friendly= self.name_friendly,
            icon_id= self.icon_id,
            description= self.description,
            domain= self.domain,
            version= self.version,
            internal_url= self.internal_url,
            external_url= self.external_url,
            port= self.port,
            namespaces= self.namespaces,
            created_at= self.created_at,
            updated_at= self.updated_at,
            deleted_at= self.deleted_at,
        )
    
    
    def __repr__(self):
        return f"<ServiceModel(name='{self.name}', resource_path='{self.resource_path}')>"