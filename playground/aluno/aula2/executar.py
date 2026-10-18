"""Monta o pipeline da aula 2.

    docker compose run --rm etl python aluno/aula2/executar.py

Parte 1: complete transformacoes.py e gere saida/dados_limpos.csv.
Parte 2: complete ParquetS3 em destinos.py e troque o destino abaixo.
"""

from destinos import CsvLocal, ParquetS3  # noqa: F401
from fontes import CargaPostgres, ClimaApi
from pipeline import Transformada, executar
from transformacoes import limpar_carga, limpar_clima

executar(
    fontes=[
        Transformada(CargaPostgres(), limpar_carga),
        Transformada(ClimaApi(), limpar_clima),
    ],
    destino=CsvLocal("saida/dados_limpos.csv"),
    # Parte 2: destino=ParquetS3("carga_clima/dados.parquet"),
    inicio="2025-01-01",
    fim="2025-01-08",
)
