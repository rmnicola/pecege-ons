#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes de invariantes do laboratorio Pecege-ONS.

Rodam dentro do container etl (pytest). Pressupoem que o pipeline de fontes
e integracao (00 a 03) ja foi executado por tests/run_tests.sh. Cada teste verifica um invariante
significativo com contagens reais dos dados.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import _common as U  # noqa: E402


def escalar(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]


def conjunto(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        return {r[0] for r in cur.fetchall()}


@pytest.fixture(scope="module")
def dest():
    c = U.conectar_destino()
    yield c
    c.close()


@pytest.fixture(scope="module")
def bal():
    c = U.conectar_balanco()
    yield c
    c.close()


@pytest.fixture(scope="module")
def cur():
    c = U.conectar_curva()
    yield c
    c.close()


# ---------------------------------------------------------------- integracao
def test_aula1_integracao_linhas_e_unicidade(dest):
    total = escalar(dest, "SELECT count(*) FROM aula1.integrado")
    subs = escalar(dest, "SELECT count(*) FROM aula1.integrado "
                         "WHERE tipo_subsistema='subsistema'")
    sin = escalar(dest, "SELECT count(*) FROM aula1.integrado "
                        "WHERE tipo_subsistema='agregado_sin'")
    assert total == 840, f"esperado 840 linhas integradas, veio {total}"
    assert subs == 672, f"esperado 4x168=672 subsistemas, veio {subs}"
    assert sin == 168, f"esperado 168 linhas do agregado SIN, veio {sin}"
    dups = escalar(dest, "SELECT count(*) FROM (SELECT id_subsistema, din_instante "
                         "FROM aula1.integrado GROUP BY 1,2 HAVING count(*)>1) t")
    assert dups == 0, "a chave (id_subsistema, din_instante) deve ser unica"
    nulos = escalar(dest, "SELECT count(*) FROM aula1.integrado "
                          "WHERE id_subsistema IS NULL OR din_instante IS NULL")
    assert nulos == 0


def test_medidas_de_carga_mantidas_separadas(dest):
    col = escalar(
        dest,
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema='aula1' AND table_name='integrado' "
        "AND column_name IN ('val_carga','val_cargaenergiahomwmed')",
    )
    assert col == 2
    divergentes = escalar(dest, "SELECT count(*) FROM aula1.integrado "
                                "WHERE tem_curva AND NOT carga_coincide")
    assert divergentes == 0  # no recorte de 2025 as duas medidas coincidem


# --------------------------------------------------------------- idempotencia
def test_idempotencia_e_reexecucao():
    marcador = U.RESULT_DIR / "_idempotencia.json"
    assert marcador.exists(), "run_tests.sh deve rodar o pipeline duas vezes"
    dados = json.loads(marcador.read_text(encoding="utf-8"))
    assert dados["igual"] is True, f"reexecucao mudou contagens: {dados}"


# ------------------------------------------------- rastreabilidade / origem
def test_rastreabilidade_e_origem_nao_alterada(dest, bal, cur):
    prov = U.carregar_proveniencia()
    assert prov, "PROVENIENCIA.json ausente"
    for fonte, conn, tabela, nome in (
        ("balanco", bal, "oficial.balanco_horario",
         "balanco_oficial_2025-01-01_2025-01-08.csv"),
        ("curva", cur, "oficial.curva_horaria",
         "curva_oficial_2025-01-01_2025-01-08.csv"),
    ):
        n = escalar(conn, f"SELECT count(*) FROM {tabela}")
        assert n == prov["fontes"][fonte]["recorte_linhas"]
        # o arquivo de snapshot nao foi alterado
        assert U.sha256_arquivo(U.OFICIAL_DIR / nome) == \
            prov["fontes"][fonte]["recorte_sha256"], "snapshot oficial alterado!"
    sem_meta = escalar(dest, "SELECT count(*) FROM aula1.stg_balanco "
                             "WHERE _sha256_recorte IS NULL OR _extraido_em IS NULL")
    assert sem_meta == 0


# ------------------------------------------------- conexoes/volumes separados
def test_servicos_e_bases_separados(bal, cur, dest):
    def regclass(conn, nome):
        return escalar(conn, f"SELECT to_regclass('{nome}')::text")

    # cada fonte so tem o seu dataset
    assert regclass(bal, "oficial.balanco_horario") is not None
    assert regclass(bal, "oficial.curva_horaria") is None
    assert regclass(cur, "oficial.curva_horaria") is not None
    assert regclass(cur, "oficial.balanco_horario") is None
    # destino separado das fontes
    assert regclass(dest, "oficial.balanco_horario") is None
    assert regclass(dest, "aula1.integrado") is not None
    # hosts distintos
    assert U.descricao_conexao("FONTE_BALANCO")["host"] != \
        U.descricao_conexao("FONTE_CURVA")["host"]


# ----------------------------------------------------------- manifesto x dados
def test_manifesto_consistente_com_copia():
    caminho = U.ROOT / "gabarito" / "MANIFESTO_LABORATORIO.json"
    assert caminho.exists()
    manifesto = json.loads(caminho.read_text(encoding="utf-8"))
    # ordem de grandeza: base + extras - removidas
    assert manifesto["total_defeitos"] == 22
    assert manifesto["por_tipo"]["hora_faltante"] == 2
    assert manifesto["por_tipo"]["duplicata_exata"] == 2
    assert manifesto["por_tipo"]["conflito_chave"] == 2
    assert manifesto["por_tipo"]["extremo_suspeito"] == 2
    lab_bal = U.LAB_DIR / "balanco_laboratorio_2025-01-01_2025-01-08.csv"
    _, linhas = U.ler_csv(lab_bal)
    assert len(linhas) == 841
