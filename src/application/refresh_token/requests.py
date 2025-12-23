from arcs_lib_pca.application import RequestAuth

class RefreshTokenRequestAuth(RequestAuth):

    def permissions(self):
        return []