"""Solução da parte 2: destino Parquet no armazenamento S3 (RustFS)."""

import io
import os
from pathlib import Path

import boto3
import pandas as pd
from botocore.config import Config


class CsvLocal:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def gravar(self, dados):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados.to_csv(self.caminho, index=False)
        print(f"{len(dados)} linhas gravadas em {self.caminho}")


class ParquetS3:
    def __init__(self, chave, bucket=None):
        self.chave = chave
        self.bucket = bucket or os.environ["S3_BUCKET"]
        self.s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["S3_ENDPOINT"],
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_KEY"],
            region_name="us-east-1",
            config=Config(s3={"addressing_style": "path"}),
        )

    def gravar(self, dados):
        buffer = io.BytesIO()
        dados.to_parquet(buffer, index=False)
        self.s3.put_object(Bucket=self.bucket, Key=self.chave, Body=buffer.getvalue())
        # Confere lendo de volta: o objeto gravado é o que se esperava?
        objeto = self.s3.get_object(Bucket=self.bucket, Key=self.chave)
        lido = pd.read_parquet(io.BytesIO(objeto["Body"].read()))
        assert len(lido) == len(dados), "o Parquet lido tem outro número de linhas"
        assert list(lido.dtypes) == list(dados.dtypes), "os tipos mudaram no caminho"
        print(f"{len(dados)} linhas gravadas em s3://{self.bucket}/{self.chave}")
