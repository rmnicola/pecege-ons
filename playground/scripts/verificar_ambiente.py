#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica se o ambiente das aulas ETL I e II esta pronto.

Confere, em ordem: bibliotecas Python, conexao com a fonte PostgreSQL
(PG_DSN), acesso a API Historical Weather da Open-Meteo, a API de clima
local e o armazenamento S3 da aula ETL II, e gravacao na pasta saida/.
Nao altera dados das fontes.

Uso:
    docker compose run --rm etl python scripts/verificar_ambiente.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

SAIDA = Path(__file__).resolve().parents[1] / "saida"
URL_CLIMA = "https://archive-api.open-meteo.com/v1/archive"

resultados: list[tuple[str, bool, str]] = []


def registrar(item: str, ok: bool, detalhe: str) -> None:
    resultados.append((item, ok, detalhe))
    print(f"[{'OK' if ok else 'FALHA'}] {item}: {detalhe}")


def verificar_bibliotecas() -> None:
    faltando = []
    for nome in ("psycopg", "httpx", "pandas", "pyarrow", "boto3"):
        try:
            __import__(nome)
        except ImportError:
            faltando.append(nome)
    if faltando:
        registrar("bibliotecas", False,
                  f"faltando {', '.join(faltando)}; rode: docker compose build etl")
    else:
        registrar("bibliotecas", True, "psycopg, httpx, pandas, pyarrow e boto3 disponiveis")


def verificar_postgres() -> None:
    dsn = os.environ.get("PG_DSN")
    if not dsn:
        registrar("PostgreSQL", False, "variavel PG_DSN ausente; confira compose.yaml")
        return
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=10) as conexao:
            linhas = conexao.execute(
                "SELECT count(*) FROM oficial.curva_horaria"
            ).fetchone()[0]
    except Exception as erro:  # noqa: BLE001 - mensagem para o aluno
        registrar("PostgreSQL", False,
                  f"{type(erro).__name__}: {erro}".strip()
                  + " | rode: docker compose up -d --wait e o script 00_carregar_fontes.py")
        return
    if linhas == 0:
        registrar("PostgreSQL", False,
                  "tabela oficial.curva_horaria vazia; rode scripts/00_carregar_fontes.py")
    else:
        registrar("PostgreSQL", True, f"oficial.curva_horaria com {linhas} linhas")


def verificar_open_meteo() -> None:
    try:
        import httpx
        resposta = httpx.get(URL_CLIMA, params={
            "latitude": -15.79, "longitude": -47.88,
            "start_date": "2025-01-01", "end_date": "2025-01-01",
            "hourly": "temperature_2m", "timezone": "UTC",
        }, timeout=30.0)
        resposta.raise_for_status()
        horas = len(resposta.json()["hourly"]["time"])
    except Exception as erro:  # noqa: BLE001 - mensagem para o aluno
        registrar("Open-Meteo", False,
                  f"{type(erro).__name__}: {erro}".strip()
                  + " | confira acesso HTTPS a archive-api.open-meteo.com")
        return
    registrar("Open-Meteo", horas == 24, f"{horas} horas recebidas para um dia")


def verificar_api_local() -> None:
    url = os.environ.get("CLIMA_URL")
    if not url:
        registrar("API de clima local", False, "variavel CLIMA_URL ausente; confira compose.yaml")
        return
    try:
        import httpx
        resposta = httpx.get(url, params={
            "latitude": -1.46, "longitude": -48.49,
            "start_date": "2025-01-01", "end_date": "2025-01-01",
            "hourly": "temperature_2m",
        }, timeout=10.0)
        resposta.raise_for_status()
        horas = len(resposta.json()["hourly"]["time"])
    except Exception as erro:  # noqa: BLE001 - mensagem para o aluno
        registrar("API de clima local", False, f"{type(erro).__name__}: {erro} | rode ./preparar.sh de novo")
        return
    registrar("API de clima local", horas == 24, f"{horas} horas recebidas para um dia")


def verificar_armazenamento() -> None:
    try:
        import boto3
        from botocore.config import Config
        s3 = boto3.client(
            "s3", endpoint_url=os.environ["S3_ENDPOINT"],
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_KEY"],
            region_name="us-east-1", config=Config(s3={"addressing_style": "path"}),
        )
        bucket = os.environ["S3_BUCKET"]
        s3.head_bucket(Bucket=bucket)
    except Exception as erro:  # noqa: BLE001 - mensagem para o aluno
        registrar("armazenamento S3", False, f"{type(erro).__name__}: {erro} | rode ./preparar.sh de novo")
        return
    registrar("armazenamento S3", True, f"bucket {bucket} disponivel no RustFS")


def verificar_saida() -> None:
    teste = SAIDA / ".teste_gravacao"
    try:
        SAIDA.mkdir(exist_ok=True)
        teste.write_text("ok", encoding="utf-8")
        teste.unlink()
    except OSError as erro:
        registrar("pasta saida/", False,
                  f"{erro} | crie o .env com ETL_UID/ETL_GID (veja as instrucoes)")
        return
    registrar("pasta saida/", True, "gravacao permitida")


def main() -> int:
    print(f"Python {sys.version.split()[0]}")
    verificar_bibliotecas()
    verificar_postgres()
    verificar_open_meteo()
    verificar_api_local()
    verificar_armazenamento()
    verificar_saida()
    falhas = [item for item, ok, _ in resultados if not ok]
    print()
    if falhas:
        print("Ambiente com pendencias: " + ", ".join(falhas))
        return 1
    print("Ambiente pronto para a aula.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
