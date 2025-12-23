from http import HTTPStatus

from arcs_lib_pca.application import BaseController

from src.application.addresses.requests import DeleteAddressRequestAuth
from src.application.addresses.responses import DeleteAddressResponse
from src.infrastructure.models import AddressModel


class AddressesController(BaseController):

    @BaseController.route(
        path="/<path:address_id>",
        methods=["DELETE"],
        request=DeleteAddressRequestAuth,
        response=DeleteAddressResponse)
    def delete_address(self, req: DeleteAddressRequestAuth, resp: DeleteAddressResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        contact = self.load_repository(AddressModel).db.get_by_id(req.address_id)

        if not contact:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Address not found")

        self.load_repository(AddressModel).db.delete(id=req.address_id)

        return resp(status_code=HTTPStatus.OK, message="Address deleted")