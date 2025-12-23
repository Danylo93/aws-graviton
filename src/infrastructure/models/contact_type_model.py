from sqlalchemy import Column, String
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from sqlalchemy.orm import relationship


class ContactTypeModel(PostgreSqlModel):
    __tablename__ = 'contact_types'
    __timestamp__ = True

    id = ColumnId()
    type_contact = Column(String, nullable=False)
    icon = Column(String, nullable=True)
    description = Column(String, nullable=True)

    contacts = relationship("ContactModel", back_populates="contact_type", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ContactTypeModel(id='{self.id}', typeContact='{self.typeContact}')>"