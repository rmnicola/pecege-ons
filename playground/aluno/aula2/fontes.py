"""Fontes da aula 2: os mesmos contratos da aula 1, agora com dados que precisam de correção.

Cada fonte devolve os dados como chegam (brutos), sem corrigir nada:
id_subsistema, instante e valor, mais as colunas de contexto que a origem informa.
"""

import os
from datetime import date, timedelta

import httpx
import pandas as pd
import psycopg
from psycopg.rows import dict_row

CIDADES = {
    "N": ("Belém", -1.46, -48.49),
    "NE": ("Recife", -8.05, -34.88),
    "SE": ("São Paulo", -23.55, -46.63),
    "S": ("Porto Alegre", -30.03, -51.23),
}


class CargaPostgres:
    """Cópia de laboratório da Curva de Carga: todas as colunas chegam como texto."""
    nome = "carga_mwmed"
    SQL = """SELECT id_subsistema, din_instante AS instante,
                    val_cargaenergiahomwmed AS valor
             FROM laboratorio.curva_horaria
             WHERE din_instante >= %(inicio)s AND din_instante < %(fim)s"""

    def extrair(self, inicio, fim):
        with psycopg.connect(os.environ["PG_DSN"], row_factory=dict_row) as conexao:
            linhas = conexao.execute(self.SQL, {"inicio": inicio, "fim": fim}).fetchall()
        return pd.DataFrame(linhas)


class ClimaApi:
    """API de clima no formato da Open-Meteo. Por padrão, a API local do playground."""
    nome = "temperatura_c"

    def __init__(self, url=None, cidades=CIDADES):
        self.url = url or os.environ["CLIMA_URL"]
        self.cidades = cidades

    def extrair(self, inicio, fim):
        # O contrato usa fim exclusivo; a API inclui end_date.
        ultimo_dia = (date.fromisoformat(fim) - timedelta(days=1)).isoformat()
        partes = []
        for sub, (_, lat, lon) in self.cidades.items():
            resposta = httpx.get(self.url, params={
                "latitude": lat, "longitude": lon,
                "start_date": inicio, "end_date": ultimo_dia,
                "hourly": "temperature_2m", "timezone": "America/Sao_Paulo",
            }, timeout=30.0)
            resposta.raise_for_status()
            dados = resposta.json()
            partes.append(pd.DataFrame({
                "id_subsistema": sub,
                "instante": dados["hourly"]["time"],
                "valor": dados["hourly"]["temperature_2m"],
                "unidade": dados["hourly_units"]["temperature_2m"],
            }))
        return pd.concat(partes, ignore_index=True)
