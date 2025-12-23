
from arcs_lib_pca.infrastructure.model import ColumnId, PostgreSqlModel

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

class KeyContactModel(PostgreSqlModel):

    __tablename__ = 'key_contacts'
    __timestamp__ = True
    __userstamp__ = True

    id = ColumnId()

    name = Column(String, nullable=False, unique=False)
    contact = Column(String, nullable=False, unique=False)

    role_id = ColumnId(ForeignKey('key_contact_roles.id'), unique=False)
    role = relationship('KeyContactRoleModel', foreign_keys=[role_id])

    def __repr__(self):
        return f"<KeyContact(id='{self.id}', name='${self.name}', contact='{self.contact}')>"
