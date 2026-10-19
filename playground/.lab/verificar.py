"""Cria o bucket da aula 2 e confere se o laboratório está pronto."""

import os
import sys
from pathlib import Path

falhas = []


def conferir(item, teste):
    try:
        detalhe = teste()
        print(f"[OK] {item}: {detalhe}")
    except Exception as erro:  # noqa: BLE001 - a mensagem vai para o aluno
        falhas.append(item)
        print(f"[FALHA] {item}: {type(erro).__name__}: {erro}")


def postgres():
    import psycopg
    with psycopg.connect(os.environ["PG_DSN"], connect_timeout=10) as conexao:
        linhas = conexao.execute("SELECT count(*) FROM oficial.curva_horaria").fetchone()[0]
    assert linhas == 672, f"{linhas} linhas em oficial.curva_horaria, esperava 672"
    return f"oficial.curva_horaria com {linhas} linhas"


def clima(url):
    def teste():
        import httpx
        resposta = httpx.get(url, params={
            "latitude": -1.46, "longitude": -48.49,
            "start_date": "2025-01-01", "end_date": "2025-01-01",
            "hourly": "temperature_2m",
        }, timeout=30.0)
        resposta.raise_for_status()
        horas = len(resposta.json()["hourly"]["time"])
        assert horas == 24, f"{horas} horas para um dia"
        return "24 horas recebidas para um dia"
    return teste


def armazenamento():
    import boto3
    from botocore.config import Config
    s3 = boto3.client(
        "s3", endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1", config=Config(s3={"addressing_style": "path"}),
    )
    bucket = os.environ["S3_BUCKET"]
    s3.create_bucket(Bucket=bucket)
    return f"bucket {bucket} criado no RustFS"


def saida():
    teste = Path(__file__).resolve().parents[1] / "saida" / ".teste"
    teste.write_text("ok")
    teste.unlink()
    return "gravação permitida"


conferir("PostgreSQL", postgres)
conferir("Open-Meteo", clima("https://archive-api.open-meteo.com/v1/archive"))
conferir("API de clima local", clima(os.environ["CLIMA_URL"]))
conferir("armazenamento S3", armazenamento)
conferir("pasta saida/", saida)

if falhas:
    print("\nPendências: " + ", ".join(falhas) + ". Rode ./preparar.sh de novo; se continuar, chame o professor.")
    sys.exit(1)
print("\nTudo pronto para trabalhar.")
