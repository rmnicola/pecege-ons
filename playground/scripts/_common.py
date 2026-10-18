#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades compartilhadas pelos scripts de ETL Pecege-ONS.

Padroes:
  * conexoes separadas para fonte-balanco, fonte-curva e destino;
  * conexao com retry (os servicos sobem junto com o ETL);
  * leitura de CSV como texto (staging), sem inferir tipos silenciosamente;
  * parsing explicito de data/hora e numero, registrando o motivo quando falha;
  * logs e resumos em resultados/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg

from _util import (  # noqa: F401  (reexportado para os scripts)
    AGREGADOS,
    NOMES_CANONICOS,
    SUBSISTEMAS_SISTEMA,
    chave_normalizada,
    classificar_grupos_chave,
    normalizar_id,
    normalizar_nome,
    parse_instante,
    parse_numero,
)

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
ROOT = Path(os.environ.get("PLAYGROUND_DIR", Path(__file__).resolve().parents[1]))
OFICIAL_DIR = ROOT / "data" / "oficial"
LAB_DIR = ROOT / "data" / "laboratorio"
RESULT_DIR = ROOT / "resultados"

RECORTE_INI = "2025-01-01 00:00:00"
RECORTE_FIM = "2025-01-08 00:00:00"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def get_logger(nome: str) -> logging.Logger:
    logger = logging.getLogger(nome)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
    logger.propagate = False
    return logger


# ---------------------------------------------------------------------------
# Conexoes
# ---------------------------------------------------------------------------
def _cfg(prefixo: str) -> dict:
    return {
        "host": os.environ.get(f"{prefixo}_HOST", prefixo.lower().replace("_", "-")),
        "port": int(os.environ.get(f"{prefixo}_PORT", "5432")),
        "dbname": os.environ.get(f"{prefixo}_DB", prefixo.lower()),
        "user": os.environ.get(f"{prefixo}_USER", "ons_lab"),
        "password": os.environ.get(f"{prefixo}_PASSWORD", "ons_lab"),
    }


def conectar(prefixo: str, tentativas: int = 30, espera: float = 2.0):
    """Conecta a um servico pelo prefixo de variaveis de ambiente."""
    cfg = _cfg(prefixo)
    logger = get_logger("conectar")
    ultimo = None
    for i in range(1, tentativas + 1):
        try:
            conn = psycopg.connect(**cfg)
            logger.info(
                "conectado a %s (%s/%s) apos %d tentativa(s)",
                prefixo, cfg["host"], cfg["dbname"], i,
            )
            return conn
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
            logger.warning(
                "falha ao conectar em %s (%s): %s. Retentando em %.1fs (%d/%d)",
                prefixo, cfg["host"], exc, espera, i, tentativas,
            )
            time.sleep(espera)
    raise SystemExit(f"nao foi possivel conectar em {prefixo}: {ultimo!r}")


def conectar_balanco(**kw):
    return conectar("FONTE_BALANCO", **kw)


def conectar_curva(**kw):
    return conectar("FONTE_CURVA", **kw)


def conectar_destino(**kw):
    return conectar("DESTINO", **kw)


def descricao_conexao(prefixo: str) -> dict:
    cfg = _cfg(prefixo)
    return {"host": cfg["host"], "dbname": cfg["dbname"], "user": cfg["user"]}


