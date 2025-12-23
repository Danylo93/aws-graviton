import typing as t
from http import HTTPStatus

from arcs_lib_pca.application import BaseController, Response
from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from pydantic import BaseModel, Field
from src.infrastructure.models import TechnicalTeamModel, AccessProfileModel
from arcs_lib_pca.domain import GenericUUID

from .requests import(
    GetAllTechnicalTeamsRequestAuth,
    GetTechnicalTeamByIDRequestAuth,
    DeleteTechnicalTeamByIDRequestAuth,
    CreateTechnicalTeamRequestAuth,
    CreateManyTechnicalTeamRequestAuth,
    UpdateTechnicalTeamRequestAuth,
    DeleteByPilotIDAndEngineerIDRequestAuth
)

from .responses import(
    TechnicalTeamGetByIdResponse,
    TechnicalTeamCreatedResponse,
    TechnicalTeamDeletedResponse,
    TechnicalTeamUpdatedResponse,
    TechnicalTeamGetResponse,
    DeleteByPilotIDAndEngineerIDResponse
)

class UpsertTechnicalTeamResponse(BaseModel):
    model: t.Optional[t.Dict[str, t.Any]] = Field(None)
    status_code: HTTPStatus = Field(...)
    message: str = Field(...)

class TechnicalTeamController(BaseController):

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllTechnicalTeamsRequestAuth,
        response=TechnicalTeamGetResponse)
    def get_all_technical_teams(self, req: GetAllTechnicalTeamsRequestAuth, resp: TechnicalTeamGetResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        technical_team_repo = self.load_repository(TechnicalTeamModel)
        subquery = QueryParamsUseCase.load(req.params)
        technical_team = technical_team_repo.db.with_query(subquery).paginate(
            page=req.page, 
            per_page=req.per_page, 
            load=['mechanic', 'engineer', 'pilot']
        )

        return resp(HTTPStatus.OK, technical_team, message='Sucessfully')

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateTechnicalTeamRequestAuth,
        response=TechnicalTeamCreatedResponse)
    def create_new_technical_team(self, req: CreateTechnicalTeamRequestAuth, resp: TechnicalTeamCreatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        response = self.upsert_technical_team(
            pilot_id=req.pilot_id,
            engineer_id=req.engineer_id,
            mechanic_id=req.mechanic_id
        )

        return resp(response.status_code, body=response.model or {}, message=response.message)
    
    @BaseController.route(
        path="/in_batch/",
        methods=["POST"],
        request=CreateManyTechnicalTeamRequestAuth,
        response=TechnicalTeamCreatedResponse)
    def create_in_batch_technical_team(self, req: CreateManyTechnicalTeamRequestAuth, resp: TechnicalTeamCreatedResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")
        
        for team in req.teams:
            self.upsert_technical_team(
                pilot_id=team.pilot_id,
                engineer_id=team.engineer_id,
                mechanic_id=team.mechanic_id
            )

        return resp(HTTPStatus.OK, message="Sucessfully")

    @BaseController.route(
        path="/<path:technical_team_id>",
        methods=["GET"],
        request=GetTechnicalTeamByIDRequestAuth,
        response=TechnicalTeamGetByIdResponse)
    def get_technical_team_by_id(self, req: GetTechnicalTeamByIDRequestAuth, resp: TechnicalTeamGetByIdResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        technical_team_repo = self.load_repository(TechnicalTeamModel)
        technical_team = technical_team_repo.db.get_by_id(id=req.technical_team_id)

        if not technical_team:
            return resp(HTTPStatus.NOT_FOUND, message="Technical team not found")

        return resp(HTTPStatus.OK, 
                    technical_team.to_dict(lazy_load=["mechanic", "engineer", "pilot"]), 
                    message="Successfully"
                )

    @BaseController.route(
        path="/<path:technical_team_id>",
        methods=["PUT", "PATCH"],
        request=UpdateTechnicalTeamRequestAuth,
        response=TechnicalTeamUpdatedResponse)
    def update_technical_team_by_id(self, req: UpdateTechnicalTeamRequestAuth, resp: TechnicalTeamUpdatedResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        technical_team_repo = self.load_repository(TechnicalTeamModel)
        access_profile_repo = self.load_repository(AccessProfileModel)

        if not (tech_team_model := technical_team_repo.db.get_by_id(id=req.technical_team_id)):
            return resp(HTTPStatus.NOT_FOUND, message='Technical team not found')

        if not access_profile_repo.db.contains(profile_id=req.pilot_id):
            return resp(status_code=HTTPStatus.NOT_FOUND, message=f"Pilot profile not found")
        tech_team_model.pilot_id = req.pilot_id

        if req.mechanic_id and not access_profile_repo.db.contains(profile_id=req.mechanic_id):
            return resp(status_code=HTTPStatus.NOT_FOUND, message=f"Mechanic profile not found")
        tech_team_model.mechanic_id = req.mechanic_id

        if req.engineer_id and not access_profile_repo.db.contains(profile_id=req.engineer_id):
            return resp(status_code=HTTPStatus.NOT_FOUND, message=f"Enginner profile not found")
        tech_team_model.engineer_id = req.engineer_id

        technical_model = technical_team_repo.db.update_by_id(id=req.technical_team_id, data=tech_team_model)

        if not technical_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error while updated technical team")

        return resp(HTTPStatus.OK, technical_model.to_dict(), "Updated technical team successfully")


    @BaseController.route(
        path="/<path:technical_team_id>",
        methods=["DELETE"],
        request=DeleteTechnicalTeamByIDRequestAuth,
        response=TechnicalTeamDeletedResponse)
    def delete_technical_team_by_id(self, req: DeleteTechnicalTeamByIDRequestAuth, resp: TechnicalTeamDeletedResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        technical_team_repo = self.load_repository(TechnicalTeamModel)
        if not technical_team_repo.db.contains(id=req.technical_team_id):
            return resp(HTTPStatus.NOT_FOUND, message='Technical team not found')

        self.load_repository(TechnicalTeamModel).db.remove_by_id(id=req.technical_team_id)

        return resp(HTTPStatus.OK, message="Technical team deleted successfully")
    
    @BaseController.route(
        path="/technical_teams/engineer/<path:engineer_id>/pilot/<path:pilot_id>",
        methods=["DELETE"],
        request=DeleteByPilotIDAndEngineerIDRequestAuth,
        response=DeleteByPilotIDAndEngineerIDResponse)
    def delete_technical_team_by_pilot_id_and_engineer_id(self, req: DeleteByPilotIDAndEngineerIDRequestAuth, resp: DeleteByPilotIDAndEngineerIDResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Invalid request")

        technical_team_repo = self.load_repository(TechnicalTeamModel)
        if not technical_team_repo.db.contains(pilot_id=req.pilot_id, engineer_id=req.engineer_id):
            return resp(HTTPStatus.NOT_FOUND, message='Technical team not found')

        self.load_repository(TechnicalTeamModel).db.remove(
            pilot_id=req.pilot_id,
            engineer_id=req.engineer_id
        )

        return resp(HTTPStatus.OK, message="Technical team deleted successfully")
    
    def upsert_technical_team(self, pilot_id: GenericUUID, mechanic_id: GenericUUID, engineer_id: GenericUUID) -> UpsertTechnicalTeamResponse:
        if not self.load_repository(AccessProfileModel).db.contains(profile_id=pilot_id):
            return UpsertTechnicalTeamResponse(
                status_code=HTTPStatus.NOT_FOUND,
                message=f"Pilot profile not found"
            )

        if mechanic_id and not self.load_repository(AccessProfileModel).db.contains(profile_id=mechanic_id):
            return UpsertTechnicalTeamResponse(
                status_code=HTTPStatus.NOT_FOUND,
                message=f"Mechanic profile not found"
            )

        if engineer_id and not self.load_repository(AccessProfileModel).db.contains(profile_id=engineer_id):
            return UpsertTechnicalTeamResponse(status_code=HTTPStatus.NOT_FOUND, message=f"Enginner profile not found")

        data= {
            "pilot_id": pilot_id,
            "mechanic_id": mechanic_id,
            "engineer_id": engineer_id
        }

        technical_team_model : TechnicalTeamModel = self.load_repository(TechnicalTeamModel).db.get_by(pilot_id=pilot_id)

        if technical_team_model:
            technical_team_model = self.load_repository(TechnicalTeamModel).db.update_by_id(id=technical_team_model.id, data=data)

            if not technical_team_model:
                return UpsertTechnicalTeamResponse(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
                    message="Error while update technical team")

            return UpsertTechnicalTeamResponse(
                status_code=HTTPStatus.CREATED, 
                data=technical_team_model.to_dict(), 
                message="Created technical team successfully"
            )

        technical_team_model = self.load_repository(TechnicalTeamModel).db.add(data=data)

        if not technical_team_model:
            return UpsertTechnicalTeamResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                message="Error while creating technical team"
            )
        
        return UpsertTechnicalTeamResponse(
            model=technical_team_model.to_dict(),
            status_code=HTTPStatus.OK,
            message="Created successfully"
        )