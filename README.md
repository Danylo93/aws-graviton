# Arcs-service - V1
Microservice responsável por fornecer todas as funcionalidades de configurações personalizadas por usuário. Integrado com Microsoft EntraID, storage e database através do ARCS-LIB-PCA

# Arquivos movido para ambiente de HOMOLOGAÇÃO

Os demais arquivos serão ignorados, para adicionar um arquivo ou pasta no ambiente de homologação, verifique/altere o Dockerfile.hml

```SHELL
COPY /alembic ./alembic
COPY /src ./src
COPY /__init__.py ./
COPY /alembic.ini ./
COPY /hml.env ./.env
COPY /main.py ./
COPY /pyproject.toml ./
```
