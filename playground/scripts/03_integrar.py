#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""03 - Integra balanco e curva com verificacao de unicidade e cardinalidade.

Antes de integrar, o script verifica se a chave (id_subsistema, din_instante)
e unica em cada staging e se a cardinalidade do cruzamento e 1:1.

  * cenario aula1: integra oficial + oficial -> aula1.integrado.
    O agregado SIN so existe no balanco; ele e marcado como
    tipo_subsistema = 'agregado_sin' e nao participa do cruzamento 1:1.
    As medidas val_carga e val_cargaenergiahomwmed sao mantidas separadas.
  * cenario aula2: a copia de laboratorio tem duplicatas/conflitos; a
    integracao ingenua e REJEITADA (sai com codigo 2) e o motivo e gravado.

Uso:
    docker compose run --rm etl python scripts/03_integrar.py --cenario aula1
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import _common as U

LOG = U.get_logger("03_integrar")
CHAVE = ["id_subsistema", "din_instante"]


def verificar_unicidade(conn, tabela: str, colunas=CHAVE) -> list[tuple]:
    cols = ", ".join(colunas)
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {cols}, count(*) AS n FROM {tabela} "
            f"GROUP BY {cols} HAVING count(*) > 1 ORDER BY n DESC, {cols}"
        )
        return cur.fetchall()


def verificar_cardinalidade(conn, tabela: str, cenario: str) -> dict:
    """Conta quantas linhas por chave a fonte tem (nulos etc.)."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {tabela}")
        total = cur.fetchone()[0]
        cur.execute(f"SELECT count(DISTINCT (id_subsistema, din_instante)) FROM {tabela}")
        distintas = cur.fetchone()[0]
        cur.execute(
            f"SELECT count(*) FROM {tabela} "
            f"WHERE id_subsistema IS NULL OR din_instante IS NULL"
        )
        nulos = cur.fetchone()[0]
    return {"tabela": tabela, "linhas": total, "chaves_distintas": distintas,
            "chaves_nulas": nulos, "excedente": total - distintas}


def gravar_check(conn, schema: str, verificacao: str, resultado: str, detalhe) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {schema}.integridade_checks (verificacao, resultado, detalhe) "
            f"VALUES (%s, %s, %s)",
            (verificacao, resultado, json.dumps(detalhe, ensure_ascii=False, default=str)),
        )


def main(argv=None) -> int:
    inicio = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cenario", required=True, choices=["aula1", "aula2"])
    args = parser.parse_args(argv)
    cenario = args.cenario

    conn = U.conectar_destino()
    try:
        if cenario == "aula1":
            return integrar_aula1(conn, inicio)
        return rejeitar_aula2(conn, inicio)
    finally:
        conn.close()


def integrar_aula1(conn, inicio: float) -> int:
    schema = "aula1"
    U.executar_ddl(conn, f"""
DROP TABLE IF EXISTS {schema}.integridade_checks CASCADE;
CREATE TABLE {schema}.integridade_checks (
    verificacao text,
    resultado text,
    detalhe jsonb,
    verificado_em timestamptz DEFAULT now()
);
""")

    dups_bal = verificar_unicidade(conn, "aula1.stg_balanco")
    dups_cur = verificar_unicidade(conn, "aula1.stg_curva")
    card_bal = verificar_cardinalidade(conn, "aula1.stg_balanco", "aula1")
    card_cur = verificar_cardinalidade(conn, "aula1.stg_curva", "aula1")

    gravar_check(conn, schema, "unicidade_balanco",
                 "ok" if not dups_bal else "falha", dups_bal)
    gravar_check(conn, schema, "unicidade_curva",
                 "ok" if not dups_cur else "falha", dups_cur)
    gravar_check(conn, schema, "cardinalidade_balanco", "ok", card_bal)
    gravar_check(conn, schema, "cardinalidade_curva", "ok", card_cur)

    if dups_bal or dups_cur:
        conn.commit()
        raise SystemExit(
            "chave (id_subsistema, din_instante) nao e unica na staging; "
            "integracao abortada."
        )

    # conjuntos de chaves por subsistema
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT id_subsistema FROM aula1.stg_balanco ORDER BY 1")
        subs_bal = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT id_subsistema FROM aula1.stg_curva ORDER BY 1")
        subs_cur = [r[0] for r in cur.fetchall()]
    so_bal = sorted(set(subs_bal) - set(subs_cur))
    so_cur = sorted(set(subs_cur) - set(subs_bal))
    gravar_check(conn, schema, "subsistemas", "ok",
                 {"balanco": subs_bal, "curva": subs_cur,
                  "so_no_balanco": so_bal, "so_na_curva": so_cur})
    # SIN e um agregado esperado apenas no balanco
    gravar_check(conn, schema, "agregado_sin",
                 "ok" if set(so_bal) <= {"SIN"} and not so_cur else "atencao",
                 {"so_no_balanco": so_bal, "so_na_curva": so_cur})

    U.executar_ddl(conn, f"""
