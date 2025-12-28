import os
import sys
import logging
from dotenv import load_dotenv

# Configurar logging detalhado antes de qualquer import
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("INICIANDO APLICAÇÃO - Fase 1: Imports básicos")
logger.info("=" * 60)

try:
    logger.info("Carregando dotenv...")
    load_dotenv()
    logger.info("✅ dotenv carregado")
except Exception as e:
    logger.error(f"❌ Erro ao carregar dotenv: {e}", exc_info=True)
    raise

logger.info("=" * 60)
logger.info("Fase 2: Importando controllers")
logger.info("=" * 60)

try:
    logger.info("Importando AddressesController...")
    from src.application.addresses.controller import AddressesController
    logger.info("✅ AddressesController importado")
    
    logger.info("Importando ContactsController...")
    from src.application.contacts.controller import ContactsController
    logger.info("✅ ContactsController importado")
    
    logger.info("Importando arcs_lib_pca...")
    from arcs_lib_pca import Arcs, ServiceFlask
    logger.info("✅ arcs_lib_pca importado")
    
    logger.info("Importando outros controllers...")
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
        UserGuestController
    )
    logger.info("✅ Todos os controllers importados")
except Exception as e:
    logger.error(f"❌ Erro ao importar controllers: {e}", exc_info=True)
    raise

logger.info("=" * 60)
logger.info("Fase 3: Criando instância Arcs")
logger.info("=" * 60)

try:
    logger.info("Criando instância Arcs(__file__)...")
    app = Arcs(__file__)
    logger.info("✅ Instância Arcs criada")
except Exception as e:
    logger.error(f"❌ Erro ao criar instância Arcs: {e}", exc_info=True)
    raise

logger.info("=" * 60)
logger.info("Fase 4: Definindo ArcsService")
logger.info("=" * 60)

try:
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
    
    logger.info("✅ ArcsService definido")
except Exception as e:
    logger.error(f"❌ Erro ao definir ArcsService: {e}", exc_info=True)
    raise

logger.info("=" * 60)
logger.info("Fase 5: Criando wsgi_app")
logger.info("=" * 60)

try:
    logger.info("Criando wsgi_app...")
    wsgi_app = app.service.wsgi()
    logger.info("✅ wsgi_app criado com sucesso!")
    logger.info("=" * 60)
    logger.info("APLICAÇÃO PRONTA PARA SERVER REQUISIÇÕES")
    logger.info("=" * 60)
except Exception as e:
    logger.error(f"❌ Erro ao criar wsgi_app: {e}", exc_info=True)
    raise

if __name__ == "__main__":
    app.service.run()
