from arcs_lib_pca.application import Response

class GetAllKeyContactResponse(Response):
    def load_links(self):
        if "items" in self.body:
            for contact in self.body['items']:
                if 'id' in contact:
                    id = contact["id"]
                    self.insert_link("GET", f"visualizar_contato_{id}", f"/key_contacts/{id}", f"Visualizar contato: {id}")
                    self.insert_link("PUT", f"atualizar_contato_{id}", f"/key_contacts/{id}", f"Atualizar contato: {id}")
                    self.insert_link("DELETE", f"deletar_contato_{id}", f"/key_contacts/{id}", f"Deletar contato: {id}")


class CreateKeyContactResponse(Response):
    def load_links(self):
        contact = self.body
        if 'id' in contact:
            id = contact["id"]
            self.insert_link("GET", f"visualizar_contato_{id}", f"/key_contacts/{id}", f"Visualizar contato: {id}")
            self.insert_link("PUT", f"atualizar_contato_{id}", f"/key_contacts/{id}", f"Atualizar contato: {id}")
            self.insert_link("DELETE", f"deletar_contato_{id}", f"/key_contacts/{id}", f"Deletar contato: {id}")


class GetKeyContactResponse(Response):
    def load_links(self):
        contact = self.body
        if 'id' in contact:
            id = contact["id"]
            self.insert_link("GET", f"visualizar_contato_{id}", f"/key_contacts/{id}", f"Visualizar contato: {id}")
            self.insert_link("PUT", f"atualizar_contato_{id}", f"/key_contacts/{id}", f"Atualizar contato: {id}")
            self.insert_link("DELETE", f"deletar_contato_{id}", f"/key_contacts/{id}", f"Deletar contato: {id}")


class UpdateKeyContactResponse(Response):
    def load_links(self):
        contact = self.body
        if 'id' in contact:
            id = contact["id"]
            self.insert_link("GET", f"visualizar_contato_{id}", f"/key_contacts/{id}", f"Visualizar contato: {id}")
            self.insert_link("PUT", f"atualizar_contato_{id}", f"/key_contacts/{id}", f"Atualizar contato: {id}")
            self.insert_link("DELETE", f"deletar_contato_{id}", f"/key_contacts/{id}", f"Deletar contato: {id}")


class DeleteKeyContactResponse(Response):
    def load_links(self):
        return None

# Key Contact Role

class GetAllKeyContactRoleResponse(Response):
    def load_links(self):
        if "items" in self.body:
            for contact_role in self.body['items']:
                if 'id' in contact_role:
                    id = contact_role["id"]
                    self.insert_link("GET", f"visualizar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Visualizar grupo contato: {id}")
                    self.insert_link("PUT", f"atualizar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Atualizar grupo contato: {id}")
                    self.insert_link("DELETE", f"deletar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Deletar grupo contato: {id}")


class CreateKeyContactRoleResponse(Response):
    def load_links(self):
        contact_role = self.body
        if 'id' in contact_role:
            id = contact_role["id"]
            self.insert_link("GET", f"visualizar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Visualizar grupo contato: {id}")
            self.insert_link("PUT", f"atualizar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Atualizar grupo contato: {id}")
            self.insert_link("DELETE", f"deletar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Deletar grupo contato: {id}")

class UpdateKeyContactRoleResponse(Response):
    def load_links(self):
        contact_role = self.body
        if 'id' in contact_role:
            id = contact_role["id"]
            self.insert_link("GET", f"visualizar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Visualizar grupo contato: {id}")
            self.insert_link("PUT", f"atualizar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Atualizar grupo contato: {id}")
            self.insert_link("DELETE", f"deletar_grupo_contato_{id}", f"/key_contacts/roles/{id}", f"Deletar grupo contato: {id}")


class DeleteKeyContactRoleResponse(Response):
    def load_links(self):
        return None