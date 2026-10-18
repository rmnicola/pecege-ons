#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes unitarios puros (SEM Docker/PostgreSQL).

Cobrem:
  * parsing numerico finito ('nan'/'inf' nao sao medicao valida);
  * normalizacao de id/nome;
  * classificacao de duplicatas por chave NORMALIZADA, comparando TODAS as
    colunas de negocio (incluindo nome): aliases de id e datas ISO que
    escondem conflitos.

Rodam com `python tests/test_unit_sem_docker.py` (host, sem psycopg) ou via
pytest dentro do container etl.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _util import (  # noqa: E402
    classificar_grupos_chave,
    normalizar_id,
    normalizar_nome,
    parse_instante,
    parse_numero,
)


# ------------------------------------------------------------------ numeros
def test_parse_numero_finito():
    assert parse_numero("123.45") == (123.45, "ok")
    assert parse_numero(" 7 ") == (7.0, "ok")
    assert parse_numero("123,45") == (123.45, "decimal_virgula")


def test_parse_numero_nao_finito():
    for texto in ("nan", "+nan", "-nan", "inf", "+inf", "-inf", "Infinity", "1e999"):
        num, status = parse_numero(texto)
        assert num is None, f"{texto!r} nao pode virar medicao"
        assert status == "nao_finito", f"{texto!r} -> {status!r}"


def test_parse_numero_ausente_invalido():
    assert parse_numero("") == (None, "vazio")
    assert parse_numero(None) == (None, "vazio")
    for texto in ("N/A", "NA", "-", "--", "NULL", "abc", "1.2.3", "1,2,3"):
        num, status = parse_numero(texto)
        assert num is None
        assert status == "invalido", f"{texto!r} -> {status!r}"


# --------------------------------------------------------------- instante
def test_parse_instante_formatos():
    assert parse_instante("2025-01-02 03:00:00") is not None
    assert parse_instante("2025-01-02T03:00:00") is not None
    assert parse_instante("02/01/2025 03:00") is None
    assert parse_instante("") is None
    assert parse_instante(None) is None


# ------------------------------------------------------------- categorias
def test_normalizacao_categorias():
    assert normalizar_id(" s ") == "S"
    assert normalizar_id("n") == "N"
    assert normalizar_nome("nordeste") == "NORDESTE"
    assert normalizar_nome("SUDESTE/CENTRO-OESTE") == "SUDESTE"
    assert normalizar_nome("SUDESTE") == "SUDESTE"


# --------------------------------------------------- duplicatas por chave
COLS = ["nom_subsistema", "val_carga"]


def _grupo(rows):
    gs = classificar_grupos_chave(rows, COLS, "id_subsistema", "din_instante")
    assert len(gs) == 1, f"esperava 1 grupo, veio {gs}"
    return gs[0]


def test_alias_id_e_data_iso_mesmo_conteudo_e_duplicata_exata():
    rows = [
        {"id_subsistema": " s ", "nom_subsistema": "SUL",
         "din_instante": "2025-01-02 03:00:00", "val_carga": "10288.47"},
        {"id_subsistema": "S", "nom_subsistema": "SUL",
         "din_instante": "2025-01-02T03:00:00", "val_carga": "10288.47"},
    ]
    g = _grupo(rows)
    assert g["tipo"] == "duplicata_exata"
    assert g["id_normalizado"] == "S"
    assert g["instante_normalizado"] == "2025-01-02 03:00:00"
    assert g["colunas_divergentes"] == 0


def test_alias_id_e_data_iso_nomes_diferentes_e_conflito():
    rows = [
        {"id_subsistema": " s ", "nom_subsistema": "SUL",
         "din_instante": "2025-01-02 03:00:00", "val_carga": "10288.47"},
        {"id_subsistema": "S", "nom_subsistema": "SUDESTE",
         "din_instante": "2025-01-02T03:00:00", "val_carga": "10288.47"},
    ]
    g = _grupo(rows)
    assert g["tipo"] == "conflito_chave"
    assert g["colunas_divergentes"] == 1
    assert "nom_subsistema" in g["colunas_divergentes_lista"]


def test_alias_id_e_data_iso_medidas_diferentes_e_conflito():
    rows = [
        {"id_subsistema": " n", "nom_subsistema": "NORTE",
         "din_instante": "2025-01-06 08:00:00", "val_carga": "7356.342"},
        {"id_subsistema": "N", "nom_subsistema": "NORTE",
         "din_instante": "2025-01-06T08:00:00", "val_carga": "9999.999"},
    ]
    g = _grupo(rows)
    assert g["tipo"] == "conflito_chave"
    assert "val_carga" in g["colunas_divergentes_lista"]


def test_horas_diferentes_nao_formam_grupo():
    rows = [
        {"id_subsistema": "S", "nom_subsistema": "SUL",
         "din_instante": "2025-01-02 03:00:00", "val_carga": "1"},
        {"id_subsistema": " s ", "nom_subsistema": "SUL",
         "din_instante": "2025-01-02T04:00:00", "val_carga": "1"},
    ]
    assert classificar_grupos_chave(rows, COLS, "id_subsistema", "din_instante") == []


def _executar_todos():
    testes = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("test_") and callable(f)]
    falhas = 0
    for nome, fn in testes:
        try:
            fn()
            print(f"ok   {nome}")
        except AssertionError as exc:
            falhas += 1
            print(f"FALHA {nome}: {exc}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes unitarios passaram")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(_executar_todos())
