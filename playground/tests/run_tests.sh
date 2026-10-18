#!/usr/bin/env bash
# Roda o pipeline REAL dos dois cenarios, verifica reexecucao (idempotencia)
# e executa os testes de invariantes. Todos os comandos rodam no container etl;
# o host nao precisa de Python nem de cliente PostgreSQL.
#
# Uso (a partir de playground/):
#   bash tests/run_tests.sh
set -euo pipefail

cd "$(dirname "$0")/.."
DC="docker compose"

log() { printf '\n=== %s ===\n' "$*"; }

log "subindo os bancos (aguardando healthcheck)"
$DC up -d --wait fonte-balanco fonte-curva destino

log "testes unitarios puros (sem acesso aos bancos)"
$DC run --rm etl python tests/test_unit_sem_docker.py

run() { $DC run --rm etl python "$@"; }

pipeline() {
  run scripts/00_carregar_fontes.py
  run scripts/01_extrair_balanco.py --cenario aula1
  run scripts/02_extrair_curva.py --cenario aula1
  run scripts/03_integrar.py --cenario aula1
  run scripts/01_extrair_balanco.py --cenario aula2
  run scripts/02_extrair_curva.py --cenario aula2
  run scripts/04_diagnosticar.py
  run scripts/05_tratar.py
  run scripts/06_avaliar.py
}

contagens() {
  $DC exec -T -e PGPASSWORD=ons_lab destino psql -U ons_lab -d analytics -At -F';' -c "
    SELECT
      (SELECT count(*) FROM aula1.integrado)
      || ',' || (SELECT count(*) FROM aula2.limpo_balanco)
      || ',' || (SELECT count(*) FROM aula2.limpo_curva)
      || ',' || (SELECT count(*) FROM aula2.integrado_limpo)
      || ',' || (SELECT count(*) FROM aula2.quarentena)
      || ',' || (SELECT count(*) FROM aula2.diagnostico_extremos);"
}

log "pipeline (execucao 1)"
pipeline
c1="$(contagens)"
log "pipeline (execucao 2) - checagem de idempotencia"
pipeline
c2="$(contagens)"

igual="false"
[ "$c1" = "$c2" ] && igual="true"
cat > resultados/_idempotencia.json <<JSON
{
  "execucao_1": "$c1",
  "execucao_2": "$c2",
  "igual": $igual
}
JSON
printf 'idempotencia: %s\n  exec1=%s\n  exec2=%s\n' "$igual" "$c1" "$c2"

log "integracao ingenua do cenario aula2 (deve rejeitar com exit 2)"
set +e
$DC run --rm etl python scripts/03_integrar.py --cenario aula2
codigo=$?
set -e
printf '%s\n' "$codigo" > resultados/03_aula2_exitcode.txt
printf 'exit code de 03 aula2 = %s (esperado 2)\n' "$codigo"

log "testes de invariantes"
$DC run --rm etl python -m pytest tests -q

log "concluido"
