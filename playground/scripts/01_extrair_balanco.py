#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01 - Extrai o BALANCO da fonte para a staging do destino.

  * cenario aula1: fonte oficial (oficial.balanco_horario) -> aula1.stg_balanco
  * cenario aula2: copia de laboratorio (laboratorio.balanco_horario) ->
                   aula2.stg_balanco, tudo como texto.

Nao limpa, nao deduplica, nao converte: apenas copia e registra a
rastreabilidade (servico/banco/tabela de origem, recorte, hash e instante).

Uso:
    docker compose run --rm etl python scripts/01_extrair_balanco.py --cenario aula1
"""

from __future__ import annotations

import argparse
import sys
import time

import _common as U

LOG = U.get_logger("01_extrair_balanco")

COLUNAS = [
    "id_subsistema", "nom_subsistema", "din_instante",
    "val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar",
    "val_carga", "val_intercambio",
]
TIPOS_OFICIAL = {
    "id_subsistema": "text NOT NULL",
    "nom_subsistema": "text",
    "din_instante": "timestamp NOT NULL",
    "val_gerhidraulica": "numeric",
    "val_gertermica": "numeric",
    "val_gereolica": "numeric",
    "val_gersolar": "numeric",
    "val_carga": "numeric",
    "val_intercambio": "numeric",
}


def ddl_oficial(schema: str, tabela: str) -> str:
    cols = ",\n".join(f"    {c} {TIPOS_OFICIAL[c]}" for c in COLUNAS)
    return f"""
DROP TABLE IF EXISTS {schema}.{tabela} CASCADE;
CREATE TABLE {schema}.{tabela} (
{cols},
{U.ddl_colunas_meta()}
);
"""


def ddl_laboratorio(schema: str, tabela: str) -> str:
    cols = ",\n".join(f"    {c} text" for c in COLUNAS)
    return f"""
DROP TABLE IF EXISTS {schema}.{tabela} CASCADE;
CREATE TABLE {schema}.{tabela} (
    linha_lab bigint,
{cols},
{U.ddl_colunas_meta()}
);
"""


def main(argv=None) -> int:
    inicio = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cenario", required=True, choices=["aula1", "aula2"])
    args = parser.parse_args(argv)
    cenario = args.cenario

    conn_bal = U.conectar_balanco()
    conn_dest = U.conectar_destino()
    try:
        if cenario == "aula1":
            schema, tabela = "aula1", "stg_balanco"
            U.executar_ddl(conn_dest, ddl_oficial(schema, tabela))
            meta = U.metadados_origem(
                "FONTE_BALANCO", "oficial", "balanco_horario",
                "balanco_oficial_2025-01-01_2025-01-08.csv", "balanco", cenario,
            )
            select = "SELECT " + ", ".join(COLUNAS) + " FROM oficial.balanco_horario"
            destino_tabela = f"{schema}.{tabela}"
            n = U.extrair(conn_bal, conn_dest, select, destino_tabela, COLUNAS, meta)
        else:
            schema, tabela = "aula2", "stg_balanco"
            U.executar_ddl(conn_dest, ddl_laboratorio(schema, tabela))
            meta = U.metadados_origem(
                "FONTE_BALANCO", "laboratorio", "balanco_horario",
                "balanco_laboratorio_2025-01-01_2025-01-08.csv", "balanco", cenario,
            )
            colunas_src = ["linha_lab"] + COLUNAS
            select = "SELECT " + ", ".join(colunas_src) + " FROM laboratorio.balanco_horario"
            destino_tabela = f"{schema}.{tabela}"
            n = U.extrair(
                conn_bal, conn_dest, select, destino_tabela,
                colunas_src, meta,
            )
    finally:
        conn_bal.close()
        conn_dest.close()

    # confere o que foi gravado no destino
    conn_dest = U.conectar_destino()
    try:
        with conn_dest.cursor() as cur:
            cur.execute(f"SELECT count(*), count(DISTINCT id_subsistema) FROM {destino_tabela}")
            total, subs = cur.fetchone()
    finally:
        conn_dest.close()

    resumo = {
        "script": "01_extrair_balanco",
        "cenario": cenario,
        "destino": destino_tabela,
        "linhas_extraidas": n,
        "linhas_no_destino": total,
        "subsistemas_distintos": subs,
        "duracao_s": round(time.time() - inicio, 2),
    }
    if total != n:
        raise SystemExit(f"divergencia: extraidas {n}, no destino {total}")
    U.salvar_json(f"01_extrair_balanco_{cenario}.json", resumo)
    LOG.info("balanco/%s: %d linhas -> %s (%.2fs)", cenario, n, destino_tabela, resumo["duracao_s"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
