import typing as t
from pydantic import Field, EmailStr, field_validator

from arcs_lib_pca.application import Request, RequestAuth
from arcs_lib_pca.tools.security.permissions import CanWrite, CanUpdate

class SendResetPasswordRequest(Request):
    email: EmailStr = Field(..., description="Email to send reset code")
    
    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()

    def permissions(self):
        return [CanWrite]

class ValidateCodeRequest(Request):
    email: EmailStr = Field(..., description="Email of the user")
    code: str = Field(..., min_length=4, max_length=4, description="4-digit reset code")
    
    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()
    def permissions(self):
        return [CanWrite]


class ResetPasswordAuthenticatedAuthRequest(RequestAuth):
    old_password: str = Field(..., description="Old password")
    new_password: str = Field(..., description="New password")

    def permissions(self):
        return [CanUpdate]

class ResetPasswordRequest(Request):
    email: EmailStr = Field(..., description="Email of the user")
    code: str = Field(..., min_length=4, max_length=4, description="4-digit reset code")
    new_password: str = Field(..., description="New password")
    
    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()
    
    def permissions(self):
        return [CanUpdate]

class ForceResetPasswordRequestAuth(RequestAuth):
    email: EmailStr = Field(..., description="Email of the user")
    new_password: str = Field(..., description="New password")

    @field_validator('email', mode='before')
    @classmethod
    def email_validator(cls, value: str) -> str:
        return str(value).lower().strip()

    def permissions(self):
        return [CanUpdate]