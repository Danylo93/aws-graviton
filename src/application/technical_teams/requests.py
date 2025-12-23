import typing as t

from pydantic import Field, BaseModel
from arcs_lib_pca.domain.value_objects import GenericUUID, DateTime
from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanRead, CanUpdate, CanDelete, CanWrite


class GetAllTechnicalTeamsRequestAuth(RequestAuth):
    page: int = Field(default=1, ge=1, description="page")
    per_page: int = Field(default=10, ge=1, description="per_page")

    def permissions(self):
        return [CanRead]


class GetTechnicalTeamByIDRequestAuth(RequestAuth):
    technical_team_id: GenericUUID = Field(..., description="id of technical team")

    def permissions(self):
        return [CanRead]


class DeleteTechnicalTeamByIDRequestAuth(RequestAuth):
    technical_team_id: GenericUUID = Field(..., description="id of technical team")

    def permissions(self):
        return [CanDelete]


class CreateTechnicalTeamRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="ID of the pilot")
    mechanic_id: t.Optional[GenericUUID] = Field(None, description="ID of the mechanic")
    engineer_id: t.Optional[GenericUUID] = Field(None, description="ID of the engineer")

    def permissions(self):
        return [CanWrite]

class TechnicalTeamVO(BaseModel):
    pilot_id: GenericUUID = Field(..., description="ID of the pilot")
    mechanic_id: t.Optional[GenericUUID] = Field(None, description="ID of the mechanic")
    engineer_id: t.Optional[GenericUUID] = Field(None, description="ID of the engineer")

class CreateManyTechnicalTeamRequestAuth(RequestAuth):
    teams: t.List[TechnicalTeamVO] = Field(..., description="Teams")

    def permissions(self):
        return [CanWrite]

class UpdateTechnicalTeamRequestAuth(RequestAuth):
    technical_team_id: GenericUUID = Field(..., description="id of technical team")

    pilot_id: GenericUUID = Field(..., description="ID of the pilot")
    mechanic_id: t.Optional[GenericUUID] = Field(None, description="ID of the mechanic")
    engineer_id: t.Optional[GenericUUID] = Field(None, description="ID of the engineer")

    def permissions(self):
        return [CanUpdate]

class DeleteByPilotIDAndEngineerIDRequestAuth(RequestAuth):
    pilot_id: GenericUUID = Field(..., description="ID of the pilot")
    engineer_id: GenericUUID = Field(..., description="ID of the engineer")

    def permissions(self):
        return [CanDelete]