"""Monta o pipeline com as peças escolhidas.

    python .lab/gabarito/aula1/componivel/executar.py
    python .lab/gabarito/aula1/componivel/executar.py --offline
"""

import sys

from destinos import CsvLocal
from fontes import CargaPostgres, ClimaArquivo, ClimaOpenMeteo
from pipeline import executar

clima = ClimaArquivo(".lab/open-meteo") if "--offline" in sys.argv else ClimaOpenMeteo()

executar(
    fontes=[CargaPostgres(), clima],
    destino=CsvLocal("saida/dados.csv"),
    inicio="2025-01-01",
    fim="2025-01-08",
)
