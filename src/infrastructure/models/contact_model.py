from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

class ContactModel(PostgreSqlModel):
    __tablename__ = 'contacts'
    __timestamp__ = True

    id = ColumnId()
    contact_type_id = ColumnId(ForeignKey('contact_types.id'), unique=False)
    person_id = ColumnId(ForeignKey('people.id'), unique=False)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    is_emergency = Column(Boolean, default=False)
    is_main = Column(Boolean, default=False)
    is_verified = Column(DateTime, nullable=True)

    person = relationship('PersonModel', foreign_keys=[person_id], cascade="all, delete")
    contact_type = relationship("ContactTypeModel", foreign_keys=[contact_type_id], cascade="all, delete")

    def __repr__(self):
        return f"<ContactModel(id='{self.id}', name='{self.name}', value='{self.value}')>"