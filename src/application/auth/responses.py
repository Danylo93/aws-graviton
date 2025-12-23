from arcs_lib_pca.application import Response
from typing import Dict, Any, Optional

class AuthResponse(Response):
    def load_links(self):
        return None
    
class RegisterProviderResponse(Response):
    def load_links(self):
        return None