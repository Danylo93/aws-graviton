from arcs_lib_pca.application import Response

class ServiceAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for service in self.body['items']:
                if hasattr(service, "name"):
                    self.insert_link("UPDATE", f"atualizar_service_{service.name}", f"/arcs/services/{service.name}", f"Atualizar service: {service.name}")
                    self.insert_link("DELETE", f"deletar_service_{service.name}", f"/arcs/services/{service.name}", f"Deletar service: {service.name}")

class ServiceGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "name"):
            self.insert_link("UPDATE", "atualizar_service", f"/arcs/services/{self.body.name}", "Atualizar service")
            self.insert_link("DELETE", "criar_dados", f"/arcs/services/{self.body.name}", "deletar service")

class ServiceCreatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "name"):
            self.insert_link("UPDATE", "atualizar_service", f"/arcs/services/{self.body.name}", "Atualizar service")
            self.insert_link("DELETE", "criar_dados", f"/arcs/services/{self.body.name}", "deletar service")
    
class ServiceUpdatedResponse(Response):
    
    def load_links(self):
        if hasattr(self.body, "name"):
            self.insert_link("DELETE", "criar_dados", f"/arcs/services/{self.body.name}", "deletar service")

class ServiceDeletedResponse(Response):
    
    def load_links(self):
        return None