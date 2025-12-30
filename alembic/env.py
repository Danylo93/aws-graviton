import os
import urllib.parse
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine, engine_from_config, pool, text
from alembic import context
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from arcs_lib_pca.infrastructure.model.postgresql_model import PostgreSqlModel
from src.infrastructure import models  # Certifique-se de que os modelos estão carregados

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do Alembic
config = context.config

# Variáveis de ambiente do banco de dados
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
AZURE_CLIENT_ID = os.getenv("AZURE_MANAGED_IDENTITY_CLIENT_ID")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
ENV = os.getenv("ENV", "DEVELOPMENT").upper()

# Definir a URL do banco de dados com base no ambiente
def get_database_url():
    if ENV == 'TEST':
        return TEST_DATABASE_URL
    elif ENV in ["PRODUCTION", "HOMOLOG"]:
        # Autenticação via Azure AD no ambiente de produção ou homologação
        # O Service Connector cria o usuário AAD, geralmente como "aad_arcs_postgres" ou "aad_user_{POSTGRES_DB}"
        # Tenta usar POSTGRES_AAD_USER se definido explicitamente
        postgres_aad_user = os.getenv("POSTGRES_AAD_USER")
        if postgres_aad_user:
            postgres_user = postgres_aad_user
        else:
            # Tenta usar o padrão do Service Connector: "aad_arcs_postgres" ou "aad_user_{POSTGRES_DB}"
            # Primeiro tenta "aad_arcs_postgres" (padrão do Service Connector quando connection name é "arcs_postgres")
            # Se não funcionar, tenta "aad_user_{POSTGRES_DB}" (padrão antigo)
            postgres_user = "aad_arcs_postgres"  # Padrão do Service Connector para connection name "arcs_postgres"
        
        # Tentar usar ClientSecretCredential se as variáveis estiverem disponíveis
        # Caso contrário, usar DefaultAzureCredential
        azure_client_id = os.getenv("AZURE_CLIENT_ID")
        azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
        azure_tenant_id = os.getenv("AZURE_TENANT_ID")
        
        if azure_client_id and azure_client_secret and azure_tenant_id:
            # Usar ClientSecretCredential quando as variáveis estão disponíveis
            credential = ClientSecretCredential(
                tenant_id=azure_tenant_id,
                client_id=azure_client_id,
                client_secret=azure_client_secret
            )
        else:
            # Fallback para DefaultAzureCredential
            credential = DefaultAzureCredential()
        
        access_token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token
        password = urllib.parse.quote_plus(access_token)
        return f"postgresql+psycopg://{postgres_user}:{password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}?sslmode=require"
    else:
        # Ambiente de desenvolvimento/local
        password = urllib.parse.quote_plus(POSTGRES_PASSWORD or "")
        return f"postgresql+psycopg://{POSTGRES_USER}:{password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

database_url = get_database_url()
config.set_main_option('sqlalchemy.url', database_url)

# Configuração de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados para suporte ao autogenerate
target_metadata = PostgreSqlModel.metadata

# Função para criar o banco de dados, se não existir
def create_database_if_not_exists(db_url: str):
    engine = create_engine(db_url.rsplit('/', 1)[0], isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :dbname"), {'dbname': POSTGRES_DB}).scalar()
            if not exists:
                conn.execute(text(f"CREATE DATABASE {POSTGRES_DB}"))
    except Exception as e:
        raise RuntimeError(f"Erro ao criar o banco de dados: {e}")
    finally:
        engine.dispose()

# Garantir que o banco de dados existe em ambientes locais
if ENV not in ["PRODUCTION", "HOMOLOG", "TEST"]:
    create_database_if_not_exists(database_url)

# Modo de migração offline
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# Modo de migração online
def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# Verificar modo de execução (offline/online) e executar migrações
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
