from typing import Self, Optional

from sqlalchemy import Column, ForeignKey, String, DateTime, func, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from arcs_lib_pca.domain import DateTime as DateTimeVo, ProfilePicture, ProfilePermissions, File

class ProfileModel(PostgreSqlModel):
    __tablename__ = 'profile'
    __timestamp__ = True

    id = ColumnId()
    description = Column(String, nullable=True)
    pictures = Column(JSONB, nullable=True)
    permissions = Column(JSONB, nullable=True) #t.List[ProfilePermissions]
    person_id = ColumnId(ForeignKey('people.id'), nullable=False, unique=False)
    subgroup_id = ColumnId(ForeignKey('subgroups.id'), nullable=False, unique=False)
    last_access = Column(DateTime(timezone=True), nullable=True)

    person = relationship('PersonModel', back_populates="profiles", foreign_keys=[person_id], cascade="all, delete")

    subgroup = relationship('SubGroupModel', back_populates="profiles", foreign_keys=[subgroup_id], cascade="all, delete")

    def __repr__(self):
        return f"<ProfileModel(id='{self.id}', description='{self.description}')>"

    def stamp_access(self) -> Self:
        self.last_access = DateTimeVo.now()
        return self

    def set_picture(self, key: str, image: File ) -> Self:
        pictures = self.pictures or {}
        
        pictures[key] = ProfilePicture(id=image.id, url=image).to_dict()
        self.pictures = pictures
        return self
    
    def del_picture(self, key: str) -> Self:
        pictures = self.pictures
        
        if key in pictures:
            del pictures[key]

        self.pictures = pictures
        return self
    
    def get_permission_by_service(self, service_name: str) -> Optional[ProfilePermissions]:
        if not self.permissions:
            return None

        return next((ProfilePermissions(**perm) for perm in self.permissions if perm['service']['name'] == service_name), None)
        

