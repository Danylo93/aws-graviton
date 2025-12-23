from typing import List, Type
from pydantic import Field
from arcs_lib_pca.application import RequestAuth


class LogoutRequestAuth(RequestAuth):

    def permissions(self):
        return []