from arcs_lib_pca.application import Response

class SendCodeResponse(Response):
    def load_links(self):
        return []

class ValidateCodeResponse(Response):
    def load_links(self):
        return []

class ResetPasswordResponse(Response):
    def load_links(self):
        return []

class ResetPasswordAuthenticatedResponse(Response):
    def load_links(self):
        return []