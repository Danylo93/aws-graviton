from arcs_lib_pca.application import Response
from typing import Dict, Any, Optional

class AuthorizeGetResponse(Response):
    def load_links(self):
        self.insert_link(
            "GET",
            "/authorize/{provider_name}",
            "/",
            "Get a authorize of provider name"
        )