DROP TABLE IF EXISTS {schema}.integrado CASCADE;
CREATE TABLE {schema}.integrado (
    id_subsistema text NOT NULL,
    din_instante timestamp NOT NULL,
    nom_subsistema_balanco text,
    nom_subsistema_curva text,
    tipo_subsistema text NOT NULL,
    val_carga numeric,
    val_cargaenergiahomwmed numeric,
    dif_carga numeric,
    carga_coincide boolean,
    tem_balanco boolean NOT NULL,
    tem_curva boolean NOT NULL,
    _sha256_recorte_balanco text,
    _sha256_recorte_curva text,
    _integrado_em timestamptz DEFAULT now(),
    PRIMARY KEY (id_subsistema, din_instante)
);
""")

    with conn.cursor() as cur:
        cur.execute(f"""
INSERT INTO {schema}.integrado (
    id_subsistema, din_instante, nom_subsistema_balanco, nom_subsistema_curva,
    tipo_subsistema, val_carga, val_cargaenergiahomwmed, dif_carga,
    carga_coincide, tem_balanco, tem_curva,
    _sha256_recorte_balanco, _sha256_recorte_curva
)
SELECT
    COALESCE(b.id_subsistema, c.id_subsistema),
    COALESCE(b.din_instante, c.din_instante),
    b.nom_subsistema,
    c.nom_subsistema,
    CASE WHEN COALESCE(b.id_subsistema, c.id_subsistema) = 'SIN'
         THEN 'agregado_sin' ELSE 'subsistema' END,
    b.val_carga,
    c.val_cargaenergiahomwmed,
    b.val_carga - c.val_cargaenergiahomwmed,
    CASE WHEN b.val_carga IS NULL OR c.val_cargaenergiahomwmed IS NULL
         THEN NULL
         ELSE b.val_carga = c.val_cargaenergiahomwmed END,
    b.id_subsistema IS NOT NULL,
    c.id_subsistema IS NOT NULL,
    b._sha256_recorte,
    c._sha256_recorte
FROM {schema}.stg_balanco b
FULL OUTER JOIN {schema}.stg_curva c
  ON b.id_subsistema = c.id_subsistema AND b.din_instante = c.din_instante
""")
        n_int = cur.rowcount
    conn.commit()

    # indicadores de qualidade da integracao
    with conn.cursor() as cur:
        cur.execute(f"""
SELECT count(*),
       count(*) FILTER (WHERE tipo_subsistema = 'subsistema'),
       count(*) FILTER (WHERE tipo_subsistema = 'agregado_sin'),
       count(*) FILTER (WHERE NOT tem_curva),
       count(*) FILTER (WHERE tem_curva AND NOT carga_coincide),
       count(*) FILTER (WHERE dif_carga <> 0)
FROM {schema}.integrado
""")
        total, subs, sin, sem_curva, divergentes, dif_nao_zero = cur.fetchone()
        # residual do agregado SIN x soma dos subsistemas
        cur.execute(f"""
