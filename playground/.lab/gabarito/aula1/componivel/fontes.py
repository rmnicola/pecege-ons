"""Fontes que cumprem o contrato: extrair(inicio, fim) -> id_subsistema, instante, valor."""

import json
import os
from datetime import date, timedelta
from pathlib import Path

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
    nome = "carga_mwmed"
    SQL = """SELECT id_subsistema, din_instante AS instante,
                    val_cargaenergiahomwmed AS valor
             FROM oficial.curva_horaria
             WHERE din_instante >= %(inicio)s AND din_instante < %(fim)s"""

    def extrair(self, inicio, fim):
        with psycopg.connect(os.environ["PG_DSN"], row_factory=dict_row) as conexao:
            linhas = conexao.execute(self.SQL, {"inicio": inicio, "fim": fim}).fetchall()
        tabela = pd.DataFrame(linhas)
        tabela["valor"] = tabela["valor"].astype(float)
        return tabela


def _tabela_clima(sub, resposta):
    return pd.DataFrame({
        "id_subsistema": sub,
        "instante": pd.to_datetime(resposta["hourly"]["time"]),
        "valor": resposta["hourly"]["temperature_2m"],
    })


class ClimaOpenMeteo:
    nome = "temperatura_c"
    URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, cidades=CIDADES):
        self.cidades = cidades

    def extrair(self, inicio, fim):
        # O contrato usa fim exclusivo; a API inclui end_date.
        ultimo_dia = (date.fromisoformat(fim) - timedelta(days=1)).isoformat()
        partes = []
        for sub, (_, lat, lon) in self.cidades.items():
            resposta = httpx.get(self.URL, params={
                "latitude": lat, "longitude": lon,
                "start_date": inicio, "end_date": ultimo_dia,
                "hourly": "temperature_2m", "timezone": "America/Sao_Paulo",
            }, timeout=30.0)
            resposta.raise_for_status()
            partes.append(_tabela_clima(sub, resposta.json()))
        return pd.concat(partes, ignore_index=True)


class ClimaArquivo:
    """Mesmo contrato, lendo respostas salvas da Open-Meteo (clima_<subsistema>.json)."""
    nome = "temperatura_c"

    def __init__(self, pasta):
        self.pasta = Path(pasta)

    def extrair(self, inicio, fim):
        partes = []
        for arquivo in sorted(self.pasta.glob("clima_*.json")):
            sub = arquivo.stem.removeprefix("clima_")
            partes.append(_tabela_clima(sub, json.loads(arquivo.read_text(encoding="utf-8"))))
        tabela = pd.concat(partes, ignore_index=True)
        no_periodo = (tabela["instante"] >= inicio) & (tabela["instante"] < fim)
        return tabela[no_periodo].reset_index(drop=True)
