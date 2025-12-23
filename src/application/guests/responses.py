from arcs_lib_pca.application import Response
from typing import Dict, Any, List, Optional

class GetGuestResponse(Response):
    def load_links(self):
        self.insert_link(
            "GET",
            "/accounts/guests",
            "/",
            "List of all request guests"
        )


class GetAllResponse(Response):
    def load_links(self):
        self.insert_link(
            "GET",
            "/accounts/guests",
            "/",
            "Create invite from guest"
        )