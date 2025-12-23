from arcs_lib_pca.application import Response

class PersonAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for person in self.body["items"]:
                if hasattr(person, "id") and hasattr(person, "id"):
                    self.insert_link("UPDATE", f"update_person_{person.id}", f"/accounts/persons/{person.id}", f"Atualizar person de {person.id}")
                    self.insert_link("DELETE", f"deletar_person_{person.id}", f"/accounts/persons/{person.id}", f"Deletar person de {person.id}")

class PersonGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "id") and hasattr(self.body, "id"):
            self.insert_link("UPDATE", f"update_person_{self.body.id}", f"/accounts/persons/{self.body.id}", f"Atualizar person de {self.body.id}")
            self.insert_link("DELETE", f"create_person_{self.body.id}", f"/accounts/persons/{self.body.id}", f"deletar person de {self.body.id}")

class PersonCreatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("UPDATE", "update_person", f"/accounts/persons/{self.body.id}", "Atualizar person")
            self.insert_link("DELETE", "delete_person", f"/accounts/persons/{self.body.id}", "deletar person")
    
class PersonUpdatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "id"):
            self.insert_link("DELETE", "delete_person", f"/accounts/persons/{self.body.id}", "deletar person")

class PersonDeletedResponse(Response):
    
    def load_links(self):
        return None
    
class PersonGetByDocResponse(Response):
    
    def load_links(self):
        return None