from enum import Enum
import typing as t
from http import HTTPStatus

from pydantic import BaseModel, Field, field_validator

from arcs_lib_pca.utils.string import to_snake_case
from arcs_lib_pca.domain.value_objects import (
    File,
    DateTime,
    GenericUUID,
    AccessProfile,
    ProfilePermissions,
    ProfilePicture as ProfilePictureVO,
    BasePermissions,
    EmailStr
)
from arcs_lib_pca.infrastructure.repository.redis_repository import RedisRepository

class DefaultSubgroupNameEnum(Enum):
    MAIN_PILOT = 'main_pilot'

class DashboardLabelsPilotsPerStage(BaseModel):
    stage_id: GenericUUID = Field(default=None, description="Id of stage")
    stage_name: str = Field(default=None, description="Name of stage")

    def to_dict(self) -> dict:
        return {
            "stage_id": str(self.stage_id),
            "stage_name": self.stage_name
        }

class DashboardDataPilotsPerStage(BaseModel):
    total_pilots: int = Field(default=0, description="Total of pilots")
    total_cars: int = Field(default=0, description="Total of cars")

    def to_dict(self) -> dict:
        return {
            "total_pilots": self.total_pilots,
            "total_cars": self.total_cars
        }

class DashboardPilotsPerStageResponse(BaseModel):
    labels: t.List[DashboardLabelsPilotsPerStage] = Field(default=[], description="List of labels")
    data: t.List[DashboardDataPilotsPerStage] = Field(default=[], description="List of data")

    def process_totals(self, service_pagination: dict) -> t.Self:
        """
        Process the totals of pilots per cars per stage from the response of the service

        :param service_pagination: The response of the service
        :type service_pagination: dict
        :return: None
        :rtype: None
        """

        if "data" in service_pagination:
            service_data = service_pagination["data"]

        if service_data and ("totalItems" in service_data) and service_data["totalItems"] > 0:
            fields_required = ["stage_id", "stage_name", "total_pilots", "total_cars"]

            for item in service_data["items"]:
                if item and all(field in item for field in fields_required):
                    self.labels.append(DashboardLabelsPilotsPerStage(stage_id=item["stage_id"], stage_name=item["stage_name"]))
                    self.data.append(DashboardDataPilotsPerStage(total_pilots=item["total_pilots"], total_cars=item["total_cars"]))
        return self
    def to_dict(self) -> dict:
        return {
            "labels": [label.to_dict() for label in self.labels],
            "data": [d.to_dict() for d in self.data],
        }
class DashboardShipmentsResponse(BaseModel):
    labels: t.List[str] = Field(default=[], description="List of labels")
    data: t.List[int] = Field(default=[], description="List of data")

    def to_dict(self) -> dict:
        return {
            "labels": self.labels,
            "data": self.data
        }

class DashboardDataShipmentsStatus(BaseModel):
    id: GenericUUID = Field(default=None, description="Id of shipment")
    type: str = Field(default=None, description="Type of shipment")
    pilot: dict = Field(default=None, description="Pilot of shipment")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.type,
            "pilot": self.pilot
        }

class DashboardPendingShipmentsResponse(BaseModel):
    total_items: int = Field(default=0, description="Total of items")
    data: t.List[DashboardDataShipmentsStatus] = Field(default=[], description="List of data")

    def to_dict(self) -> dict:
        return {
            "total_items": self.total_items,
            "data": [d.to_dict() for d in self.data if isinstance(d, DashboardDataShipmentsStatus)]
        }

