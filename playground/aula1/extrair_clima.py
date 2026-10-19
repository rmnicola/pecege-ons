"""Extrai a temperatura horária de uma cidade por subsistema (Open-Meteo).

Simplificação didática: a temperatura de uma cidade não representa
o subsistema inteiro.

    python aula1/extrair_clima.py
"""

import httpx

URL = "https://archive-api.open-meteo.com/v1/archive"

CIDADES = {
    "N": ("Belém", -1.46, -48.49),
    "NE": ("Recife", -8.05, -34.88),
    "SE": ("São Paulo", -23.55, -46.63),
    "S": ("Porto Alegre", -30.03, -51.23),
}


def extrair(evento, lat, lon):
    resposta = httpx.get(URL, params={
        "latitude": lat, "longitude": lon,
        "start_date": evento["inicio"],
        "end_date": evento["fim"],
        "hourly": "temperature_2m",
        "timezone": "America/Sao_Paulo",
    }, timeout=30.0)
    resposta.raise_for_status()
    return resposta.json()


if __name__ == "__main__":
    evento = {"inicio": "2025-01-01", "fim": "2025-01-08"}
    for subsistema, (cidade, lat, lon) in CIDADES.items():
        dados = extrair(evento, lat, lon)
        horas = dados["hourly"]["time"]
        unidade = dados["hourly_units"]["temperature_2m"]
        print(f"{subsistema} ({cidade}): {len(horas)} horas, de {horas[0]} a {horas[-1]}, unidade {unidade}")
