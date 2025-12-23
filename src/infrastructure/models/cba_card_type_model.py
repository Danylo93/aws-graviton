from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId


class CBACardTypeModel(PostgreSqlModel):
    __tablename__ = 'cba_card_types'
    __timestamp__ = True

    id = ColumnId()
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)

    people = relationship("PersonModel", back_populates="cba_card_type")

    def __repr__(self):
        return f"<CBACardTypeModel(id='{self.id}', type='{self.type}')>"