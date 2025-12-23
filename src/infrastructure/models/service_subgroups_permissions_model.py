from typing import Optional, List, Self
from sqlalchemy import ForeignKey, UniqueConstraint, Column, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model.postgresql_model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import BasePermissions

from src.utils.permissions import merge_base_permissions_list

class ServiceSubgroupsPermissionsModel(PostgreSqlModel):
    __tablename__ = 'service_subgroups_permissions'
    __timestamp__ = True
    
    service_id = ColumnId(ForeignKey('services.id', ondelete='CASCADE'), unique=False)
    subgroup_id = ColumnId(ForeignKey('subgroups.id', ondelete='CASCADE'), unique=False)

    #Permissões que o subgrupo tem sobre o serviço
    get = Column(Boolean, default=False)
    post = Column(Boolean, default=False)
    put = Column(Boolean, default=False)
    delete = Column(Boolean, default=False)

    #Permissões que o subgrupo tem sobre os controllers/namespaces do serviço
    controllers = Column(JSONB, nullable=True) # -> List[BasePermissions]

    # Relacionamento com ServiceModel
    service = relationship('ServiceModel', back_populates='service_subgroups')

    # Relacionamento com SubGroupModel
    subgroup = relationship('SubGroupModel', back_populates='permissions')

    # Constraint para garantir que não existam duplicatas
    __table_args__ = (UniqueConstraint('service_id', 'subgroup_id', name='_service_subgroup_uc'),)
    
    def sync_controllers(self, controllers: Optional[List[BasePermissions]]) -> Self:
        """Syncs the controllers of the service with the provided controllers.

        This method merges the provided controllers with the existing controllers
        and filters out any controllers that do not belong to the namespaces of the service.

        Args:
            controllers (list[BasePermissions]): The controllers to be synced.

        Returns:
            self
        """
        # Obter os controllers existentes ou inicializar uma lista vazia        
        current_controllers = self.controllers or []

        # Mesclar os controllers fornecidos com os existentes, se aplicável
        if controllers:
            current_controllers = merge_base_permissions_list(current_controllers, controllers)

        if len(current_controllers): 
            # Filtrar apenas os controllers que pertencem aos namespaces do serviço e 
            # atualizar os controllers armazenados com a lista filtrada
            namespaces = self.service.namespaces or []
            self.controllers = [
                ctrl
                for ctrl in current_controllers
                if ctrl.name in namespaces
            ]
        return self

    def to_vo(self) -> BasePermissions:
        """
        Convert this model to a domain value object.

        :raises ValueError: If service name is not set.
        :return: A domain value object representing this model.
        :rtype: BasePermissions
        """
        if not self.service.name:
            raise ValueError("App client name is required")
        
        return BasePermissions(
            name=self.service.name,
            get=self.get,
            post=self.post, 
            put=self.put, 
            delete=self.delete
        )