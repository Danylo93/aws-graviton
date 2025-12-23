from sqlalchemy import Column, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import BasePermissions


class AppClientGroupsPermissionsModel(PostgreSqlModel):
    __tablename__ = 'app_client_groups_permissions'
    __timestamp__ = True

    app_client_id = ColumnId(ForeignKey('app_clients.id', ondelete='CASCADE'), unique=False)
    group_id = ColumnId(ForeignKey('groups.id', ondelete='CASCADE'), unique=False)

    get = Column(Boolean, default=False)
    post = Column(Boolean, default=False)
    put = Column(Boolean, default=False)
    delete = Column(Boolean, default=False)

    # Relacionamento com AppClientModel
    app_client = relationship(
        'AppClientModel', 
        back_populates='app_client_groups_permissions', 
        foreign_keys=[app_client_id]
    )

    # Relacionamento com GroupModel
    group = relationship(
        'GroupModel', 
        back_populates='app_client_groups_permissions', 
        foreign_keys=[group_id]
    )

    # Constraint de unicidade para evitar duplicatas
    __table_args__ = (
        UniqueConstraint('app_client_id', 'group_id', name='_app_client_group_uc'),
    )

    def to_vo(self) -> BasePermissions:
        if not self.app_client or not self.app_client.name:
            raise ValueError("App client name is required for permissions.")

        return BasePermissions(
            name=self.app_client.name,
            get=self.get,
            post=self.post,
            put=self.put,
            delete=self.delete
        )

    
    def __repr__(self):
        return f"<AppClientGroupsPermissionsModel(app_client_id='{self.app_client_id}', group_id='{self.group_id}')>"
    