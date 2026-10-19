"""Destinos que cumprem o contrato: gravar(dados)."""

import os
from pathlib import Path


class CsvLocal:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def gravar(self, dados):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados.to_csv(self.caminho, index=False)
        print(f"{len(dados)} linhas gravadas em {self.caminho}")


class ParquetS3:
    """Desafio, parte 2: gravar os dados como Parquet no armazenamento S3 (RustFS).

    Configuração no ambiente: S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY e S3_BUCKET.
    Console web para conferir o resultado: http://localhost:9001/rustfs/console/
    (usuário ons_lab, senha ons_lab_s3)
    """

    def __init__(self, chave, bucket=None):
        self.chave = chave  # caminho do objeto dentro do bucket, ex.: "carga_clima/dados.parquet"
        self.bucket = bucket or os.environ["S3_BUCKET"]

    def gravar(self, dados):
        # Dicas:
        # - O pandas grava Parquet num arquivo ou num buffer em memória (io.BytesIO).
        # - boto3.client("s3", endpoint_url=...) fala com qualquer serviço S3, não só a AWS.
        #   Fora da AWS, use region_name="us-east-1" e
        #   config=botocore.config.Config(s3={"addressing_style": "path"}).
        # - put_object grava um objeto: bucket, chave e o conteúdo em bytes.
        # - Depois de gravar, leia de volta e confira: mesmas linhas, mesmos tipos?
        raise NotImplementedError("ParquetS3.gravar")
