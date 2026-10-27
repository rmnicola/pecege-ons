"""Desafio extra: as estratégias de fonte e de destino.

Fonte é qualquer classe com extrair(inicio, fim), que devolve uma tabela com
id_subsistema, instante e as colunas de valor. Destino é qualquer classe com
gravar(dados). CargaPostgres e CsvLocal estão prontas, como exemplo.
Nos passos 1 a 3, você escreve as outras três, reaproveitando o código das aulas 1 e 2.

Teste com:

    python aula2/extra/executar.py

Enunciado: https://rmnicola.github.io/pecege-ons/aulas/2026-10-22-etl-ii/desafio-extra/
"""

import io
import os
from pathlib import Path

import boto3
import httpx
import pandas as pd
import psycopg
from botocore.config import Config
from psycopg.rows import dict_row


# Fontes ----------------------------------------------------------------------

class CargaPostgres:
    """Pronta: a carga oficial do banco, como na aula 1."""

    SQL = """SELECT id_subsistema, din_instante, val_cargaenergiahomwmed
             FROM oficial.curva_horaria
             WHERE din_instante >= %(inicio)s AND din_instante < %(fim)s"""

    def extrair(self, inicio, fim):
        with psycopg.connect(os.environ["PG_DSN"], row_factory=dict_row) as conexao:
            linhas = conexao.execute(self.SQL, {"inicio": inicio, "fim": fim}).fetchall()
        carga = pd.DataFrame(linhas).rename(columns={
            "din_instante": "instante", "val_cargaenergiahomwmed": "carga_mwmed"})
        carga["carga_mwmed"] = carga["carga_mwmed"].astype(float)
        return carga


# Passo 1. ClimaOpenMeteo
# A temperatura de uma cidade por subsistema, da Open-Meteo: é o passo 2 do
# aula1/combinar.py, dentro de um método. Devolva id_subsistema, instante e temperatura_c.
# Atenção ao fim: a Open-Meteo inclui o último dia (end_date); o contrato não inclui.
#     pd.Timestamp  https://pandas.pydata.org/docs/reference/api/pandas.Timestamp.html
#     pd.concat     https://pandas.pydata.org/docs/reference/api/pandas.concat.html

class ClimaOpenMeteo:
    URL = "https://archive-api.open-meteo.com/v1/archive"
    CIDADES = {
        "N": ("Belém", -1.46, -48.49),
        "NE": ("Recife", -8.05, -34.88),
        "SE": ("São Paulo", -23.55, -46.63),
        "S": ("Porto Alegre", -30.03, -51.23),
    }

    def extrair(self, inicio, fim):
        return None  # troque


# Passo 2. CargaLaboratorio
# A carga com falhas da aula 2, já arrumada. O SQL lê tudo como texto, como o aula2/fontes.py.
# Converta o instante para data, filtre o período e aplique os passos 1 a 5 do seu
# aula2/limpar.py. Devolva id_subsistema, instante, carga_mwmed e carga_imputada.
# Dica: ordene por subsistema e instante antes de interpolar.
#     sort_values  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.sort_values.html

class CargaLaboratorio:
    SQL = """SELECT id_subsistema, din_instante, val_cargaenergiahomwmed
             FROM laboratorio.curva_horaria"""

    def extrair(self, inicio, fim):
        return None  # troque


# Destinos --------------------------------------------------------------------

class CsvLocal:
    """Pronta: grava a tabela num CSV da pasta saida/."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def gravar(self, dados):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados.to_csv(self.caminho, index=False)
        print(f"{len(dados)} linhas gravadas em {self.caminho}")


# Passo 3. ParquetS3
# Grava a tabela em Parquet no armazenamento S3 (RustFS), no bucket da aula 2.
# O cliente já está pronto em self.s3. Grave o Parquet na memória (io.BytesIO)
# e envie com put_object.
#     to_parquet  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html
#     put_object  https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html

class ParquetS3:
    def __init__(self, chave):
        self.chave = chave
        self.bucket = os.environ["S3_BUCKET"]
        self.s3 = boto3.client(
            "s3", endpoint_url=os.environ["S3_ENDPOINT"],
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_KEY"],
            region_name="us-east-1", config=Config(s3={"addressing_style": "path"}),
        )

    def gravar(self, dados):
        pass  # troque
