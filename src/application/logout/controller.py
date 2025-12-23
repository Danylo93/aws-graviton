from arcs_lib_pca.application import BaseController
from arcs_lib_pca.domain.value_objects import AccessProfile

from src.infrastructure.models.access_profile_model import AccessProfileModel

from .requests import(
    LogoutRequestAuth,
)

from .responses import(
    LogoutResponse,
)

class LogoutController(BaseController):

    @BaseController.route(
        path="/",
        methods=["POST"],
        request=LogoutRequestAuth,
        response=LogoutResponse)
    def logout(self, req: LogoutRequestAuth, resp: LogoutResponse):
        if req.has_errors():
            return resp(status_code=404, message="Invalid request")
        
        ap_repo = self.load_repository(AccessProfileModel)
        # AccessProfile.remove_in_redis(ap_repo.redis, req.current_profile.profile_id)
        
        return resp(200, {}, "Exited successfully")
        


