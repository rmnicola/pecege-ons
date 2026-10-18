#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""06 - Avalia o tratamento contra a referencia limpa (ORACLE de avaliacao).

A referencia limpa e o proprio recorte oficial congelado (data/clean_ref/).
Ela serve APENAS como gabarito de avaliacao: as decisoes de producao vem das
evidencias do diagnostico (04) e das politicas explicitas (05). O script
compara tres cenarios por subsistema e coluna:

  * referencia : clean_ref (oracle)
  * naive      : staging cru da copia de laboratorio, valores parseaveis,
                 duplicatas e extremos incluidos (o que aconteceria sem tratar)
  * tratado    : aula2.limpo_* (apos 05)

Indicadores: cobertura (horas com valor nao nulo em 168), media, pico, minimo.

Uso:
    docker compose run --rm etl python scripts/06_avaliar.py
"""

from __future__ import annotations

import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime

import _common as U

LOG = U.get_logger("06_avaliar")
MED_BAL = ["val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar",
           "val_carga", "val_intercambio"]
MED_CUR = ["val_cargaenergiahomwmed"]
ESPERADO_POR_SUB = 168


def pontos_do_csv(caminho, medidas, incluir_sin=True):
    _, linhas = U.ler_csv(caminho)
    cols = ["id_subsistema", "nom_subsistema", "din_instante"] + medidas
    por_sub = defaultdict(lambda: defaultdict(dict))
    for linha in linhas:
        d = dict(zip(cols, linha))
        sub = U.normalizar_id(d["id_subsistema"])
        if not incluir_sin and sub == "SIN":
            continue
        inst = U.parse_instante(d["din_instante"])
        if inst is None:
            continue
        ts = inst.strftime("%Y-%m-%d %H:%M:%S")
        for c in medidas:
            num, status = U.parse_numero(d[c])
            if status in ("ok", "decimal_virgula"):
                por_sub[sub][c][ts] = num
    return por_sub


def pontos_do_staging(conn, tabela, medidas):
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {tabela}")
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    por_sub = defaultdict(lambda: defaultdict(list))
    for r in rows:
        sub = U.normalizar_id(r["id_subsistema"])
        inst = U.parse_instante(r["din_instante"])
        if inst is None:
            continue
        ts = inst.strftime("%Y-%m-%d %H:%M:%S")
        for c in medidas:
            num, status = U.parse_numero(r[c])
            if status in ("ok", "decimal_virgula"):
                por_sub[sub][c].append(num)
    return por_sub


def pontos_do_limpo(conn, tabela, medidas):
    with conn.cursor() as cur:
        cur.execute(f"SELECT id_subsistema, din_instante, {', '.join(medidas)} FROM {tabela}")
        rows = cur.fetchall()
    por_sub = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        sub, inst = row[0], row[1]
        ts = inst.strftime("%Y-%m-%d %H:%M:%S")
        for i, c in enumerate(medidas):
            if row[2 + i] is not None:
                por_sub[sub][c][ts] = float(row[2 + i])
    return por_sub


def metricas(valores: dict) -> dict:
    vals = list(valores.values())
    if not vals:
        return {"cobertura": 0, "media": None, "pico": None, "minimo": None}
    return {
        "cobertura": len(vals),
        "media": round(statistics.fmean(vals), 4),
        "pico": round(max(vals), 4),
        "minimo": round(min(vals), 4),
    }


def avaliar_fonte(conn, destino_tabela, stg_tabela, caminho_ref, medidas, fonte):
    ref = pontos_do_csv(caminho_ref, medidas)
    naive = pontos_do_staging(conn, stg_tabela, medidas)
    trat = pontos_do_limpo(conn, destino_tabela, medidas)

    linhas = []
    for sub in sorted(set(ref) | set(naive) | set(trat)):
        for c in medidas:
            m_ref = metricas(ref.get(sub, {}).get(c, {}))
            m_naive = metricas(dict(enumerate(naive.get(sub, {}).get(c, []))))
            m_trat = metricas(trat.get(sub, {}).get(c, {}))
            if m_ref["cobertura"] == 0 and m_trat["cobertura"] == 0:
                continue
            for cenario, m in (("referencia", m_ref), ("naive", m_naive),
                               ("tratado", m_trat)):
                linhas.append((fonte, cenario, sub, c, m["cobertura"],
                               ESPERADO_POR_SUB, m["media"], m["pico"], m["minimo"]))
    return linhas, ref, naive, trat


def main() -> int:
    inicio = time.time()
    conn = U.conectar_destino()
    try:
        U.executar_ddl(conn, """
DROP TABLE IF EXISTS aula2.avaliacao_indicadores CASCADE;
CREATE TABLE aula2.avaliacao_indicadores (
    fonte text, cenario text, id_subsistema text, coluna text,
    cobertura integer, esperado integer, media numeric, pico numeric, minimo numeric
);
""")
        linhas_b, ref_b, naive_b, trat_b = avaliar_fonte(
            conn, "aula2.limpo_balanco", "aula2.stg_balanco",
            U.CLEAN_REF_DIR / "balanco_clean_ref_2025-01-01_2025-01-08.csv",
            MED_BAL, "balanco",
        )
        linhas_c, ref_c, naive_c, trat_c = avaliar_fonte(
            conn, "aula2.limpo_curva", "aula2.stg_curva",
            U.CLEAN_REF_DIR / "curva_clean_ref_2025-01-01_2025-01-08.csv",
            MED_CUR, "curva",
        )
        linhas = linhas_b + linhas_c
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO aula2.avaliacao_indicadores VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                linhas,
            )
        conn.commit()

        # impacto: diferenca das medias/picos do tratado e do naive vs referencia
        impacto = {}
        for fonte, ref, naive, trat, medidas in (
            ("balanco", ref_b, naive_b, trat_b, MED_BAL),
            ("curva", ref_c, naive_c, trat_c, MED_CUR),
        ):
            for sub in sorted(ref):
                for c in medidas:
                    base = metricas(ref.get(sub, {}).get(c, {}))
                    tr = metricas(trat.get(sub, {}).get(c, {}))
                    nv = metricas(dict(enumerate(naive.get(sub, {}).get(c, []))))
                    if base["media"] is None:
                        continue
                    chave = f"{fonte}.{sub}.{c}"
                    impacto[chave] = {
                        "cobertura_ref": base["cobertura"],
                        "cobertura_tratado": tr["cobertura"],
                        "media_ref": base["media"],
                        "media_tratado": tr["media"],
                        "delta_media_tratado": (
                            None if tr["media"] is None else round(tr["media"] - base["media"], 4)
                        ),
                        "pico_ref": base["pico"],
                        "pico_tratado": tr["pico"],
                        "delta_pico_tratado": (
                            None if tr["pico"] is None else round(tr["pico"] - base["pico"], 4)
                        ),
                        "pico_naive": nv["pico"],
                        "delta_pico_naive": (
                            None if nv["pico"] is None else round(nv["pico"] - base["pico"], 4)
                        ),
                    }
        resumo = {
            "script": "06_avaliar",
            "observacao": (
                "clean_ref = oracle de avaliacao; decisoes de producao vem do "
                "diagnostico (04) e das politicas de tratamento (05)."
            ),
            "linhas_avaliacao": len(linhas),
            "impacto": impacto,
            "duracao_s": round(time.time() - inicio, 2),
        }
        U.salvar_json("06_avaliar.json", resumo)
        LOG.info("avaliacao concluida: %d linhas; impacto em resultados/06_avaliar.json",
                 len(linhas))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
