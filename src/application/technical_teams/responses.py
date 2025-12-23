from arcs_lib_pca.application import Response
from arcs_lib_pca.utils.string import to_snake_case

class TechnicalTeamGetResponse(Response):

    def load_links(self):
        self.insert_link("POST", "Create a new technical_team",
                         f"/arcs_service/technical_teams", "Create technical_team data")


class TechnicalTeamGetByIdResponse(Response):

    def load_links(self):
        if 'id' in self.body:
                technical_team = self.body
                id = technical_team["id"]

                self.insert_link("POST", "Create a new technical_team",
                                f"/arcs_service/technical_teams", "Create technical_team data")

                self.insert_link("UPDATE", "Update technical_team",
                                f"/arcs_service/technical_teams/{id}", "Update technical_team data")

                self.insert_link("DELETE", "Delete technical_team",
                                f"/arcs_service/technical_teams/{id}", "Delete technical_team")


class TechnicalTeamCreatedResponse(Response):

    def load_links(self):
        if 'id' in self.body:
            technical_team = self.body
            id = technical_team["id"]

            self.insert_link("GET", "Get technical_teams by id",
                             f"/arcs_service/technical_teams/{id}", "Get technical teams by id")

            self.insert_link("UPDATE", "Update technical_team",
                             f"/arcs_service/technical_teams/{id}", "Update technical_team data")

            self.insert_link("DELETE", "Delete technical_team",
                             f"/arcs_service/technical_teams/{id}", "Delete technical_team")


class TechnicalTeamUpdatedResponse(Response):

    def load_links(self):
        if 'id' in self.body:
            technical_team = self.body
            id = technical_team["id"]

            self.insert_link("POST", "Create a new technical_team",
                            f"/arcs_service/technical_teams", "Create technical_team data")

            self.insert_link("GET", "Get technical_teams by id",
                            f"/arcs_service/technical_teams/{id}", "Get technical teams by id")

            self.insert_link("DELETE", "Delete technical_team",
                                f"/arcs_service/technical_teams/{id}", "Delete technical_team")


class TechnicalTeamDeletedResponse(Response):

    def load_links(self):
        self.insert_link("GET", "Get all technical_teams",
                          f"/arcs_service/technical_teams", "Get all technical teams")

        self.insert_link("POST", "Create a new technical_team",
                         f"/arcs_service/technical_teams", "Create technical_team data")

class DeleteByPilotIDAndEngineerIDResponse(Response):
    def load_links(self):
        return None