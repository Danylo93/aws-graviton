from arcs_lib_pca.application import Response
from arcs_lib_pca.utils.string import to_snake_case
class PermissionAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for permission in self.body["items"]:
                if hasattr(permission, "id") and hasattr(permission, "app_client_name") and hasattr(permission, "service_name"):
                    self.insert_link("UPDATE", f"update_permission_{to_snake_case(permission.app_client_name)}", f"/arcs/permissions/{permission.id}", f"Atualizar permissão de {permission.app_client_name} em {permission.service_name}")
                    self.insert_link("DELETE", f"deletar_permission_{to_snake_case(permission.app_client_name)}", f"/arcs/permissions/{permission.id}", f"Deletar permissão de {permission.app_client_name} em {permission.service_name}")

class PermissionGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "id") and hasattr(self.body, "app_client_name") and hasattr(self.body, "service_name"):
            self.insert_link("UPDATE", f"update_permission_{to_snake_case(self.body.app_client_name)}", f"/arcs/permissions/{self.body.id}", f"Atualizar permissão de {self.body.app_client_name} em {self.body.service_name}")
            self.insert_link("DELETE", f"create_permission_{to_snake_case(self.body.app_client_name)}", f"/arcs/permissions/{self.body.id}", f"deletar permissão de {self.body.app_client_name} em {self.body.service_name}")

class PermissionCreatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("UPDATE", "update_permission", f"/arcs/permissions/{self.body.id}", "Atualizar permissão")
            self.insert_link("DELETE", "delete_permission", f"/arcs/permissions/{self.body.id}", "deletar permissão")
    
class PermissionUpdatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("DELETE", "delete_permission", f"/arcs/permissions/{self.body.id}", "deletar permission")

class PermissionDeletedResponse(Response):
    
    def load_links(self):
        return None