class DashboardDataShipmentsResponse(BaseModel):
    total_items: int = Field(default=0, description="Total of items")
    total_realized: int = Field(default=0, description="Total of realized items")
    total_outstanding: int = Field(default=0, description="Total of outstanding items")
    data: t.List[DashboardDataShipmentsStatus] = Field(default=[], description="List of data")

    # Função para processar status
    def process_status(self, redis: RedisRepository, service_pagination: dict, service_type: str, field_status: str) -> t.Self:
        """
        Processes the status of items from the service pagination data and updates
        shipment statistics accordingly.

        This method iterates over items in the `service_pagination` data to determine
        their status based on the `field_status` field. It updates the total count of
        items, realized items, and outstanding items while appending relevant shipment
        data to the `data` attribute.

        Args:
            redis (RedisRepository): Instance of RedisRepository to fetch AccessProfile
                details when needed.
            service_pagination (dict): Dictionary containing paginated service data
                including items and their statuses.
            service_type (str): Type of service related to the shipment.
            field_status (str): Key within each item to check for status keywords.

        Updates:
            - Increments `self.total_items` by the number of items in `service_pagination`.
            - Increments `self.total_realized` for items with a status matching any
            of the predefined keywords.
            - Appends to `self.data` with items having outstanding status, including
            details about the shipment and pilot.
        """

        keywords = ["completed", "sent", "finalized", "concluído", "enviado", "finalizado", "finalizada"]

        if "data" in service_pagination:
            service_data = service_pagination["data"]

        if service_data and ("totalItems" in service_data) and service_data["totalItems"] > 0:
            self.total_items += service_data["totalItems"]

            for item in service_data["items"]:
                if field_status not in item:
                    continue

                status = str(item[field_status]).lower()
                if any(key in status for key in keywords):
                    self.total_realized += 1
                else:
                    pilot = None

                    if "pilot" in item:
                        pilot = item["pilot"]
                    elif "pilot_id" in item:
                        pilot = AccessProfile.get_of_redis(redis, item["pilot_id"]).to_dict()
                    elif "profile" in item:
                        pilot = item["profile"]
                    elif "profile_id" in item:
                        pilot = AccessProfile.get_of_redis(redis, item["profile_id"]).to_dict()
                    else:
                        continue

                    self.total_outstanding += 1
                    self.data.append(
                        DashboardDataShipmentsStatus(
                            id = item["id"],
                            type = service_type,
                            pilot = pilot
                        )
                    )

        return self

    def to_dict(self) -> dict:
        return {
            "total_items": self.total_items,
            "total_realized": self.total_realized,
            "total_outstanding": self.total_outstanding,
            "data": [d.to_dict() for d in self.data if isinstance(d, DashboardDataShipmentsStatus)]
        }

class DashboardResponse(BaseModel):
    total_pilots: int = Field(default=0, description="Total of pilots")
    total_stages: int = Field(default=0, description="Total of stages")
    total_cars: int = Field(default=0, description="Total of cars")
    total_users: int = Field(default=0, description="Total of users")
    shipments: DashboardShipmentsResponse = Field(default={}, description="Shipment data")
    pilots_per_stage: DashboardPilotsPerStageResponse = Field(default={}, description="Pilots per stage")
    pending_shipments: DashboardPendingShipmentsResponse = Field(default={}, description="Pending shipments data")

    def to_dict(self) -> dict:
        return {
            "total_pilots": self.total_pilots,
            "total_stages": self.total_stages,
            "total_cars": self.total_cars,
            "total_users": self.total_users,
            "shipments": self.shipments.to_dict() if isinstance(self.shipments, DashboardShipmentsResponse) else {},
            "pilots_per_stage": self.pilots_per_stage.to_dict() if isinstance(self.pilots_per_stage, DashboardPilotsPerStageResponse) else {},
            "pending_shipments": self.pending_shipments.to_dict() if isinstance(self.pending_shipments, DashboardPendingShipmentsResponse) else {},
        }

class ErrorRegisterUserVO(BaseModel):
    email: EmailStr = Field(..., description="Email of user")

    @property
    def email_obfuscated(self) -> str:
        email_parts = self.email.split('@')
        username = email_parts[0]
        domain = email_parts[1]
        return f"{username[0]}****{username[-1]}@{domain[0]}*****{domain[-1]}"
    
    def to_dict(self) -> dict:
        return {
            "email": self.email_obfuscated
        }

class ResponseRegisterUseCase(BaseModel):
    http_status: t.Union[int, HTTPStatus] = Field(..., description="HTTP status code")
    data: t.Optional[AccessProfile] | t.Dict = Field(default=None, description="Access profile")
    message: str = Field(..., min_length=1, description="Error message")

