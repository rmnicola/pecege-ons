#!/usr/bin/env bash
# Prepara o laboratório: registra seu usuário, constrói a imagem Python,
# sobe os bancos, carrega os dados (só na primeira vez) e verifica tudo.
# Pode ser executado de novo a qualquer momento: não apaga dados.
set -euo pipefail
cd "$(dirname "$0")"

etapa() { printf '\n==> %s\n' "$1"; }
falha() { printf '\n[FALHA] %s\n' "$1" >&2; exit 1; }

etapa "Conferindo o Docker"
command -v docker >/dev/null 2>&1 || falha "Docker não encontrado. Instale-o (passo 3 da preparação)."
docker compose version >/dev/null 2>&1 || falha "Docker Compose v2 não encontrado. Instale docker-compose-v2 (passo 3)."
docker info >/dev/null 2>&1 || falha "Sem permissão para usar o Docker. Rode o usermod do passo 3, reconecte e tente de novo."
echo "ok"

if [ ! -f .env ]; then
  etapa "Registrando seu usuário em .env"
  printf 'ETL_UID=%s\nETL_GID=%s\n' "$(id -u)" "$(id -g)" > .env
  echo "ok"
fi

etapa "Construindo a imagem Python (na primeira vez, leva alguns minutos)"
docker compose build etl

etapa "Subindo os bancos"
docker compose up -d --wait fonte-balanco fonte-curva destino

etapa "Carregando os dados"
linhas=$(docker compose exec -T fonte-curva psql -U ons_lab -d curva -tAc \
  "SELECT count(*) FROM oficial.curva_horaria" 2>/dev/null || echo 0)
if [ "${linhas:-0}" -gt 0 ] 2>/dev/null; then
  echo "dados já carregados ($linhas linhas de carga); nada a fazer"
else
  docker compose run --rm etl python scripts/00_carregar_fontes.py --sem-reset
fi

etapa "Verificando o ambiente"
docker compose run --rm etl python scripts/verificar_ambiente.py

printf '\nTudo pronto para trabalhar.\n'
