#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""00 - Cria os schemas e carrega o snapshot (oficial e laboratorio).

Idempotente: pode ser executado quantas vezes for preciso. Ele recria as
tabelas de origem e os schemas de destino do zero (reset deterministico),
portanto rode-o antes de uma sequencia nova de extracoes.

  * fonte-balanco: oficial.balanco_horario (tipado) e
                   laboratorio.balanco_horario (texto cru).
  * fonte-curva:   oficial.curva_horaria (tipado) e
                   laboratorio.curva_horaria (texto cru).
  * destino:       schemas aula1 e aula2 (recriados vazios).

Uso:
    docker compose run --rm etl python scripts/00_carregar_fontes.py
"""

from __future__ import annotations

import sys
import time

import _common as U

LOG = U.get_logger("00_carregar_fontes")

# ---------------------------------------------------------------------------
# definicoes
# ---------------------------------------------------------------------------
BALANCO_COLUNAS = [
    "id_subsistema", "nom_subsistema", "din_instante",
    "val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar",
    "val_carga", "val_intercambio",
]
BALANCO_MEDIDAS = [
    "val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar",
    "val_carga", "val_intercambio",
]
CURVA_COLUNAS = [
    "id_subsistema", "nom_subsistema", "din_instante", "val_cargaenergiahomwmed",
]
CURVA_MEDIDAS = ["val_cargaenergiahomwmed"]

DDL_OFICIAL_BALANCO = """
DROP TABLE IF EXISTS oficial.balanco_horario CASCADE;
CREATE TABLE oficial.balanco_horario (
    id_subsistema text NOT NULL,
    nom_subsistema text,
    din_instante timestamp NOT NULL,
    val_gerhidraulica numeric,
    val_gertermica numeric,
    val_gereolica numeric,
    val_gersolar numeric,
    val_carga numeric,
    val_intercambio numeric,
    PRIMARY KEY (id_subsistema, din_instante)
);
"""

DDL_OFICIAL_CURVA = """
DROP TABLE IF EXISTS oficial.curva_horaria CASCADE;
CREATE TABLE oficial.curva_horaria (
    id_subsistema text NOT NULL,
    nom_subsistema text,
    din_instante timestamp NOT NULL,
    val_cargaenergiahomwmed numeric,
    PRIMARY KEY (id_subsistema, din_instante)
);
"""


def ddl_lab_balanco() -> str:
    cols = "\n".join(f"    {c} text," for c in BALANCO_COLUNAS)
    return f"""
DROP TABLE IF EXISTS laboratorio.balanco_horario CASCADE;
CREATE TABLE laboratorio.balanco_horario (
    linha_lab bigint GENERATED ALWAYS AS IDENTITY,
{cols}
    PRIMARY KEY (linha_lab)
);
"""


def ddl_lab_curva() -> str:
    cols = "\n".join(f"    {c} text," for c in CURVA_COLUNAS)
    return f"""
