from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.domain import GenericUUID
from arcs_lib_pca.tools.security.permissions import CanDelete
from pydantic import Field


class DeleteContactRequestAuth(RequestAuth):
    contact_id: GenericUUID = Field(..., title="Contact ID")

    def permissions(self):
        return [CanDelete]