# ---------------------------------------------------------------------------
# DDL / carga
# ---------------------------------------------------------------------------
def garantir_schema(conn, schema: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    conn.commit()


def executar_ddl(conn, sql: str, commit: bool = True) -> None:
    with conn.cursor() as cur:
        cur.execute(sql)
    if commit:
        conn.commit()


def copiar_linhas(conn, tabela: str, colunas: list[str], linhas: list[tuple],
                  commit: bool = True) -> int:
    """COPY rapido mantendo os valores como texto (sem inferencia de tipo)."""
    if not linhas:
        return 0
    colunas_sql = ", ".join(f'"{c}"' for c in colunas)
    sql = f"COPY {tabela} ({colunas_sql}) FROM STDIN"
    with conn.cursor() as cur:
        with cur.copy(sql) as copy:
            for linha in linhas:
                copy.write_row(linha)
    if commit:
        conn.commit()
    return len(linhas)


META_COLUNAS = [
    ("_cenario", "text"),
    ("_fonte_servico", "text"),
    ("_banco_fonte", "text"),
    ("_schema_origem", "text"),
    ("_tabela_origem", "text"),
    ("_arquivo_origem", "text"),
    ("_origem_url", "text"),
    ("_sha256_recorte", "text"),
    ("_sha256_arquivo_origem", "text"),
    ("_extraido_em", "timestamptz"),
]


def ddl_colunas_meta() -> str:
    return ",\n".join(f"    {nome} {tipo}" for nome, tipo in META_COLUNAS)


def extrair(conn_origem, conn_destino, select_sql: str, destino: str,
            colunas: list[str], meta: dict) -> int:
    """Le do banco de origem e carrega no destino preservando valores crus.

    Como origem e destino sao servicos PostgreSQL distintos, buscamos os
    registros e usamos COPY no destino. O dicionario `meta` e gravado em
    colunas de rastreabilidade.
    """
    with conn_origem.cursor() as cur:
        cur.execute(select_sql)
        registros = cur.fetchall()
    meta_vals = tuple(meta[nome] for nome, _ in META_COLUNAS)
    linhas = [tuple(r) + meta_vals for r in registros]
    return copiar_linhas(conn_destino, destino, colunas + [n for n, _ in META_COLUNAS], linhas)


def metadados_origem(prefixo: str, schema: str, tabela: str, arquivo: str,
                     fonte_prov: str, cenario: str) -> dict:
    prov = carregar_proveniencia()
    rec = prov.get("fontes", {}).get(fonte_prov, {})
    return {
        "_cenario": cenario,
        "_fonte_servico": descricao_conexao(prefixo)["host"],
        "_banco_fonte": descricao_conexao(prefixo)["dbname"],
        "_schema_origem": schema,
        "_tabela_origem": tabela,
        "_arquivo_origem": rec.get("recorte_arquivo", arquivo),
        "_origem_url": rec.get("csv_url"),
        "_sha256_recorte": rec.get("recorte_sha256"),
        "_sha256_arquivo_origem": rec.get("sha256_arquivo_origem"),
        "_extraido_em": agora_utc(),
    }


def executar_copy_da_tabela(conn, origem: str, destino: str, colunas: list[str],
                            onde: str = "TRUE") -> int:
    """INSERT ... SELECT (para mover entre schemas do mesmo banco)."""
    colunas_sql = ", ".join(f'"{c}"' for c in colunas)
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {destino} ({colunas_sql}) "
            f"SELECT {colunas_sql} FROM {origem} WHERE {onde}"
        )
        n = cur.rowcount
    conn.commit()
    return n


# ---------------------------------------------------------------------------
# Leitura de CSV / proveniencia
# ---------------------------------------------------------------------------
def ler_csv(caminho: Path, separador: str = ";") -> tuple[list[str], list[list[str]]]:
    """Le CSV como texto puro, preservando o conteudo original das celulas."""
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f, delimiter=separador)
        cabecalho = next(leitor)
        linhas = [linha for linha in leitor if linha and any(c != "" for c in linha)]
    return cabecalho, linhas


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def carregar_proveniencia() -> dict:
    caminho = OFICIAL_DIR / "PROVENIENCIA.json"
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Parsing e chaves: implementados em _util.py (sem psycopg) e
# reexportados no topo deste modulo.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Saida de relatorios
# ---------------------------------------------------------------------------
def salvar_json(nome: str, dados) -> Path:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    caminho = RESULT_DIR / nome
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return caminho


def salvar_texto(nome: str, texto: str) -> Path:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    caminho = RESULT_DIR / nome
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def argumento_cenario(argv=None) -> str:
    import argparse

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--cenario", required=True, choices=["aula1", "aula2"])
    args = parser.parse_args(argv)
    return args.cenario