DROP TABLE IF EXISTS laboratorio.curva_horaria CASCADE;
CREATE TABLE laboratorio.curva_horaria (
    linha_lab bigint GENERATED ALWAYS AS IDENTITY,
{cols}
    PRIMARY KEY (linha_lab)
);
"""

DDL_META = """
CREATE SCHEMA IF NOT EXISTS meta;
DROP TABLE IF EXISTS meta.proveniencia CASCADE;
CREATE TABLE meta.proveniencia (
    fonte text PRIMARY KEY,
    url text,
    sha256_arquivo_origem text,
    sha256_recorte text,
    recorte_inicio text,
    recorte_fim text,
    linhas integer,
    subsistemas text[],
    gerado_em_utc text,
    carregado_em timestamptz DEFAULT now()
);
"""


# ---------------------------------------------------------------------------
# rotinas
# ---------------------------------------------------------------------------
def carregar_oficial(conn, schema_tabela: str, caminho, colunas, medidas):
    cabecalho, linhas = U.ler_csv(caminho)
    if cabecalho != colunas:
        raise SystemExit(f"cabecalho inesperado em {caminho}: {cabecalho}")
    registros = []
    nao_numericos = []
    datas_invalidas = []
    for linha in linhas:
        d = dict(zip(cabecalho, linha))
        inst = U.parse_instante(d["din_instante"])
        if inst is None:
            datas_invalidas.append(d["din_instante"])
        valores = []
        for c in colunas:
            if c == "din_instante":
                valores.append(inst.strftime("%Y-%m-%d %H:%M:%S") if inst else d[c])
            elif c in medidas:
                num, status = U.parse_numero(d[c])
                if status != "ok":
                    nao_numericos.append((d["id_subsistema"], d["din_instante"], c, d[c], status))
                valores.append(None if num is None else f"{num:.10f}".rstrip("0").rstrip("."))
            else:
                valores.append(d[c])
        registros.append(tuple(valores))
    if datas_invalidas:
        raise SystemExit(f"datas invalidas no arquivo oficial {caminho.name}: {datas_invalidas[:5]}")
    if nao_numericos:
        raise SystemExit(
            f"valores nao numericos no arquivo oficial {caminho.name}: {nao_numericos[:5]}"
        )
    n = U.copiar_linhas(conn, schema_tabela, colunas, registros)
    return cabecalho, registros, n


def carregar_lab(conn, schema_tabela: str, caminho, colunas):
    cabecalho, linhas = U.ler_csv(caminho)
    if cabecalho != colunas:
        raise SystemExit(f"cabecalho inesperado em {caminho}: {cabecalho}")
    registros = [tuple(linha) for linha in linhas]
    n = U.copiar_linhas(conn, schema_tabela, colunas, registros)
    return n


def resumo_tabela(conn, tabela: str, coluna_id: str, coluna_tempo: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT count(*), count(DISTINCT {coluna_id}), "
            f"min({coluna_tempo}), max({coluna_tempo}) FROM {tabela}"
        )
        n, subs, tmin, tmax = cur.fetchone()
    return {
        "tabela": tabela,
        "linhas": n,
        "subsistemas": subs,
        "instante_min": str(tmin),
        "instante_max": str(tmax),
    }


def gravar_proveniencia(conn, info: dict, fonte: str) -> None:
    rec = info["fontes"][fonte]
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO meta.proveniencia
              (fonte, url, sha256_arquivo_origem, sha256_recorte,
               recorte_inicio, recorte_fim, linhas, subsistemas, gerado_em_utc)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                fonte,
                rec["csv_url"],
                rec["sha256_arquivo_origem"],
                rec["recorte_sha256"],
                rec["recorte_inicio_inclusive"],
                rec["recorte_fim_exclusive"],
                rec["recorte_linhas"],
                rec["recorte_subsistemas"],
                info["gerado_em_utc"],
            ),
        )
    conn.commit()


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Cria schemas e carrega o snapshot (oficial e laboratorio)."
    )
    parser.add_argument(
        "--sem-reset", action="store_true",
        help="NAO apaga os schemas aula1/aula2; preserva resultados ja gerados.",
    )
    args = parser.parse_args(argv)

    inicio = time.time()
    prov = U.carregar_proveniencia()
    if not prov:
        raise SystemExit(
            "data/oficial/PROVENIENCIA.json ausente. Rode "
            "scripts/tools/baixar_snapshot.py (com internet) ou restaure o snapshot."
        )

    relatorio = {"gerado_em_utc": U.agora_utc().isoformat(timespec="seconds"),
                 "sem_reset": args.sem_reset, "fontes": {}}

    # ----------------------------------------------------------- fonte-balanco
    LOG.info("preparando fonte-balanco")
    conn = U.conectar_balanco()
    try:
        U.garantir_schema(conn, "oficial")
        U.garantir_schema(conn, "laboratorio")
        U.executar_ddl(conn, DDL_META)
        gravar_proveniencia(conn, prov, "balanco")
        U.executar_ddl(conn, DDL_OFICIAL_BALANCO)
        _, registros, n = carregar_oficial(
            conn, "oficial.balanco_horario",
            U.OFICIAL_DIR / "balanco_oficial_2025-01-01_2025-01-08.csv",
            BALANCO_COLUNAS, BALANCO_MEDIDAS,
        )
        esperado = prov["fontes"]["balanco"]["recorte_linhas"]
        if n != esperado:
            raise SystemExit(f"balanco oficial: carreguei {n}, esperava {esperado}")
        U.executar_ddl(conn, ddl_lab_balanco())
        n_lab = carregar_lab(
            conn, "laboratorio.balanco_horario",
            U.LAB_DIR / "balanco_laboratorio_2025-01-01_2025-01-08.csv",
            BALANCO_COLUNAS,
        )
        relatorio["fontes"]["balanco"] = {
            "oficial": resumo_tabela(conn, "oficial.balanco_horario", "id_subsistema", "din_instante"),
            "oficial_linhas_carregadas": n,
            "laboratorio": resumo_tabela(
                conn, "laboratorio.balanco_horario", "id_subsistema", "din_instante"
            ),
            "laboratorio_linhas_carregadas": n_lab,
            "sha256_recorte": prov["fontes"]["balanco"]["recorte_sha256"],
            "sha256_arquivo_origem": prov["fontes"]["balanco"]["sha256_arquivo_origem"],
        }
        LOG.info("fonte-balanco: oficial=%d laboratorio=%d", n, n_lab)
    finally:
        conn.close()

    # ------------------------------------------------------------- fonte-curva
    LOG.info("preparando fonte-curva")
    conn = U.conectar_curva()
    try:
        U.garantir_schema(conn, "oficial")
        U.garantir_schema(conn, "laboratorio")
        U.executar_ddl(conn, DDL_META)
        gravar_proveniencia(conn, prov, "curva")
        U.executar_ddl(conn, DDL_OFICIAL_CURVA)
        _, registros, n = carregar_oficial(
            conn, "oficial.curva_horaria",
            U.OFICIAL_DIR / "curva_oficial_2025-01-01_2025-01-08.csv",
            CURVA_COLUNAS, CURVA_MEDIDAS,
        )
        esperado = prov["fontes"]["curva"]["recorte_linhas"]
        if n != esperado:
            raise SystemExit(f"curva oficial: carreguei {n}, esperava {esperado}")
        U.executar_ddl(conn, ddl_lab_curva())
        n_lab = carregar_lab(
            conn, "laboratorio.curva_horaria",
            U.LAB_DIR / "curva_laboratorio_2025-01-01_2025-01-08.csv",
            CURVA_COLUNAS,
        )
        relatorio["fontes"]["curva"] = {
            "oficial": resumo_tabela(conn, "oficial.curva_horaria", "id_subsistema", "din_instante"),
            "oficial_linhas_carregadas": n,
            "laboratorio": resumo_tabela(
                conn, "laboratorio.curva_horaria", "id_subsistema", "din_instante"
            ),
            "laboratorio_linhas_carregadas": n_lab,
            "sha256_recorte": prov["fontes"]["curva"]["recorte_sha256"],
            "sha256_arquivo_origem": prov["fontes"]["curva"]["sha256_arquivo_origem"],
        }
        LOG.info("fonte-curva: oficial=%d laboratorio=%d", n, n_lab)
    finally:
        conn.close()

    # ------------------------------------------------------------------ destino
    conn = U.conectar_destino()
    try:
        if args.sem_reset:
            LOG.warning(
                "--sem-reset: schemas aula1/aula2 preservados (nao apaga resultados)."
            )
            for schema in ("aula1", "aula2"):
                U.executar_ddl(conn, f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            relatorio["destino"] = {"schemas_preservados": ["aula1", "aula2"]}
        else:
            LOG.warning(
                "reset do destino: os schemas aula1 e aula2 serao APAGADOS e "
                "recriados (resultados das duas aulas perdidos). Use --sem-reset "
                "para apenas recarregar as fontes."
            )
            for schema in ("aula1", "aula2"):
                U.executar_ddl(conn, f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
                U.executar_ddl(conn, f'CREATE SCHEMA "{schema}"')
            relatorio["destino"] = {"schemas_recriados": ["aula1", "aula2"]}
    finally:
        conn.close()

    relatorio["duracao_s"] = round(time.time() - inicio, 2)
    caminho = U.salvar_json("00_carregar_fontes.json", relatorio)
    LOG.info("concluido em %.2fs; relatorio em %s", relatorio["duracao_s"], caminho)
    return 0


if __name__ == "__main__":
    sys.exit(main())
