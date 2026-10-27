"""Gabarito do desafio extra da aula 2: as estratégias do gabarito no pipeline do aluno.

    python .lab/gabarito/aula2/extra/executar.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[4] / "aula2" / "extra"))

from estrategias import CargaLaboratorio, ClimaOpenMeteo, ParquetS3  # noqa: E402
from pipeline import executar  # noqa: E402

executar(
    fontes=[CargaLaboratorio(), ClimaOpenMeteo()],
    destino=ParquetS3("extra/carga_clima.parquet"),
    inicio="2025-01-01",
    fim="2025-01-08",
)
