from arcs_lib_pca.application import Response
from arcs_lib_pca.utils.string import to_snake_case

class GroupAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for group in self.body["items"]:
                if hasattr(group, "id") and hasattr(group, "name") and hasattr(group, "service_name"):
                    self.insert_link("UPDATE", f"update_group_{to_snake_case(group.name)}", f"/accounts/groups/{group.id}", f"Atualizar grupo de {group.name}")
                    self.insert_link("DELETE", f"deletar_group_{to_snake_case(group.name)}", f"/accounts/groups/{group.id}", f"Deletar grupo de {group.name}")

class GroupGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "id") and hasattr(self.body, "name") and hasattr(self.body, "service_name"):
            self.insert_link("UPDATE", f"update_group_{to_snake_case(self.body.name)}", f"/accounts/groups/{self.body.id}", f"Atualizar grupo de {self.body.name}")
            self.insert_link("DELETE", f"create_group_{to_snake_case(self.body.name)}", f"/accounts/groups/{self.body.id}", f"deletar grupo de {self.body.name}")

class GroupCreatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("UPDATE", "update_group", f"/accounts/groups/{self.body.id}", "Atualizar grupo")
            self.insert_link("DELETE", "delete_group", f"/accounts/groups/{self.body.id}", "deletar grupo")
    
class GroupUpdatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("DELETE", "delete_group", f"/accounts/groups/{self.body.id}", "deletar group")

class GroupDeletedResponse(Response):
    
    def load_links(self):
        return None
    

class GetServicesByGroupIdResponse(Response):

    def load_links(self):
        return None