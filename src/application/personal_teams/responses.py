from arcs_lib_pca.application import Response
from arcs_lib_pca.utils.string import to_snake_case

class PersonalTeamAllGetResponse(Response):

    def load_links(self):
        if self.body:
            personal_team = self.body
            members = personal_team.get('members', {})
            for member in members:
                pilot_id = member.get('pilot_id')

            self.insert_link("POST", "Create a new personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}",
                            "Create a member of personal_team data")


class PersonalTeamGetByIdResponse(Response):

    def load_links(self):
        personal_team = self.body
        member = personal_team.get('member', {})


        member_id = member.get('id')
        pilot_id = member.get('pilot_id')

        if member_id and pilot_id:
            self.insert_link("POST", "Create a new personal team from pilot",
                             f"/arcs_service/personal_teams/pilot/{pilot_id}",
                             "Create a member of personal_team data")

            self.insert_link("PUT", "Update a personal team from pilot",
                             f"/arcs_service/personal_teams/pilot/{pilot_id}/member/{member_id}",
                             "Update a member of personal_team data")

            self.insert_link("DELETE", "Delete a personal team from pilot",
                             f"/arcs_service/personal_teams/pilot/{pilot_id}/member/{member_id}",
                             "Delete a member of a personal_team data")


class PersonalTeamCreatedResponse(Response):

    def load_links(self):
        if 'id' in self.body:
            personal_team = self.body
            pilot_id = personal_team["pilot_id"]
            member_id = personal_team["member_id"]

            self.insert_link("POST", "Create a new personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}",
                            "Create a member of personal_team data")

            self.insert_link("PUT", "Update a personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}/member/{member_id}",
                            "Update a member of personal_team data")

            self.insert_link("DELETE", "Delete a personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}/member/{member_id}",
                            "Delete a member of a personal_team data")


class PersonalTeamUpdatedResponse(Response):

    def load_links(self):
        if 'id' in self.body:
            personal_team = self.body
            pilot_id = personal_team["pilot_id"]
            member_id = personal_team["member_id"]

            self.insert_link("POST", "Create a new personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}",
                            "Create a member of personal_team data")

            self.insert_link("PUT", "Update a personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}/member/{member_id}",
                            "Update a member of personal_team data")

            self.insert_link("DELETE", "Delete a personal team from pilot",
                            f"/arcs_service/personal_teams/pilot/{pilot_id}/member/{member_id}",
                            "Delete a member of a personal_team data")


class PersonalTeamDeletedResponse(Response):

    def load_links(self):
        pass

class UpdateMemberAcceptanceResponse(Response):

    def load_links(self):
        pass