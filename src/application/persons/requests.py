from typing import Optional

from pydantic import Field, field_validator
from arcs_lib_pca.domain.value_objects import GenericUUID, DateTime
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanUpdate, CanDelete

class GetAllPersonRequestAuth(RequestAuth):
    page: int = Field(default=1, ge=1, description="page")
    per_page: int = Field(default=10, ge=1, description="per_page")

    def permissions(self):
        return [CanRead]

class GetPersonRequestAuth(RequestAuth):
    person_id: GenericUUID = Field(..., description="id of person")

    def permissions(self):
        return [CanRead]
    
class UpdatePersonRequestAuth(RequestAuth):
    person_id: GenericUUID = Field(..., description="id of person")
    
    first_name: Optional[str] = Field(default=None, description="First name of the person")
    last_name: Optional[str] = Field(default=None, description="Last name of the person")
    full_name: str = Field(..., description="Full name of the person")
    identification: Optional[str] = Field(default=None, description="Identification document number")
    status: Optional[str] = Field(default="active", description="Current status of the person")
    pronoun: Optional[str] = Field(default=None, description="Pronoun used by the person")
    social_name: Optional[str] = Field(default=None, description="Social name of the person")
    birth_date: Optional[DateTime] = Field(default=None, description="Date of birth")
    doc: Optional[str] = Field(default=None, description="Additional document information")
    reg_doc: Optional[str] = Field(default=None, description="Registration document")
    passport: Optional[str] = Field(default=None, description="Passport number")
    birth_place: Optional[str] = Field(default=None, description="Place of birth")
    blood_type: Optional[str] = Field(default=None, description="Blood type")
    medical_agreement: Optional[str] = Field(default=None, description="Medical agreement or insurance information")
    weight: Optional[float] = Field(default=0.0, ge=0, description="Weight in kilograms")
    height: Optional[float] = Field(default=0.0, ge=0, description="Height in meters")
    shirt_size: Optional[str] = Field(default=None, description="Shirt size")
    shoe_size: Optional[int] = Field(default=None, ge=1, description="Shoe size")
    cba_card_code: Optional[str] = Field(default=None, description="CBA card code")
    cba_card_type_id: Optional[GenericUUID] = Field(default=None, description="Foreign key to CBA card type")
    fia_card: Optional[str] = Field(default=None, description="FIA card number")
    fia_card_type_id: Optional[GenericUUID] = Field(default=None, description="Foreign key to FIA card type")
    
    def permissions(self):
        return [CanUpdate]

class DeletePersonRequestAuth(RequestAuth):
    person_id: GenericUUID = Field(..., description="id of person")

    def permissions(self):
        return [CanDelete]
    
class GetPersonByDocRequestAuth(RequestAuth):
    doc: str = Field(..., description="Document number")

    @field_validator('doc', mode='before')
    @classmethod
    def doc_validator(cls, value: str) -> str:
        if value is None:
            return value
        return ''.join(filter(str.isdigit, str(value).strip()))

    def permissions(self):
        return [CanRead]