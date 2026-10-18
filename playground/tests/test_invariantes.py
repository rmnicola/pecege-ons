#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes de invariantes do laboratorio Pecege-ONS.

Rodam dentro do container etl (pytest). Pressupoem que o pipeline completo
ja foi executado por tests/run_tests.sh. Cada teste verifica um invariante
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


# -------------------------------------------------- rejeicao da integracao suja
def test_rejeicao_integracao_bruta_aula2(dest):
    n = escalar(dest, "SELECT count(*) FROM aula2.integracao_rejeitada")
    assert n == 4, f"esperado 4 chaves problematicas, veio {n}"
    exatos = escalar(dest, "SELECT count(*) FROM aula2.integracao_rejeitada "
                           "WHERE motivo='duplicata_exata'")
    conflitos = escalar(dest, "SELECT count(*) FROM aula2.integracao_rejeitada "
                              "WHERE motivo='conflito_chave'")
    assert exatos == 2
    assert conflitos == 2
    marcador = U.RESULT_DIR / "03_aula2_exitcode.txt"
    assert marcador.exists(), "run_tests.sh deve gravar o exit code de 03 aula2"
    assert marcador.read_text().strip() == "2"


# ------------------------------------------------------------ lacunas e zeros
def test_lacunas_sem_fabricar_linhas(dest):
    # a hora removida de proposito nao pode reaparecer, nem como zero
    for tabela, col in (("aula2.limpo_balanco", "val_carga"),
                        ("aula2.limpo_curva", "val_cargaenergiahomwmed")):
        fabricado = escalar(
            dest,
            f"SELECT count(*) FROM {tabela} WHERE id_subsistema='N' "
            f"AND din_instante='2025-01-03 05:00:00'",
        )
        assert fabricado == 0, f"linha ausente nao pode ser fabricada em {tabela}"
    lacunas = escalar(dest, "SELECT count(*) FROM aula2.lacunas "
                            "WHERE id_subsistema='N' "
                            "AND din_instante='2025-01-03 05:00:00'")
    assert lacunas == 2, "a lacuna deve ser registrada nas duas fontes"


# --------------------------------------------------- padronizacao de categorias
def test_padronizacao_categorias(dest):
    ids = conjunto(dest, "SELECT DISTINCT id_subsistema FROM aula2.limpo_balanco")
    assert ids <= {"N", "NE", "S", "SE", "SIN"}
    ids_cur = conjunto(dest, "SELECT DISTINCT id_subsistema FROM aula2.limpo_curva")
    assert ids_cur <= {"N", "NE", "S", "SE"}
    # nome canonico de SE igual nas duas fontes
    nome_bal = escalar(dest, "SELECT DISTINCT nom_subsistema FROM aula2.limpo_balanco "
                             "WHERE id_subsistema='SE'")
    nome_cur = escalar(dest, "SELECT DISTINCT nom_subsistema FROM aula2.limpo_curva "
                             "WHERE id_subsistema='SE'")
    assert nome_bal == "SUDESTE"
    assert nome_cur == "SUDESTE"
    # o valor bruto defeituoso continua preservado na staging (nao foi sobrescrito)
    brutos = conjunto(dest, "SELECT DISTINCT id_subsistema FROM aula2.stg_balanco")
    assert any(b != b.strip() or b != b.upper() for b in brutos), \
        "staging deve preservar o codigo cru com espaco/caixa"


# --------------------------------------------------------------- indicadores
def test_indicadores_de_impacto(dest):
    def pico(cenario, coluna):
        return float(escalar(
            dest,
            f"SELECT pico FROM aula2.avaliacao_indicadores WHERE fonte='balanco' "
            f"AND cenario='{cenario}' AND id_subsistema='SE' AND coluna='{coluna}'",
        ))

    assert pico("naive", "val_carga") == pytest.approx(2176462.2, rel=1e-6)
    assert pico("referencia", "val_carga") == pytest.approx(51471.444, rel=1e-6)
    assert pico("tratado", "val_carga") == pytest.approx(51471.444, rel=1e-6)


# --------------------------------------------------------------- decisoes
def test_decisoes_de_tratamento_gabarito(dest):
    with dest.cursor() as cur:
        cur.execute("SELECT motivo, count(*) FROM aula2.quarentena GROUP BY 1")
        d = dict(cur.fetchall())
    assert d.get("conflito_chave") == 4       # 2 linhas em cada fonte
    assert d.get("duplicata_exata") == 2      # 1 descartada em cada fonte
    assert d.get("numero_invalido") == 3      # N/A (2) + '-' (1)
    assert d.get("celula_vazia") == 2
    assert d.get("extremo_quarentena_didatica") == 2


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
