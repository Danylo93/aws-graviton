from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.domain import GenericUUID
from arcs_lib_pca.tools.security.permissions import CanDelete
from pydantic import Field


class DeleteAddressRequestAuth(RequestAuth):
    address_id: GenericUUID = Field(..., title="Address ID")

    def permissions(self):
        return [CanDelete]

