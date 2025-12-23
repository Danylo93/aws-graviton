from arcs_lib_pca.application import BaseController, RequestAuth
from src.infrastructure import models
from sqlalchemy.exc import SQLAlchemyError

from .requests import(
    GetAuthorizeRequest,
)

from .responses import(
    AuthorizeGetResponse,
)

class AuthorizeController(BaseController):
    @BaseController.route(
        path="<provider_name>",
        methods=['GET'],
        request=GetAuthorizeRequest,
        response=AuthorizeGetResponse
    )
    def get_authorize_by_provider_name(self, req: GetAuthorizeRequest, resp: AuthorizeGetResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        provider_rep = self.load_repository(models.ProviderModel)
        provider = provider_rep.db.find(name=req.provider_name)
        #TODO: Implement logic from providers authorize