SELECT max(abs(sin.val_carga - s.soma))::numeric(20,6)
FROM {schema}.integrado sin
JOIN (
    SELECT din_instante, sum(val_carga) AS soma
    FROM {schema}.integrado
    WHERE tipo_subsistema = 'subsistema'
    GROUP BY din_instante
) s ON s.din_instante = sin.din_instante
WHERE sin.tipo_subsistema = 'agregado_sin'
""")
        residual_sin = cur.fetchone()[0]
    detalhe = {
        "linhas_integradas": n_int,
        "subsistemas": subs,
        "agregado_sin": sin,
        "sem_par_na_curva": sem_curva,
        "divergencias_val_carga": divergentes,
        "dif_carga_nao_zero": dif_nao_zero,
        "residual_max_sin_vs_soma": str(residual_sin),
    }
    gravar_check(conn, schema, "merge_1_a_1", "ok", detalhe)
    gravar_check(conn, schema, "val_carga_vs_val_cargaenergiahomwmed",
                 "coincidem" if divergentes == 0 else "divergem", detalhe)
    conn.commit()

    resumo = {"script": "03_integrar", "cenario": "aula1", **detalhe,
              "duracao_s": round(time.time() - inicio, 2)}
    U.salvar_json("03_integrar_aula1.json", resumo)
    LOG.info("aula1: %d linhas integradas, %d subsistemas, %d SIN, %d sem curva",
             n_int, subs, sin, sem_curva)
    LOG.info("aula1: val_carga x val_cargaenergiahomwmed -> %d divergencias; "
             "residual max SIN=%s", divergentes, residual_sin)
    return 0


def _ler_stg(conn, tabela: str) -> tuple[list[str], list[dict]]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {tabela} ORDER BY linha_lab")
        cols = [d.name for d in cur.description]
        return cols, [dict(zip(cols, r)) for r in cur.fetchall()]


def rejeitar_aula2(conn, inicio: float) -> int:
    schema = "aula2"

    def grupos(tabela: str, medidas: list[str]) -> list[dict]:
        _, rows = _ler_stg(conn, tabela)
        return U.classificar_grupos_chave(
            rows, ["nom_subsistema"] + medidas, "id_subsistema", "din_instante"
        )

    cols_bal, _ = _ler_stg(conn, "aula2.stg_balanco")
    cols_cur, _ = _ler_stg(conn, "aula2.stg_curva")
    med_bal = [c for c in cols_bal if c.startswith("val_")]
    med_cur = [c for c in cols_cur if c.startswith("val_")]

    # Deteccao por chave NORMALIZADA: pega conflitos/duplicatas escondidos por
    # espaco/caixa no id ou por data ISO, comparando TODAS as colunas de
    # negocio (nome + medidas). A integracao ingenua e rejeitada.
    g_bal = grupos("aula2.stg_balanco", med_bal)
    g_cur = grupos("aula2.stg_curva", med_cur)

    U.executar_ddl(conn, f"""
DROP TABLE IF EXISTS {schema}.integracao_rejeitada CASCADE;
CREATE TABLE {schema}.integracao_rejeitada (
    fonte text,
    id_subsistema text,
    din_instante text,
    ocorrencias integer,
    colunas_divergentes integer,
    motivo text
);
""")
    with conn.cursor() as cur:
        for fonte, grupos_fonte in (("balanco", g_bal), ("curva", g_cur)):
            for g in grupos_fonte:
                cur.execute(
                    f"INSERT INTO {schema}.integracao_rejeitada "
                    f"(fonte, id_subsistema, din_instante, ocorrencias, "
                    f"colunas_divergentes, motivo) VALUES (%s,%s,%s,%s,%s,%s)",
                    (fonte, g["id_normalizado"], g["instante_normalizado"],
                     g["ocorrencias"], g["colunas_divergentes"], g["tipo"]),
                )
    conn.commit()

    def contar(gs, tipo):
        return sum(1 for g in gs if g["tipo"] == tipo)

    detalhe = {
        "chaves_rejeitadas_balanco": len(g_bal),
        "chaves_rejeitadas_curva": len(g_cur),
        "duplicatas_exatas_balanco": contar(g_bal, "duplicata_exata"),
        "duplicatas_exatas_curva": contar(g_cur, "duplicata_exata"),
        "conflitos_balanco": contar(g_bal, "conflito_chave"),
        "conflitos_curva": contar(g_cur, "conflito_chave"),
        "exemplos_balanco": [g["id_normalizado"] + "@" + g["instante_normalizado"]
                             for g in g_bal[:5]],
        "exemplos_curva": [g["id_normalizado"] + "@" + g["instante_normalizado"]
                           for g in g_cur[:5]],
    }
    U.salvar_json("03_integrar_aula2_rejeitada.json",
                  {"script": "03_integrar", "cenario": "aula2", **detalhe,
                   "duracao_s": round(time.time() - inicio, 2)})
    LOG.error("aula2: integracao ingenua REJEITADA. %s", detalhe)
    LOG.error("Aplique 04_diagnosticar.py e 05_tratar.py antes de integrar o cenario sujo.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
