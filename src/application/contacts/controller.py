from http import HTTPStatus
from arcs_lib_pca.application import BaseController

from src.application.contacts.requests import DeleteContactRequestAuth
from src.application.contacts.responses import DeleteContactResponse
from src.infrastructure.models import ContactModel


class ContactsController(BaseController):

    @BaseController.route(
        path="/<path:contact_id>",
        methods=["DELETE"],
        request=DeleteContactRequestAuth,
        response=DeleteContactResponse)
    def delete_contact(self, req: DeleteContactRequestAuth, resp: DeleteContactResponse):
        if req.has_errors():
            return resp(status_code=HTTPStatus.BAD_REQUEST, message="Invalid request")

        contact = self.load_repository(ContactModel).db.get_by_id(req.contact_id)

        if not contact:
            return resp(status_code=HTTPStatus.NOT_FOUND, message="Contact not found")

        self.load_repository(ContactModel).db.delete(id=req.contact_id)

        return resp(status_code=HTTPStatus.OK, message="Contact deleted")
