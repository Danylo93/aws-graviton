from arcs_lib_pca.application import Response
from typing import Dict, Any, Optional

class GetProfileResponse(Response):
    def load_links(self):
        self.insert_link(
            "GET",
            "/profiles",
            "/",
            "Get list of profiles in system"
        )

class GetUniqueProfileResponse(Response):
    def load_links(self):
        self.insert_link(
            "GET",
            "/profiles",
            "/",
            "Get list of profiles in system"
        )

class UpdateProfileResponse(Response):
    def load_links(self):
        if self.body:
            id = self.body.get('id')
            

            self.insert_link(
                "GET",
                f'/profiles',
                '/',
                'Get data of all profiles registered'
            )

            if id:
                self.insert_link(
                    "GET",
                    f'/profiles/{id}',
                    '/',
                    'Get data of profile by ID'
                )

                self.insert_link(
                    "PUT",
                    f'/profiles/{id}',
                    '/',
                    'Update data of profile by ID'
                )

class DeleteProfileResponse(Response):
    def load_links(self):
        return None
    
class GenerateTokenResponse(Response):
    def load_links(self):
        pass

class DeleteProfilePictureResponse(Response):
    def load_links(self):
        return None