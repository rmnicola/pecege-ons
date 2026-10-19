"""Extrai a carga horária por subsistema da fonte PostgreSQL.

    python aula1/extrair_carga.py
"""

import os
from collections import Counter

import psycopg
from psycopg.rows import dict_row


SQL = """SELECT id_subsistema, din_instante,
       val_cargaenergiahomwmed
FROM oficial.curva_horaria
WHERE din_instante >= %(inicio)s
  AND din_instante < %(fim)s"""


def extrair(evento):
    with psycopg.connect(
        os.environ["PG_DSN"], row_factory=dict_row
    ) as conexao:
        cursor = conexao.execute(SQL, evento)
        return cursor.fetchall()


if __name__ == "__main__":
    evento = {"inicio": "2025-01-01", "fim": "2025-01-08"}
    linhas = extrair(evento)
    print(f"{len(linhas)} linhas")
    print("por subsistema:", dict(sorted(Counter(l["id_subsistema"] for l in linhas).items())))
    print("primeira linha:", linhas[0])
