#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""02 - Extrai a CURVA DE CARGA da fonte para a staging do destino.

  * cenario aula1: oficial.curva_horaria   -> aula1.stg_curva
  * cenario aula2: laboratorio.curva_horaria -> aula2.stg_curva (texto cru)

Uso:
    docker compose run --rm etl python scripts/02_extrair_curva.py --cenario aula1
"""

from __future__ import annotations

import argparse
import sys
import time

import _common as U

LOG = U.get_logger("02_extrair_curva")

COLUNAS = [
    "id_subsistema", "nom_subsistema", "din_instante", "val_cargaenergiahomwmed",
]
TIPOS_OFICIAL = {
    "id_subsistema": "text NOT NULL",
    "nom_subsistema": "text",
    "din_instante": "timestamp NOT NULL",
    "val_cargaenergiahomwmed": "numeric",
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

    conn_cur = U.conectar_curva()
    conn_dest = U.conectar_destino()
    try:
        if cenario == "aula1":
            schema, tabela = "aula1", "stg_curva"
            U.executar_ddl(conn_dest, ddl_oficial(schema, tabela))
            meta = U.metadados_origem(
                "FONTE_CURVA", "oficial", "curva_horaria",
                "curva_oficial_2025-01-01_2025-01-08.csv", "curva", cenario,
            )
            select = "SELECT " + ", ".join(COLUNAS) + " FROM oficial.curva_horaria"
            destino_tabela = f"{schema}.{tabela}"
            n = U.extrair(conn_cur, conn_dest, select, destino_tabela, COLUNAS, meta)
        else:
            schema, tabela = "aula2", "stg_curva"
            U.executar_ddl(conn_dest, ddl_laboratorio(schema, tabela))
            meta = U.metadados_origem(
                "FONTE_CURVA", "laboratorio", "curva_horaria",
                "curva_laboratorio_2025-01-01_2025-01-08.csv", "curva", cenario,
            )
            colunas_src = ["linha_lab"] + COLUNAS
            select = "SELECT " + ", ".join(colunas_src) + " FROM laboratorio.curva_horaria"
            destino_tabela = f"{schema}.{tabela}"
            n = U.extrair(conn_cur, conn_dest, select, destino_tabela, colunas_src, meta)
    finally:
        conn_cur.close()
        conn_dest.close()

    conn_dest = U.conectar_destino()
    try:
        with conn_dest.cursor() as cur:
            cur.execute(f"SELECT count(*), count(DISTINCT id_subsistema) FROM {destino_tabela}")
            total, subs = cur.fetchone()
    finally:
        conn_dest.close()

    resumo = {
        "script": "02_extrair_curva",
        "cenario": cenario,
        "destino": destino_tabela,
        "linhas_extraidas": n,
        "linhas_no_destino": total,
        "subsistemas_distintos": subs,
        "duracao_s": round(time.time() - inicio, 2),
    }
    if total != n:
        raise SystemExit(f"divergencia: extraidas {n}, no destino {total}")
    U.salvar_json(f"02_extrair_curva_{cenario}.json", resumo)
    LOG.info("curva/%s: %d linhas -> %s (%.2fs)", cenario, n, destino_tabela, resumo["duracao_s"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
