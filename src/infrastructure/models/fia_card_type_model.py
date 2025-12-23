from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

class FIACardTypeModel(PostgreSqlModel):
    __tablename__ = 'fia_card_types'
    __timestamp__ = True

    id = ColumnId()
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)

    people = relationship("PersonModel", back_populates="fia_card_type")

    def __repr__(self):
        return f"<FIACardTypeModel(id='{self.id}', type='{self.type}')>"