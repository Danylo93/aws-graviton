from arcs_lib_pca.application import Response

class CreateInviteResponse(Response):
    def load_links(self):
        if self.body:
            self.insert_link(
                "POST",
                "/accounts/register",
                "/",
                "Create new user"
            )
            self.insert_link(
                "GET",
                "/accounts/register/{user_id}",
                "/",
                "Get details of user"
            )


class ResendInvitationResponse(Response):
    def load_links(self):
        return None
    
class GenerateInviteResponse(Response):
    def load_links(self):
        return None