from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model.postgresql_model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import AppClientPermissions

class PermissionModel(PostgreSqlModel):
    __tablename__ = 'permissions'
    __timestamp__ = True
    __userstamp__ = True
    
    id = ColumnId()
    app_client_id = ColumnId(ForeignKey('app_clients.id'), unique=False)
    service_id = ColumnId(ForeignKey('services.id'), unique=False)
    
    app_client_name = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    
    get = Column(Boolean, default=False)
    post = Column(Boolean, default=False)
    put = Column(Boolean, default=False)
    delete = Column(Boolean, default=False)

    # Many-to-One relationships with AppClients and Services
    app_client = relationship(
        'AppClientModel', 
        back_populates="permissions", 
        foreign_keys=[app_client_id]
    )

    service = relationship(
        'ServiceModel', 
        back_populates="permissions", 
        foreign_keys=[service_id]
    )

    __table_args__ = (UniqueConstraint('app_client_id', 'service_id', name='_app_service_uc'),)
    
    def to_vo(self) -> AppClientPermissions:
        return AppClientPermissions(
            id=self.id,
            client_name=self.app_client_name,
            service_name=self.service_name,
            get=self.get,
            post=self.post,
            put=self.put,
            delete=self.delete,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            deleted_by=self.deleted_by
        )
    
    def __repr__(self):
        return f"<Permission(app_client_name='{self.app_client_name}', service_name='{self.service_name}')>"

