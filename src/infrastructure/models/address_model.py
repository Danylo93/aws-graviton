from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

class AddressModel(PostgreSqlModel):
    __tablename__ = 'addresses'
    __timestamp__ = True

    id = ColumnId()
    person_id = Column(ForeignKey('people.id'), nullable=False)
    cep = Column(String, nullable=True)
    address = Column(String, nullable=False)
    code_address = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    address_complement = Column(String, nullable=True)

    person = relationship('PersonModel', back_populates="addresses", foreign_keys=[person_id], cascade="all, delete")

    def __repr__(self):
        return f"<AddressModel(id='{self.id}', address='{self.address}')>"