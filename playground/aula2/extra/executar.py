"""Desafio extra: monte o pipeline escolhendo as estratégias.

    python aula2/extra/executar.py

Do jeito que está, ele lê a carga oficial e grava saida/extra.csv.

Passo 4. Trocar as peças, sem mexer em pipeline.py:
    1. Acrescente ClimaOpenMeteo() às fontes e rode: o CSV ganha temperatura_c.
    2. Troque CargaPostgres() por CargaLaboratorio() e rode: a carga vem da cópia com falhas, já arrumada.
    3. Troque o destino por ParquetS3("extra/carga_clima.parquet") e rode.
O certo, no fim: 672 linhas e 0 valores vazios.
"""

from estrategias import CargaPostgres, CsvLocal  # importe também as suas estratégias
from pipeline import executar

executar(
    fontes=[CargaPostgres()],
    destino=CsvLocal("saida/extra.csv"),
    inicio="2025-01-01",
    fim="2025-01-08",
)
