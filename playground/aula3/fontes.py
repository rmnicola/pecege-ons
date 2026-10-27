"""Funções prontas da aula 3: não precisa mexer aqui."""

import os

import pandas as pd
import psycopg

FONTE = "Fonte: ONS, Curva de Carga Horária, 01 a 07/01/2025 (extraído em 13/10/2026)."


def ler_semana():
    """Carga de cada hora de 01 a 07/01/2025, em MWmed: uma coluna por subsistema."""
    with psycopg.connect(os.environ["PG_DSN"]) as conexao:
        linhas = conexao.execute(
            "SELECT id_subsistema, din_instante, val_cargaenergiahomwmed "
            "FROM oficial.curva_horaria").fetchall()
    carga = pd.DataFrame(linhas, columns=["subsistema", "instante", "carga_mwmed"])
    carga["carga_mwmed"] = carga["carga_mwmed"].astype(float)
    semana = carga.pivot(index="instante", columns="subsistema", values="carga_mwmed")
    return semana[["SE", "S", "NE", "N"]]


def dia_tipico(semana):
    """A média de cada hora do dia (0 a 23h), por subsistema e no total."""
    tabela = semana.groupby(semana.index.hour).mean()
    tabela["Total"] = tabela.sum(axis=1)
    return tabela


def pico_diario(semana):
    """A maior carga horária de cada dia, somando os subsistemas, e a hora em que aconteceu."""
    total = semana.sum(axis=1)
    por_dia = total.groupby(total.index.date)
    return pd.DataFrame({"pico": por_dia.max(), "hora": por_dia.idxmax().dt.hour})


def participacao_no_pico(semana):
    """O peso de cada subsistema, em %, na hora de maior carga da semana."""
    total = semana.sum(axis=1)
    return semana.loc[total.idxmax()] / total.max() * 100
