from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

class ProviderTokenModel(PostgreSqlModel):
    __tablename__ = 'provider_tokens'
    __timestamp__ = True

    id = ColumnId()
    user_id = ColumnId(ForeignKey('users.id'), nullable=False, unique=False)
    provider_id = ColumnId(ForeignKey('providers.id', ondelete='CASCADE'), nullable=False, unique=False)
    provider_access_token = Column(String, nullable=False)
    meta_data = Column(JSONB, nullable=True)
    provider_expiration = Column(DateTime, nullable=True)
    
    user = relationship('UserModel', foreign_keys=[user_id], cascade="all, delete")
    provider = relationship('ProviderModel', foreign_keys=[provider_id], cascade="all, delete")

    def __repr__(self):
        return (f"<ProviderTokenModel(id='{self.id}', user_id='{self.user_id}', "
                f"provider_access_token='{self.provider_access_token}')>")