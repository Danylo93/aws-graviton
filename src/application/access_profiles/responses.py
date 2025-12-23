from arcs_lib_pca.application import Response
from typing import Dict, Any, Optional

class AccessProfileAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for access_profile in self.body["items"]:
                if hasattr(access_profile, 'name'):
                    self.insert_link("PUT", "atualizar_access_profile", f"/arcs/access_profiles/{access_profile.name}", "Atualizar access_profile")

class AccessProfileGetResponse(Response):

    def load_links(self):
        if 'name' in self.body:
            self.insert_link("PUT", "atualizar_access_profile", f"/arcs/access_profiles/{self.body['name']}", "Atualizar access profile")

class GetAccessProfilesByUserIDResponse(Response):
    def load_links(self):
        ...