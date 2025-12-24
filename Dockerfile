FROM python:3.12-alpine AS python-base

ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Install dependencies
RUN apk add --no-cache curl git gcc musl-dev libffi-dev shadow rsync ca-certificates nano

# Creating a virtual environment just for poetry and install it with pip
RUN pip3 install -U pip setuptools && pip3 install poetry==1.8.2

RUN printf  "#!/bin/sh \
            \n \
            # set poetry venv \n \
            poetry config virtualenvs.create false --local \
            \n \
            ## Copy project and lib and exclude some folders \n \
            rsync -av --mkpath --progress /tmp/service ./ \
                  --exclude .venv \
                  --exclude .dapr \
                  --exclude .pytest_cache \
                  --exclude \"*/*__pycache__\" \
                  --exclude \"poetry.lock\" \
            \n \
            rsync -av --mkpath --progress /tmp/arcs-lib-pca ./ \
                  --exclude .venv \
                  --exclude .dapr \
                  --exclude .pytest_cache \
                  --exclude \"*/*__pycache__\" \
                  --exclude \"poetry.lock\" \
            \n \
            ## Run to microservice location \n \
            cd ./service \
            \n \
            ## Run poetry install \n \
            poetry install --no-root --with dev --without prod --without hml --no-interaction \n \
            poetry update arcs-lib-pca \
            \n \
            ## Apply migrations \n \
            poetry run alembic upgrade head \
            \n \
            ## Run service \n \
            poetry run python3 main.py --host='0.0.0.0'\n" > setup-dev.sh && chmod +x setup-dev.sh

# Create entrypoint
ENTRYPOINT ["./setup-dev.sh"]