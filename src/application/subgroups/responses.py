from arcs_lib_pca.application import Response
from arcs_lib_pca.utils.string import to_snake_case

class SubGroupAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for subgroup in self.body["items"]:
                if hasattr(subgroup, "id") and hasattr(subgroup, "name") and hasattr(subgroup, "service_name"):
                    self.insert_link("UPDATE", f"update_subgroup_{to_snake_case(subgroup.name)}", f"/accounts/subgroups/{subgroup.id}", f"Atualizar grupo de {subgroup.name}")
                    self.insert_link("DELETE", f"deletar_subgroup_{to_snake_case(subgroup.name)}", f"/accounts/subgroups/{subgroup.id}", f"Deletar grupo de {subgroup.name}")

class SubGroupGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "id") and hasattr(self.body, "name") and hasattr(self.body, "service_name"):
            self.insert_link("UPDATE", f"update_subgroup_{to_snake_case(self.body.name)}", f"/accounts/subgroups/{self.body.id}", f"Atualizar grupo de {self.body.name}")
            self.insert_link("DELETE", f"create_subgroup_{to_snake_case(self.body.name)}", f"/accounts/subgroups/{self.body.id}", f"deletar grupo de {self.body.name}")

class SubGroupCreatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("UPDATE", "update_subgroup", f"/accounts/subgroups/{self.body.id}", "Atualizar grupo")
            self.insert_link("DELETE", "delete_subgroup", f"/accounts/subgroups/{self.body.id}", "deletar grupo")
    
class SubGroupUpdatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("DELETE", "delete_subgroup", f"/accounts/subgroups/{self.body.id}", "deletar subgroup")

class SubGroupDeletedResponse(Response):
    
    def load_links(self):
        return None