class PersonBase(BaseModel):
    full_name: str = Field(..., description="Full name of the person", min_length=2) #TODO: campo obrigatorio
    first_name: t.Optional[str] = Field(None, description="First name of the person", min_length=1) #TODO: campo obrigatorio
    last_name: t.Optional[str] = Field(None, description="Last name of the person", min_length=1) #TODO: campo obrigatorio

    cellphone: t.Optional[str] = Field(default=None, description="Cellphone number of the person")
    identification: t.Optional[str] = Field(default=None, description="Identification document number")
    status: t.Optional[str] = Field(default="active", description="Current status of the person")
    pronoun: t.Optional[str] = Field(default=None, description="Pronoun used by the person")
    social_name: t.Optional[str] = Field(default=None, description="Social name of the person")
    birth_date: t.Optional[str] = Field(default=None, description="Date of birth")
    doc: t.Optional[str] = Field(default=None, description="Additional document information")
    reg_doc: t.Optional[str] = Field(default=None, description="Registration document")
    passport: t.Optional[str] = Field(default=None, description="Passport number")
    birth_place: t.Optional[str] = Field(default=None, description="Place of birth")
    blood_type: t.Optional[str] = Field(default=None, description="Blood type")
    medical_agreement: t.Optional[str] = Field(default=None, description="Medical agreement or insurance information")
    weight: t.Optional[float] = Field(default=0.0, ge=0, description="Weight in kilograms")
    height: t.Optional[float] = Field(default=0.0, ge=0, description="Height in meters")
    shirt_size: t.Optional[str] = Field(default=None, description="Shirt size")
    shoe_size: t.Optional[int] = Field(default=None, ge=1, description="Shoe size")
    cba_card_code: t.Optional[str] = Field(default=None, description="CBA card code")
    cba_card_type_id: t.Optional[GenericUUID] = Field(default=None, description="Foreign key to CBA card type")
    fia_card: t.Optional[str] = Field(default=None, description="FIA card number")
    fia_card_type_id: t.Optional[GenericUUID] = Field(default=None, description="Foreign key to FIA card type")

    @staticmethod
    def field_is_empty(value):
        if isinstance(value, str):
            if value.strip() == '':
                return False
            return True
        return False

    @classmethod
    @field_validator('full_name', mode='before')
    def validate_fullname(cls, value):
        if not cls.field_is_empty(value):
            return value
        return None

    @classmethod
    @field_validator('first_name', mode='before')
    def validate_first_name(cls, value):
        if not cls.field_is_empty(value):
            return value
        return None

    @classmethod
    @field_validator('last_name', mode='before')
    def validate_last_name(cls, value):
        if not cls.field_is_empty(value):
            return value
        return None
    
    @field_validator('doc', mode='before')
    @classmethod
    def doc_validator(cls, value: str) -> str:
        if value is None:
            return value
        return ''.join(filter(str.isdigit, str(value).strip()))

    def to_dict(self) -> dict:
        return self.model_dump()

