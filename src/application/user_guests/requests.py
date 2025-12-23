from pydantic import Field

from arcs_lib_pca.application import Request
from arcs_lib_pca.tools.security.permissions import CanRead
from arcs_lib_pca.domain.value_objects import GenericUUID


class GetUserGuestRequest(Request):
    user_guest_id: GenericUUID = Field(..., description="id of user guest")
    
    def permissions(self):
        return [CanRead]
    