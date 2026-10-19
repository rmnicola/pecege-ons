"""Solução da aula 2: as fontes e o pipeline do aluno com as transformações e o destino do gabarito.

    python .lab/gabarito/aula2/executar.py          # CSV
    python .lab/gabarito/aula2/executar.py --s3     # Parquet no RustFS
"""

import sys
from pathlib import Path

# transformacoes e destinos vêm desta pasta; fontes e pipeline, da pasta do aluno.
sys.path.append(str(Path(__file__).resolve().parents[3] / "aula2"))

from destinos import CsvLocal, ParquetS3  # noqa: E402
from fontes import CargaPostgres, ClimaApi  # noqa: E402
from pipeline import Transformada, executar  # noqa: E402
from transformacoes import limpar_carga, limpar_clima  # noqa: E402

destino = ParquetS3("carga_clima/dados.parquet") if "--s3" in sys.argv else CsvLocal("saida/dados_limpos.csv")

executar(
    fontes=[
        Transformada(CargaPostgres(), limpar_carga),
        Transformada(ClimaApi(), limpar_clima),
    ],
    destino=destino,
    inicio="2025-01-01",
    fim="2025-01-08",
)
