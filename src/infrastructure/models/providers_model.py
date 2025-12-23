from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId
from sqlalchemy.orm import relationship

class ProviderModel(PostgreSqlModel):
    __tablename__ = 'providers'
    __timestamp__ = True

    id = ColumnId()
    user_id = ColumnId(ForeignKey('users.id'), nullable=True, unique=False)
    user_guest_id = ColumnId(ForeignKey('user_guests.id'), nullable=True, unique=False)
    provider_name = Column(String, nullable=False)
    user_object_id = Column(String, nullable=True)
    group_object_id = Column(String, nullable=True)

    full_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    email_verified = Column(DateTime, nullable=True)
    picture_url = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True)

    user = relationship('UserModel', foreign_keys=[user_id], cascade="all, delete")
    user_guest = relationship('UserGuestModel', foreign_keys=[user_guest_id], cascade="all, delete")

    def __repr__(self):
        return (f"<AccountsProviderModel(id='{self.id}', user_id='{self.user_id}', "
                f"provider_name='{self.provider_name}')>")