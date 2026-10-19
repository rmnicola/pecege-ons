"""Funções prontas da aula 2: não precisa mexer aqui."""

import os

import boto3
import httpx
import pandas as pd
import psycopg
from botocore.config import Config

CIDADES = {
    "N": ("Belém", -1.46, -48.49),
    "NE": ("Recife", -8.05, -34.88),
    "SE": ("São Paulo", -23.55, -46.63),
    "S": ("Porto Alegre", -30.03, -51.23),
}


def ler_carga():
    """A carga da cópia de laboratório, de 01 a 07/01/2025. A carga chega como texto."""
    with psycopg.connect(os.environ["PG_DSN"]) as conexao:
        linhas = conexao.execute(
            "SELECT id_subsistema, din_instante, val_cargaenergiahomwmed "
            "FROM laboratorio.curva_horaria").fetchall()
    carga = pd.DataFrame(linhas, columns=["id_subsistema", "instante", "carga_mwmed"])
    carga["instante"] = pd.to_datetime(carga["instante"])
    return carga


def ler_clima():
    """A temperatura da Open-Meteo, como na aula 1, de 01 a 07/01/2025."""
    tabelas = []
    for subsistema, (cidade, lat, lon) in CIDADES.items():
        resposta = httpx.get("https://archive-api.open-meteo.com/v1/archive", params={
            "latitude": lat, "longitude": lon,
            "start_date": "2025-01-01", "end_date": "2025-01-07",
            "hourly": "temperature_2m", "timezone": "America/Sao_Paulo",
        }, timeout=30.0).json()
        tabelas.append(pd.DataFrame({
            "id_subsistema": subsistema,
            "instante": pd.to_datetime(resposta["hourly"]["time"]),
            "temperatura_c": resposta["hourly"]["temperature_2m"],
        }))
    return pd.concat(tabelas)


def completar_horas(tabela):
    """Devolve a tabela com todas as horas de 01 a 07/01 para os quatro subsistemas.

    As horas que não vieram aparecem com a carga vazia.
    """
    horas = pd.date_range("2025-01-01 00:00", "2025-01-07 23:00", freq="h")
    grade = pd.DataFrame([(s, h) for s in ["N", "NE", "S", "SE"] for h in horas],
                         columns=["id_subsistema", "instante"])
    return grade.merge(tabela, on=["id_subsistema", "instante"], how="left")


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
