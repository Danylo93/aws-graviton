import typing as t

from arcs_lib_pca.infrastructure.repository import Repositories
from pydantic import EmailStr

from src.infrastructure.models import UserModel


def get_user_by_email(user_repository: Repositories[type[UserModel]], email: EmailStr) -> t.Optional[UserModel]:
    user = user_repository.db.get_by(email=email)

    if not user:
        user = user_repository.db.get_by(
            filters=[UserModel.meta_data['emails'].contains([{"email": email}])])

    return user