class BasePermission(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the service or controller")
    get: bool = Field(True, description="Indicates if GET method is supported")
    post: bool = Field(False, description="Indicates if POST method is supported")
    put: bool = Field(False, description="Indicates if PUT method is supported")
    delete: bool = Field(False, description="Indicates if DELETE method is supported")

    @field_validator('name', mode='before')
    def transform_name_to_snake_case(cls, name: str) -> str:
        """
        Valida e transforma o campo 'name' para o formato snake_case.
        """
        if name:
            return to_snake_case(name)
        return name

    def to_vo(self) -> BasePermissions:
        return BasePermissions(
            name=self.name,
            delete=self.delete,
            get=self.get,
            post=self.post,
            put=self.put
        )

    def to_dict(self) -> dict:
        return self.model_dump()

class ProfilePermission(BaseModel):
    service: BasePermission = Field(..., description="Microservice access permissions")
    controllers: t.List[BasePermission] = Field(..., description="List of controllers identified by their namespace and respective access rules")

    def to_vo(self,
        profile_name: str,
        profile_id: GenericUUID,
        created_at: DateTime,
        created_by: GenericUUID,
        updated_at: t.Optional[DateTime] = None,
        updated_by: t.Optional[GenericUUID] = None,
        deleted_at: t.Optional[DateTime] = None,
        deleted_by: t.Optional[GenericUUID] = None
    ) -> ProfilePermissions:
        return ProfilePermissions(
            id=profile_id,
            name=profile_name,
            service=self.service.to_vo(),
            controllers=[ctr.to_vo() for ctr in self.controllers],
            created_at=created_at,
            created_by=created_by,
            deleted_at=deleted_at,
            deleted_by=deleted_by,
            updated_at=updated_at,
            updated_by=updated_by
        )

    def to_dict(self):
        return {
            "service": self.service.to_dict(),
            "controllers": [ctr.to_dict() for ctr in self.controllers]
        }

    def is_service(self, service_name: str) -> bool:
        return service_name == self.service.name

    def has_controller(self, controller_name: str) -> bool:
        return any(ctr.name == controller_name for ctr in self.controllers)

class ProfilePicture(BaseModel):
    key: str = Field(default="default", min_length=1, description="Key to identify profile image")
    image: File = Field(..., description="Image of profile")

    def to_vo(self) -> ProfilePictureVO:
        return ProfilePictureVO(
            id=self.image.id,
            url=self.image
        )

    def to_dict(self) -> t.Dict[str, ProfilePictureVO]:
        return {self.key: self.to_vo().to_dict()}

class GroupPermission(BaseModel):
    app_clients: t.List[BasePermission] = Field(..., description="Permission by app_client")

    def to_dict(self) -> dict:
        return {
            "app_clients": [perm.to_dict() for perm in self.app_clients]
        }

class SubGroupPermission(BaseModel):
    service: BasePermission = Field(..., description="Microservice access permissions")
    controllers: t.List[BasePermission] = Field(..., description="List of controllers identified by their namespace and respective access rules")

class ContactsRequest(BaseModel):
    id: t.Optional[GenericUUID] = Field(default=None, description="Unique Identificator")
    contact_type_id: t.Optional[GenericUUID] = Field(default=None, description="Id of contact type")
    contact_type_name: t.Optional[str] = Field(default=None, description="Name of contact type")
    name: str = Field(..., min_length=1, description="Name of contact")
    value: str = Field(..., min_length=1, description="Value of contact")
    is_emergency: t.Optional[bool] = Field(default=False, description="Emergency contact")
    is_main: t.Optional[bool] = Field(default=False, description="Main contact")
    is_verified: t.Optional[DateTime] = Field(default=None, description="Verified contact")

    def to_dict(self) -> dict:
        return self.model_dump()

class ProfileRequest(BaseModel):
    id: t.Optional[GenericUUID] = Field(default=None, description="Unique Identificator")
    description: t.Optional[str] = Field(default=None, description="Description of profile")
    pictures: t.Optional[t.Dict[str, File]] = Field(default={}, description="key and image of profile")
    permissions: t.Optional[t.List[ProfilePermission]] = Field(default=None, description="permissions of profile")

class AddressRequest(BaseModel):
    id: t.Optional[GenericUUID] = Field(default=None, description="Unique Identificator")
    cep: str = Field(..., min_length=1, description="The postal code (CEP) for the address.")
    address: str = Field(..., min_length=1, description="The street name and number of the address.")
    code_address: t.Optional[str] = Field(default=None, min_length=1, description="A unique code or identifier for the address.")
    neighborhood: t.Optional[str] = Field(default=None, min_length=1, description="The neighborhood where the address is located.")
    city: str = Field(..., min_length=1, description="The city where the address is situated.")
    state: str = Field(..., min_length=1, description="The state or province where the address is located.")
    country: str = Field(..., min_length=1, description="The country where the address is situated.")
    address_complement: t.Optional[str] = Field(None, max_length=100, description="Additional information about the address, such as apartment number or building name.")

    @classmethod
    @field_validator('address_complement')
    def no_blank_string(cls, value):
        if value is not None and value.strip() == "":
            return value
        return None

class UserData(BaseModel):
    email: t.Optional[str] = Field(None, description="User email")
    person: dict = Field(..., description="Person model of user")
    profile: dict = Field(..., description="Profile model of user")
    access_profile: t.Optional[dict] = Field(default=None, description="AccessProfile of this profile model")
    contacts: t.List[dict] = Field(..., description="All contacts of this person")
    addresses: t.List[dict] = Field(..., description="All addresses of this person")
    pilot: dict = Field({}, description="Pilot data")
    config: dict = Field(..., description="Config model of this profile model")

class KeyContactRole(BaseModel):
    id: t.Optional[GenericUUID] = Field(None, description="id of role")
    name: str = Field(..., description="name", min_length=1)
 
class ProfileVO(BaseModel):
    id: GenericUUID = Field(..., description="")
    person_id: GenericUUID = Field(..., description="")
    subgroup_id: GenericUUID = Field(..., description="")
    description: str = Field(..., description="")
    pictures: t.Optional[t.Dict[str, File]] = Field({}, description="")
    permissions: t.List[ProfilePermission] = Field(..., description="")
    last_access: DateTime = Field(..., description="")
    name: str = Field(..., description="")
    subgroup_name : str = Field(..., description="")
    group_name : str = Field(..., description="")
    email: EmailStr = Field(..., description="")

    def to_dict(self):
        return {
            "id": str(self.id),
            "subgroup_name": self.subgroup_name,
            "group_name": self.group_name,
            "email": str(self.email),
            "name": self.name,
            "person_id": str(self.person_id),
            "subgroup_id": str(self.subgroup_id),
            "description": self.description,
            "pictures": self.pictures,
            "last_access": self.last_access,
            "permissions": self.permissions
        }

class PilotStatusEnum(Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'

class MetaDataEmailVO(BaseModel):
    email: EmailStr = Field(..., description="Email of user")
    is_verified: bool = Field(default=False, description="Verified email")

    def to_dict(self):
        return {
            "email": str(self.email),
            "is_verified": self.is_verified
        }

class UserMetadataVO(BaseModel):
    emails: t.List[MetaDataEmailVO] = Field(default=[], description="")

    def to_dict(self):
        return {
            "emails": [email.to_dict() for email in self.emails]
        }

class UserEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Email of user")
    is_main: bool = Field(..., description="Set as main email")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()\

class ErrorVO(BaseModel):
    status: t.Union[int, HTTPStatus] = Field(..., description="HTTP status code")
    message: str = Field(..., min_length=1, description="Error message")