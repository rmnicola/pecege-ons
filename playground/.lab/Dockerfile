# A máquina do aluno: Python 3.12 com as bibliotecas da aula, psql, curl e jq.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client curl jq \
    && rm -rf /var/lib/apt/lists/*

# VS Code: ao entrar no contêiner (Attach to Running Container), instala Python e Jupyter para abrir notebooks.
LABEL devcontainer.metadata='[{"customizations":{"vscode":{"extensions":["ms-python.python","ms-toolsai.jupyter"]}}}]'

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Mesmo id do usuário do host: os arquivos gravados em saida/ ficam com o dono certo.
ARG UID=1000
ARG GID=1000
RUN groupadd -o -g "$GID" aluno && useradd -o -m -u "$UID" -g "$GID" -s /bin/bash aluno
USER aluno
WORKDIR /work
