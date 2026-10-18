"""Solução do desafio da aula 1: carga + temperatura em saida/dados.csv.

    docker compose run --rm etl python gabarito/aula1/combinar.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aluno" / "aula1"))
from extrair_carga import extrair as extrair_carga  # noqa: E402
from extrair_clima import CIDADES, extrair as extrair_clima  # noqa: E402

EVENTO = {"inicio": "2025-01-01", "fim": "2025-01-08"}
# Na Open-Meteo, end_date inclui o último dia: o mesmo período é 01 a 07.
EVENTO_CLIMA = {"inicio": "2025-01-01", "fim": "2025-01-07"}

carga = pd.DataFrame(extrair_carga(EVENTO)).rename(columns={
    "din_instante": "instante", "val_cargaenergiahomwmed": "carga_mwmed"})
carga["carga_mwmed"] = carga["carga_mwmed"].astype(float)

partes = []
for sub, (cidade, lat, lon) in CIDADES.items():
    resposta = extrair_clima(EVENTO_CLIMA, lat, lon)
    partes.append(pd.DataFrame({
        "id_subsistema": sub,
        "instante": pd.to_datetime(resposta["hourly"]["time"]),
        "temperatura_c": resposta["hourly"]["temperature_2m"],
    }))
clima = pd.concat(partes, ignore_index=True)

dados = carga.merge(clima, on=["id_subsistema", "instante"],
                    how="left", validate="one_to_one")

assert len(dados) == len(carga), "a junção mudou o número de linhas"
assert dados["temperatura_c"].notna().all(), "há horas sem temperatura"

dados = dados.sort_values(["id_subsistema", "instante"])
dados.to_csv("saida/dados.csv", index=False)
print(f"{len(dados)} linhas gravadas em saida/dados.csv")
