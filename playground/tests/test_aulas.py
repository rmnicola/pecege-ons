#!/usr/bin/env python3
"""Testes dos fluxos das aulas: API de clima local, soluções da aula 1 e da aula 2.

Rodam dentro do container etl (pytest), com os serviços do compose no ar.
Não dependem de internet: a aula 1 é testada no modo --offline.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import boto3
import pandas as pd
from botocore.config import Config

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "servicos"))
import api_clima  # noqa: E402


def rodar(*args):
    return subprocess.run([sys.executable, *args], cwd=RAIZ, capture_output=True, text=True, check=False)


def test_api_clima_aplica_os_defeitos():
    resumo = {}
    for sub in api_clima.CIDADES:
        r = api_clima._filtrar(api_clima._com_defeitos(sub, api_clima.RESPOSTAS[sub]), "2025-01-01", "2025-01-07")
        horas, temps = r["hourly"]["time"], r["hourly"]["temperature_2m"]
        resumo[sub] = (len(horas), sum(t is None for t in temps), temps.count(-999.0),
                       r["hourly_units"]["temperature_2m"], max(t for t in temps if t is not None))
    assert resumo["N"][:2] == (168, 3)
    assert resumo["NE"][2] == 2
    assert resumo["SE"][3] == "°F"
    assert resumo["S"][0] == 169 and resumo["S"][4] == 61.3
    # As respostas reais salvas continuam sem defeitos.
    assert all(t is not None for t in api_clima.RESPOSTAS["N"]["hourly"]["temperature_2m"])


def test_aula1_componivel_offline():
    r = rodar("gabarito/aula1/componivel/executar.py", "--offline")
    assert r.returncode == 0, r.stderr
    dados = pd.read_csv(RAIZ / "saida" / "dados.csv")
    assert len(dados) == 672
    assert dados.notna().all().all()


def test_aula2_solucao_csv():
    r = rodar("gabarito/aula2/executar.py")
    assert r.returncode == 0, r.stderr
    dados = pd.read_csv(RAIZ / "saida" / "dados_limpos.csv")
    assert len(dados) == 672
    assert dados.notna().all().all()
    assert dados["carga_mwmed_imputado"].sum() == 5
    assert dados["temperatura_c_imputado"].sum() == 6
    assert dados.groupby("id_subsistema")["temperatura_c"].max().max() < 40
    assert dados.groupby("id_subsistema")["carga_mwmed"].max().max() < 100_000


def test_aula2_solucao_parquet_no_s3():
    r = rodar("gabarito/aula2/executar.py", "--s3")
    assert r.returncode == 0, r.stderr
    s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"],
                      aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                      aws_secret_access_key=os.environ["S3_SECRET_KEY"],
                      region_name="us-east-1", config=Config(s3={"addressing_style": "path"}))
    corpo = s3.get_object(Bucket=os.environ["S3_BUCKET"], Key="carga_clima/dados.parquet")["Body"].read()
    lido = pd.read_parquet(io.BytesIO(corpo))
    assert len(lido) == 672
    assert lido["temperatura_c_imputado"].sum() == 6


def test_aula2_esqueleto_para_na_transformacao():
    r = rodar("aluno/aula2/executar.py")
    assert r.returncode != 0
    assert "NotImplementedError: limpar_carga" in r.stderr
