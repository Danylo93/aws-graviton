from arcs_lib_pca.infrastructure.model import ColumnId, PostgreSqlModel
from sqlalchemy import Column, String

class KeyContactRoleModel(PostgreSqlModel):

    __tablename__ = 'key_contact_roles'
    __timestamp__ = True
    __userstamp__ = True

    id = ColumnId()
    name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<KeyContactRole(id='{self.id}', name='{self.name}')>"