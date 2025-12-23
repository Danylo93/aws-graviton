import bcrypt
import typing as t

from pydantic import EmailStr
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from arcs_lib_pca.infrastructure.model import PostgreSqlModel, ColumnId

class UserModel(PostgreSqlModel):
    __tablename__ = 'users'
    __timestamp__ = True
    __private_fields__ = ['salt', 'password']

    id = ColumnId()
    email = Column(String, nullable=False, unique=True)
    salt = Column(String, nullable=False)
    password = Column(String, nullable=False)
    meta_data = Column(JSONB, nullable=True)
    email_verified = Column(DateTime(timezone=True), nullable=True)
    person_id = Column(ForeignKey('people.id'), nullable=False)

    person = relationship('PersonModel', foreign_keys=[person_id])
    providers = relationship("ProviderModel", back_populates='user', cascade="all, delete")

    @classmethod
    def hash_password(cls, password: str) -> t.Dict["salt": str, "password": str]:
        """Gera um hash seguro para a senha com bcrypt.

        Args:
            password (str): A senha a ser hasheada.

        Returns:
            t.Dict[salt:str, password:str]: 
            Um dicionário contendo o salt e o hash da senha.
        """

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        return {
            "salt": salt.decode('utf-8'),
            "password": hashed_password.decode('utf-8')
        }
        
    def set_password(self, password: str) -> 'UserModel':
        hash = self.hash_password(password)
        self.salt = hash['salt']
        self.password = hash['password']
        return self

    def verify_password(self, password: str) -> bool:
        """
        Verifica a senha fornecida em comparação com o hash armazenado no banco de dados.

        Args:
            password (str): A senha a ser verificada.

        Returns:
            bool: True se a senha estiver correta, False caso contrário.
        """
        return bool(bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8')))
    
    def set_email(self, email: EmailStr):
        self.email = email

    def __repr__(self):
        return (f"<UserModel(id='{self.id}', email='{self.email}', "
                f"created_at='{self.created_at}', email_verified='{self.email_verified}')>")
