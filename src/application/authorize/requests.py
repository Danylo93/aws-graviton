from pydantic import Field
from arcs_lib_pca.application import Request

class GetAuthorizeRequest(Request):
    provider_name: str = Field(..., description="name of provider")
