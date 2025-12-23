from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.infrastructure.repository.dynamic_sync import RedisDynamicSync

class TechnicalTeamModel(PostgreSqlModel):

    __tablename__ = 'technical_teams'
    __timestamp__ = True
    __userstamp__ = True

    __dynamic_sync__ = RedisDynamicSync('pilot_id')

    id = ColumnId()
    pilot_id = ColumnId(ForeignKey('access_profiles.profile_id'), nullable=False, unique=False)
    mechanic_id = ColumnId(ForeignKey('access_profiles.profile_id'), nullable=True, primary_key=False, unique= False)
    engineer_id = ColumnId(ForeignKey('access_profiles.profile_id'), nullable=True, primary_key=False, unique= False)

    pilot = relationship('AccessProfileModel', foreign_keys=[pilot_id])
    mechanic = relationship('AccessProfileModel', foreign_keys=[mechanic_id])
    engineer = relationship('AccessProfileModel', foreign_keys=[engineer_id])
