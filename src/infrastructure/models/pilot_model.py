from sqlalchemy import Column, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

from src.domain.value_objects import PilotStatusEnum

class PilotModel(PostgreSqlModel):
    __tablename__ = "pilots"
    __timestamp__ = True
    __userstamp__ = True

    id = ColumnId()
    profile_id = ColumnId(ForeignKey('access_profiles.profile_id'), unique=False, primary_key=False)
    person_id = ColumnId(ForeignKey('people.id'), unique=False, primary_key=False)
    name = Column(String, nullable=False)
    identifier = Column(String, unique=False, nullable=False)
    status = Column(String, nullable=False, default=PilotStatusEnum.INACTIVE.value)
    bop = Column(Float, nullable=True)

    profile = relationship('AccessProfileModel')
    person = relationship('PersonModel')
