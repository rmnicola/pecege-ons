"""Funções prontas da aula 2: não precisa mexer aqui."""

import os

import boto3
import pandas as pd
import psycopg
from botocore.config import Config


def ler_carga():
    """A carga da cópia de laboratório, de 01 a 07/01/2025. A carga chega como texto."""
    with psycopg.connect(os.environ["PG_DSN"]) as conexao:
        linhas = conexao.execute(
            "SELECT id_subsistema, din_instante, val_cargaenergiahomwmed "
            "FROM laboratorio.curva_horaria").fetchall()
    carga = pd.DataFrame(linhas, columns=["id_subsistema", "instante", "carga_mwmed"])
    carga["instante"] = pd.to_datetime(carga["instante"])
    return carga


def enviar_para_s3(arquivo, chave):
    """Envia um arquivo para o bucket da aula no armazenamento S3 (RustFS)."""
    s3 = boto3.client(
        "s3", endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1", config=Config(s3={"addressing_style": "path"}),
    )
    s3.upload_file(arquivo, os.environ["S3_BUCKET"], chave)
    print(f"enviado para s3://{os.environ['S3_BUCKET']}/{chave}")
