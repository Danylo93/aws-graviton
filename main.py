import os
from dotenv import load_dotenv
from src.application.addresses.controller import AddressesController
from src.application.contacts.controller import ContactsController
from arcs_lib_pca import Arcs, ServiceFlask
from src.application import (
    AccessProfilesController,
    AppClientsController,
    AuthController,
    ContactTypeController,
    DashboardsController,
    FiaCardTypeController,
    CBACardTypeController,
    GroupController,
    GuestController,
    InviteController,
    LogoutController,
    PermissionsController,
    PersonController,
    ProfileController,
    RefreshTokenController,
    RegisterController,
    ResetPasswordController,
    ServicesController,
    SubGroupController,
    UserController,
    KeyContactsController,
    PersonalTeamController,
    TechnicalTeamController,
    UserController,
    PilotController,
    UserGuestController,
    LibController
)

load_dotenv()
app = Arcs(__file__)

@app.load_service()
class ArcsService(ServiceFlask):
    domain: str = "app_domain"
    name: str = "arcs_service"
    friendly_name: str = "Arcs core service"
    controller: dict = {
        "/access_profiles": AccessProfilesController,
        "/app_clients": AppClientsController,
        "/auth": AuthController,
        "/contact_types": ContactTypeController,
        "/dashboards": DashboardsController,
        "/fia_card_types": FiaCardTypeController,
        "/cba_card_types": CBACardTypeController,
        "/groups": GroupController,
        "/guests": GuestController,
        "/invite": InviteController,
        "/logout": LogoutController,
        "/permissions": PermissionsController,
        "/persons": PersonController,
        "/profiles": ProfileController,
        "/refresh_token": RefreshTokenController,
        "/registers": RegisterController,
        "/reset_password": ResetPasswordController,
        "/services": ServicesController,
        "/subgroups": SubGroupController,
        "/personal_teams": PersonalTeamController,
        "/technical_teams": TechnicalTeamController,
        "/users": UserController,
        "/key_contacts": KeyContactsController,
        "/pilots": PilotController,
        "/user_guests": UserGuestController,
        "/contacts": ContactsController,
        "/addresses": AddressesController,
        "/lib": LibController,

    }
    description_service: str = "Microservice core application for Arcs."
    version: str = "1.0"
    bindings: list = []
    settings: dict = {
        "google_app_id": os.environ.get("GOOGLE_APP_ID", None),
        "microsoft_app_id": os.environ.get("MICROSOFT_APP_ID", None),
        "apple_app_id": os.environ.get("APPLE_APP_ID", None),
        "apple_keys_url": os.environ.get("APPLE_KEYS_URL", "https://appleid.apple.com/auth/keys"),
    }
    config_framework: dict = {
        "config": {}
    }

wsgi_app = app.service.wsgi()

if __name__ == "__main__":
    app.service.run()
