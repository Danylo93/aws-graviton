from arcs_lib_pca.application import Response
from typing import Dict, Any, Optional

class AppClientAllGetResponse(Response):

    def load_links(self):
        if hasattr(self.body, "items"):
            for app_client in self.body["items"]:
                if hasattr(app_client, 'name'):
                    self.insert_link("PUT", f"atualizar_app_client_{app_client.name}", f"/arcs/app_clients/{app_client.name}", f"Atualizar app client: {app_client.name}")
                    self.insert_link("DELETE", f"deletar_app_client_{app_client.name}", f"/arcs/app_clients/{app_client.name}", f"Deletar app client: {app_client.name}")

class AppClientGetResponse(Response):

    def load_links(self):
        if 'name' in self.body:
            self.insert_link("PUT", "atualizar_app_client", f"/arcs/app_clients/{self.body['name']}", "Atualizar app client")
            self.insert_link("DELETE", "criar_dados", f"/arcs/app_clients/{self.body['name']}", "deletar app client")

class AppClientGetEnvsResponse(Response):

    def load_links(self):
        return None

class AppClientCreatedResponse(Response):
    
    def load_links(self):
        if 'name' in self.body:
            self.insert_link("PUT", "atualizar_app_client", f"/arcs/app_clients/{self.body['name']}", "Atualizar app client")
            self.insert_link("DELETE", "criar_dados", f"/arcs/app_clients/{self.body['name']}", "deletar app client")
    
class AppClientUpdatedResponse(Response):
    
    def load_links(self):
        if 'name' in self.body:
            self.insert_link("DELETE", "criar_dados", f"/arcs/app_clients/{self.body['name']}", "deletar app client")

class AppClientDeletedResponse(Response):
    
    def load_links(self):
        return None
    
class ConfigResponse(Response):
    
    def load_links(self):
        self.insert_link("POST", "salvar_configurações", f"/arcs/app_clients/config", "Insere ou atualiza as configurações do usuário")