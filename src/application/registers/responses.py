from arcs_lib_pca.application import Response
from typing import Dict, Any, Optional

class GetRegisterResponse(Response):
    def load_links(self):
        if (self.body):
            self.insert_link(
                "POST",
                "/registers",
                "/",
                "Create new user"
            )

