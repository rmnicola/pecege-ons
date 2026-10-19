"""Solução do desafio da aula 1: carga + temperatura em saida/dados.csv.

    python .lab/gabarito/aula1/combinar.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "aula1"))
from extrair_carga import extrair as extrair_carga  # noqa: E402
from extrair_clima import CIDADES, extrair as extrair_clima  # noqa: E402

EVENTO = {"inicio": "2025-01-01", "fim": "2025-01-08"}
# A Open-Meteo inclui o último dia: o clima vai até 07/01
EVENTO_CLIMA = {"inicio": "2025-01-01", "fim": "2025-01-07"}

carga = pd.DataFrame(extrair_carga(EVENTO)).rename(columns={
    "din_instante": "instante", "val_cargaenergiahomwmed": "carga_mwmed"})
carga["carga_mwmed"] = carga["carga_mwmed"].astype(float)

tabelas = []
for subsistema, (cidade, lat, lon) in CIDADES.items():
    resposta = extrair_clima(EVENTO_CLIMA, lat, lon)
    tabelas.append(pd.DataFrame({
        "id_subsistema": subsistema,
        "instante": pd.to_datetime(resposta["hourly"]["time"]),
        "temperatura_c": resposta["hourly"]["temperature_2m"],
    }))
clima = pd.concat(tabelas)

dados = carga.merge(clima, on=["id_subsistema", "instante"], how="left")

print(len(dados), "linhas")
print(dados["temperatura_c"].isna().sum(), "horas sem temperatura")

dados.to_csv("saida/dados.csv", index=False)
