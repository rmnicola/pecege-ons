#!/usr/bin/env bash
# Prepara o laboratório do zero: atualiza o material, apaga o laboratório
# anterior (contêineres e dados), sobe tudo de novo e verifica.
# Seus arquivos em aula1/, aula2/ e saida/ não são apagados.
set -euo pipefail

etapa() { printf '\n==> %s\n' "$1"; }
falha() { printf '\n[FALHA] %s\n' "$1" >&2; exit 1; }

main() {
  cd "$(dirname "$0")"

  etapa "Atualizando o material"
  antes=$(git rev-parse HEAD)
  git pull --no-rebase --ff-only || falha "git pull não conseguiu atualizar. Mostre esta mensagem ao professor."
  # Se o próprio script mudou, roda a versão nova.
  [ "$(git rev-parse HEAD)" = "$antes" ] || exec ./preparar.sh

  etapa "Conferindo o Docker"
  command -v docker >/dev/null 2>&1 || falha "Docker não encontrado. Siga a preparação do ambiente."
  docker compose version >/dev/null 2>&1 || falha "Docker Compose v2 não encontrado. Siga a preparação do ambiente."
  docker info >/dev/null 2>&1 || falha "Sem permissão para usar o Docker. Rode o usermod da preparação, reconecte e tente de novo."
  [ -f .env ] || printf 'ETL_UID=%s\nETL_GID=%s\n' "$(id -u)" "$(id -g)" > .env
  rm -rf resultados  # pasta de versões anteriores do laboratório

  etapa "Apagando o laboratório anterior"
  projeto=$(docker compose config | sed -n 's/^name: //p')
  docker compose down -v --remove-orphans
  volumes=$(docker volume ls -q --filter "label=com.docker.compose.project=$projeto")
  [ -z "$volumes" ] || docker volume rm $volumes >/dev/null

  etapa "Construindo o playground (na primeira vez, leva alguns minutos)"
  docker compose build playground

  etapa "Subindo o playground, o banco e o armazenamento"
  docker compose up -d --wait

  etapa "Verificando"
  docker compose exec playground python .lab/verificar.py

  printf '\nEntre no playground:\n  pelo terminal: docker compose exec playground bash\n  pelo VS Code:  F1 → Dev Containers: Attach to Running Container… → %s-playground-1 → abra /work\n' "$projeto"
}

main "$@"
exit
