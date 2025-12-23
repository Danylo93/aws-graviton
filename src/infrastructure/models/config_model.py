from sqlalchemy import Column, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

class ConfigModel(PostgreSqlModel):
    __tablename__ = "config"
    __timestamp__ = True

    id = ColumnId()
    profile_id = ColumnId(ForeignKey('profile.id'), unique=False)
    client_name = Column(String, nullable=False)
    allow_notifications = Column(Boolean, nullable=False, default=True)
    face_id = Column(Boolean, nullable=False, default=True)
    biometrics = Column(Boolean, nullable=False, default=True)
    location = Column(Boolean, nullable=False, default=True)
    
    profile = relationship('ProfileModel', foreign_keys=[profile_id])