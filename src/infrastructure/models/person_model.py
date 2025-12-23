from sqlalchemy import Column, ForeignKey, String, DateTime, Float, Integer
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

from src.domain.value_objects import PersonBase

class PersonModel(PostgreSqlModel):
    __tablename__ = 'people'
    __timestamp__ = True

    id = ColumnId()
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    identification = Column(String, nullable=True)
    status = Column(String, nullable=True)
    pronoun = Column(String, nullable=True)
    social_name = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    doc = Column(String, nullable=True)
    reg_doc = Column(String, nullable=True)
    passport = Column(String, nullable=True)
    birth_place = Column(String, nullable=True)
    blood_type = Column(String, nullable=True)
    medical_agreement = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    shirt_size = Column(String, nullable=True)
    shoe_size = Column(Integer, nullable=True)
    cba_card_code = Column(String, nullable=True)
    cba_card_type_id = ColumnId(ForeignKey('cba_card_types.id', ondelete="SET NULL"), nullable=True, unique=False)
    fia_card = Column(String, nullable=True)
    fia_card_type_id = ColumnId(ForeignKey('fia_card_types.id', ondelete="SET NULL"), nullable=True,  unique=False)
    cellphone = Column(String, nullable=True)
    cba_card_type = relationship('CBACardTypeModel', back_populates='people', foreign_keys=[cba_card_type_id], passive_deletes="all")
    fia_card_type = relationship('FIACardTypeModel', back_populates='people', foreign_keys=[fia_card_type_id], passive_deletes="all")
    addresses = relationship('AddressModel', back_populates='person', cascade="all, delete-orphan")
    contacts = relationship('ContactModel', back_populates='person', cascade="all, delete-orphan")
    profiles = relationship('ProfileModel', back_populates='person', cascade="all, delete-orphan")
    user = relationship('UserModel', back_populates='person', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PersonModel(id='{self.id}', full_name='{self.full_name}')>"
    
    def merge_person_base(self, base: PersonBase) -> bool:
        was_updated = False
        
        input_person = base.model_dump()

        if input_person['first_name']:
            input_person['first_name'] = str(input_person['full_name']).split(' ')[0]

        if input_person['last_name']:
            input_person['last_name'] = str(input_person['full_name']).split(' ')[-1]

        for key, value in input_person.items():
           if getattr(self, key) != value:
               was_updated = True
               setattr(self, key, value)

        return was_updated