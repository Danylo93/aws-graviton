from arcs_lib_pca.application import RequestAuth
from arcs_lib_pca.tools.security.permissions import CanWrite

class RefreshTokenRequestAuth(RequestAuth):

    def permissions(self):
        return [CanWrite]