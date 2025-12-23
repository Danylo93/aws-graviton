from http import HTTPStatus
from arcs_lib_pca.application import BaseController
from src.infrastructure.models import KeyContactModel, KeyContactRoleModel

from arcs_lib_pca.use_case.postgres import QueryParamsUseCase
from .requests import (
    GetAllKeyContactRequestAuth,
    CreateKeyContactRequestAuth,
    GetKeyContactRequestAuth,
    UpdateKeyContactRequestAuth,
    DeleteKeyContactRequestAuth,

    GetAllKeyContactRoleRequestAuth,
    CreateKeyContactRoleRequestAuth,
    UpdateKeyContactRoleRequestAuth,
    DeleteKeyContactRoleRequestAuth
)

from .responses import (
    GetAllKeyContactResponse,
    CreateKeyContactResponse,
    GetKeyContactResponse,
    UpdateKeyContactResponse,
    DeleteKeyContactResponse,

    GetAllKeyContactRoleResponse,
    CreateKeyContactRoleResponse,
    UpdateKeyContactRoleResponse,
    DeleteKeyContactRoleResponse
)

class KeyContactsController(BaseController):

    @BaseController.route(
        path="/",
        methods=["GET"],
        request=GetAllKeyContactRequestAuth,
        response=GetAllKeyContactResponse
    )
    def get_all_key_contacts(self, req: GetAllKeyContactRequestAuth, resp: GetAllKeyContactResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_repo = self.load_repository(KeyContactModel)
        subquery = QueryParamsUseCase.load(req.params)
        data = key_contact_repo.db.with_query(subquery).paginate(
            page=req.page,
            per_page=req.per_page,
            load=["role"]
        )

        return resp(HTTPStatus.OK, data, "Request Succefully")


    @BaseController.route(
        path="/",
        methods=["POST"],
        request=CreateKeyContactRequestAuth,
        response=CreateKeyContactResponse
    )
    def create_key_contact(self, req: CreateKeyContactRequestAuth, resp: CreateKeyContactResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_role_repo = self.load_repository(KeyContactRoleModel)
        key_contact_repo = self.load_repository(KeyContactModel)

        role = None

        if req.role.id:
            role = key_contact_role_repo.db.get_by_id(id=str(req.role.id))

        if not role:
            role = key_contact_role_repo.db.add({
                "name": req.role.name,
            })

        if not role:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Key Contact Role")

        key_contact_model = key_contact_repo.db.add({
            "name": req.name,
            "contact": req.contact,
            "role_id": role.id
        })

        if not key_contact_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Key Contact")

        return resp(HTTPStatus.CREATED, key_contact_model.to_dict(lazy_load=['role']), "Request Succefully")

    @BaseController.route(
        path="/<path:key_contact_id>",
        methods=["GET"],
        request=GetKeyContactRequestAuth,
        response=GetKeyContactResponse
    )
    def get_key_contact(self, req: GetKeyContactRequestAuth, resp: GetKeyContactResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_repo = self.load_repository(KeyContactModel)
        model = key_contact_repo.db.get_by_id(id=str(req.key_contact_id))

        if not model:
            return resp(HTTPStatus.NOT_FOUND, message="Key Contact not found")

        return resp(HTTPStatus.OK, model.to_dict(lazy_load=['role']), "Request Succefully")

    @BaseController.route(
        path="/<path:key_contact_id>",
        methods=["PUT"],
        request=UpdateKeyContactRequestAuth,
        response=UpdateKeyContactResponse
    )
    def update_key_contact(self, req: UpdateKeyContactRequestAuth, resp: UpdateKeyContactResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_role_repo = self.load_repository(KeyContactRoleModel)
        key_contact_repo = self.load_repository(KeyContactModel)

        key_contact_model = key_contact_repo.db.get_by_id(req.key_contact_id)

        if not key_contact_model:
            return resp(HTTPStatus.NOT_FOUND, message="Key Contact Not Found")

        role = None

        if req.role.id:
            role = key_contact_role_repo.db.get_by_id(id=str(req.role.id))

        if not role:
            role = key_contact_role_repo.db.add({
                "name": req.role.name,
            })

        if not role:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Key Contact Role")

        key_contact_model = key_contact_repo.db.update_by_id(
            id=req.key_contact_id,
            data={
                "name": req.name,
                "contact": req.contact,
                "role_id": role.id 
            }
        )

        if not key_contact_model:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Key Contact")

        return resp(HTTPStatus.OK, key_contact_model.to_dict(lazy_load=['role']), "Request Succefully")


    @BaseController.route(
        path="/<path:key_contact_id>",
        methods=["DELETE"],
        request=DeleteKeyContactRequestAuth,
        response=DeleteKeyContactResponse
    )
    def delete_key_contact(self, req: DeleteKeyContactRequestAuth, resp: DeleteKeyContactResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_repo = self.load_repository(KeyContactModel)

        if not key_contact_repo.db.contains(id=str(req.key_contact_id)):
            return resp(HTTPStatus.NOT_FOUND, message="Key Contact not found")

        key_contact_repo.db.delete(id=str(req.key_contact_id))

        return resp(HTTPStatus.OK, "Request Succefully")


    @BaseController.route(
        path="/roles/",
        methods=["GET"],
        request=GetAllKeyContactRoleRequestAuth,
        response=GetAllKeyContactRoleResponse
    )
    def get_all_key_contact_roles(self, req: GetAllKeyContactRoleRequestAuth, resp: GetAllKeyContactRoleResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_role_repo = self.load_repository(KeyContactRoleModel)
        subquery = QueryParamsUseCase.load(req.params)
        
        data = key_contact_role_repo.db.with_query(subquery).paginate(
            page=req.page,
            per_page=req.per_page
        )

        return resp(HTTPStatus.OK, data, "Request Succefully")

    @BaseController.route(
        path="/roles/",
        methods=['POST'],
        request=CreateKeyContactRoleRequestAuth,
        response=CreateKeyContactRoleResponse
    )
    def create_key_contact_role(self, req: CreateKeyContactRoleRequestAuth, resp: CreateKeyContactRoleResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_role_repo = self.load_repository(KeyContactRoleModel)
        role = key_contact_role_repo.db.add({
            "name": req.name,
        })

        if not role:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error creating Key Contact Role")

        return resp(HTTPStatus.CREATED, role.to_dict(), "Request Succefully")

    @BaseController.route(
        path="/roles/<path:key_contact_role_id>",
        methods=["PUT"],
        request=UpdateKeyContactRoleRequestAuth,
        response=UpdateKeyContactRoleResponse
    )
    def update_key_contact_role(self, req: UpdateKeyContactRoleRequestAuth, resp: UpdateKeyContactRoleResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_role_repo = self.load_repository(KeyContactRoleModel)

        if not key_contact_role_repo.db.contains(id=str(req.key_contact_role_id)):
            return resp(HTTPStatus.NOT_FOUND, message="Key Contact Role not found")

        role = key_contact_role_repo.db.update_by_id(id=str(req.key_contact_role_id), data={
            "name": req.name
        })

        if not role:
            return resp(HTTPStatus.INTERNAL_SERVER_ERROR, message="Error updating Key Contact Role")

        return resp(HTTPStatus.OK, role.to_dict(), "Request Succefully")

    @BaseController.route(
        path="/roles/<path:key_contact_role_id>",
        methods=["DELETE"],
        request=DeleteKeyContactRoleRequestAuth,
        response=DeleteKeyContactRoleResponse
    )
    def delete_key_contact_role(self, req: DeleteKeyContactRoleRequestAuth, resp: DeleteKeyContactRoleResponse):
        if req.has_errors():
            return resp(HTTPStatus.BAD_REQUEST, message="Bad Request")

        key_contact_repo = self.load_repository(KeyContactModel)
        key_contact_role_repo = self.load_repository(KeyContactRoleModel)

        if not key_contact_role_repo.db.contains(id=str(req.key_contact_role_id)):
            return resp(HTTPStatus.NOT_FOUND, message="Key Contact Role not found")

        key_contacts = key_contact_repo.db.remove(role_id=req.key_contact_role_id)
        key_contact_role_repo.db.remove_by_id(id=str(req.key_contact_role_id))


        return resp(HTTPStatus.OK, "Request Succefully")