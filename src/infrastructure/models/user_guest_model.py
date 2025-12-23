from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, String, DateTime

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain.value_objects import GenericUUID


class UserGuestModel(PostgreSqlModel):
    __tablename__ = 'user_guests'
    __timestamp__ = True
    __userstamp__ = True

    id = ColumnId()
    email = Column(String, nullable=False)
    profile_id = Column(ForeignKey('profile.id'), nullable=False)
    code = Column(String, nullable=False, unique=True)

    profile = relationship('ProfileModel', foreign_keys=[profile_id], cascade="all, delete")
    
    def generate_code(self) -> str:
        self.code = str(GenericUUID.next_id()).replace("-", "")[:6]
        return self.code

    def __repr__(self):
        return f"<UserGuestModel(id='{self.id}', email='{self.email}')>"