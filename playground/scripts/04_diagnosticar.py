#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""04 - Diagnostica a copia de laboratorio SEM limpar.

Perfila, sem alterar dados:
  * ausencias (celula vazia / marcador de ausencia) por coluna;
  * duplicatas (exatas) e conflitos de chave (mesma chave, valores distintos);
  * formatos (espaco/caixa em codigo e nome, data ISO com T, decimal virgula);
  * cobertura por subsistema: horas esperadas, presentes, faltantes e extras;
  * extremos por subsistema/coluna (regra robusta por IQR), sem remover picos;
  * diagnostico geração x carga x intercambio, sem impor geracao = carga.

Grava tabelas de diagnostico em aula2.* e um resumo em resultados/.

Uso:
    docker compose run --rm etl python scripts/04_diagnosticar.py
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import _common as U

LOG = U.get_logger("04_diagnosticar")

# Valores default; podem ser sobrescritos por aluno/parametros_aula2.json.
MULT_IQR_DEFAULT = 8.0    # fora de [Q1-8*IQR, Q3+8*IQR] = extremo suspeito
FATOR_MEDIANA_DEFAULT = 10.0  # carga acima de 10x a mediana e suspeita
POSITIVAS = {"val_carga", "val_cargaenergiahomwmed", "val_gerhidraulica",
             "val_gertermica", "val_gereolica", "val_gersolar"}
CARGAS = {"val_carga", "val_cargaenergiahomwmed"}
RE_STRICT = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
META = {n for n, _ in U.META_COLUNAS}


def carregar_parametros() -> dict:
    caminho = U.ROOT / "aluno" / "parametros_aula2.json"
    if not caminho.exists():
        return {}
    try:
        parametros = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"parametros invalidos em {caminho}: {exc!r}")
    for chave in ("mult_iqr", "fator_mediana"):
        if chave in parametros:
            valor = parametros[chave]
            if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor <= 0:
                raise SystemExit(
                    f"parametro {chave} deve ser numerico positivo; recebi {valor!r} "
                    f"em {caminho}"
                )
    return parametros


def grid_esperado() -> list[str]:
    ini = datetime.strptime(U.RECORTE_INI, "%Y-%m-%d %H:%M:%S")
    fim = datetime.strptime(U.RECORTE_FIM, "%Y-%m-%d %H:%M:%S")
    out = []
    t = ini
    while t < fim:
        out.append(t.strftime("%Y-%m-%d %H:%M:%S"))
        t += timedelta(hours=1)
    return out


def quartis(valores):
    if len(valores) < 4:
        return None, None, None
    q1, q2, q3 = statistics.quantiles(valores, n=4)
    return q1, q2, q3


class Diagnostics:
    def __init__(self, conn, parametros: dict | None = None):
        self.conn = conn
        parametros = parametros or {}
        self.mult_iqr = float(parametros.get("mult_iqr", MULT_IQR_DEFAULT))
        self.fator_mediana = float(parametros.get("fator_mediana", FATOR_MEDIANA_DEFAULT))
        self.ausencias = []      # (fonte, coluna, status, n)
        self.duplicatas = []     # dicts de classificar_grupos_chave
        self.categorias = []     # (fonte, campo, valor_bruto, n, canonico)
        self.formatos = []       # (fonte, campo, tipo, valor_bruto, n)
        self.lacunas = []        # (fonte, id_norm, esperadas, presentes, faltantes, horas_faltantes)
        self.extremos = []       # (fonte, coluna, id_norm, inst, valor, q1, mediana, q3, iqr, limiar, criticidade, mult_iqr, fator_mediana, regra)
        self.geracao_carga = []  # (fonte, id_norm, n, media_soma_ger, media_carga, diferenca_media)

    def _ins(self, sql, rows):
        if not rows:
            return
        with self.conn.cursor() as cur:
            cur.executemany(sql, rows)
        self.conn.commit()

    def criar_tabelas(self):
        U.executar_ddl(self.conn, """
DROP TABLE IF EXISTS aula2.diagnostico_ausencias CASCADE;
CREATE TABLE aula2.diagnostico_ausencias (
    fonte text, coluna text, status text, n integer
);
DROP TABLE IF EXISTS aula2.diagnostico_duplicatas CASCADE;
CREATE TABLE aula2.diagnostico_duplicatas (
    fonte text, tipo text,
    id_normalizado text, instante_normalizado text,
    id_bruto_exemplo text, instante_bruto_exemplo text,
    ocorrencias integer, colunas_divergentes integer,
    colunas_divergentes_lista text, detalhe text
);
DROP TABLE IF EXISTS aula2.diagnostico_categorias CASCADE;
CREATE TABLE aula2.diagnostico_categorias (
    fonte text, campo text, valor_bruto text, n integer, valor_canonico text
);
DROP TABLE IF EXISTS aula2.diagnostico_formatos CASCADE;
CREATE TABLE aula2.diagnostico_formatos (
    fonte text, campo text, tipo text, valor_bruto text, n integer
);
DROP TABLE IF EXISTS aula2.diagnostico_lacunas CASCADE;
CREATE TABLE aula2.diagnostico_lacunas (
    fonte text, id_subsistema text, horas_esperadas integer, horas_presentes integer,
    horas_faltantes integer, horas_faltantes_lista text
);
DROP TABLE IF EXISTS aula2.diagnostico_extremos CASCADE;
CREATE TABLE aula2.diagnostico_extremos (
    fonte text, coluna text, id_subsistema text, din_instante text, valor numeric,
    q1 numeric, mediana numeric, q3 numeric, iqr numeric, limiar numeric,
    criticidade text, mult_iqr numeric, fator_mediana numeric, regra text
);
DROP TABLE IF EXISTS aula2.diagnostico_geracao_carga CASCADE;
CREATE TABLE aula2.diagnostico_geracao_carga (
    id_subsistema text, n integer, media_soma_geracao numeric, media_carga numeric,
    diferenca_media numeric, observacao text
);
""")

    # ------------------------------------------------------------------ au
    def ausencias_e_formatos(self, fonte, rows, medidas, col_id, col_nom, col_tempo):
        cont_ausencia = defaultdict(Counter)
        cat_id = Counter()
        cat_nom = Counter()
        fmt_tempo = 0
        fmt_decimal = Counter()
        for r in rows:
            for c in medidas:
                _, status = U.parse_numero(r[c])
                cont_ausencia[c][status] += 1
                if status == "decimal_virgula":
                    fmt_decimal[c] += 1
            raw_id, raw_nom = r[col_id], r[col_nom]
            cat_id[raw_id] += 1
            cat_nom[raw_nom] += 1
            raw_tempo = (r[col_tempo] or "").strip()
            if U.parse_instante(raw_tempo) is None:
                fmt_tempo += 1
            elif not RE_STRICT.match(raw_tempo):
                self.formatos.append(
                    (fonte, col_tempo, "formato_data_alternativo", raw_tempo, 1)
                )
        for c in medidas:
            for status, n in cont_ausencia[c].items():
                if n:
                    self.ausencias.append((fonte, c, status, n))
        for raw, n in cat_id.items():
            canon = U.normalizar_id(raw)
            if raw != canon:
                self.categorias.append((fonte, col_id, raw, n, canon))
        for raw, n in cat_nom.items():
            canon = U.normalizar_nome(raw)
            if raw != canon:
                self.categorias.append((fonte, col_nom, raw, n, canon))
        for c, n in fmt_decimal.items():
            self.formatos.append((fonte, c, "decimal_virgula", "(virgula decimal)", n))
        if fmt_tempo:
            self.formatos.append((fonte, col_tempo, "data_invalida", "(nao parseavel)", fmt_tempo))

    def detectar_duplicatas(self, fonte, rows, colunas_comparacao, col_id, col_tempo):
        """Agrupa por chave NORMALIZADA e compara TODAS as colunas de negocio.

        A normalizacao de id/instante serve so para agrupar chaves potenciais;
        o conteudo comparado (nome + medidas) usa os valores crus. Assim
        duplicatas/conflitos escondidos por espaco/caixa no id ou por data ISO
        sao detectados, e nao se escolhe arbitrariamente um registro que so
        depois vira a mesma chave.
        """
        for grupo in U.classificar_grupos_chave(rows, colunas_comparacao, col_id, col_tempo):
            # colunas: fonte + (tipo, id_normalizado, instante_normalizado,
            # id_bruto_exemplo, instante_bruto_exemplo, ocorrencias,
            # colunas_divergentes, colunas_divergentes_lista, detalhe)
            self.duplicatas.append((fonte,) + tuple(grupo.values()))

    def detectar_lacunas(self, fonte, rows, col_id, col_tempo):
        esperado = grid_esperado()
        # normaliza id apenas para CONTAR cobertura; os desvios de categoria
        # continuam listados em diagnostico_categorias.
        por_sub = defaultdict(set)
        for r in rows:
            norm = U.normalizar_id(r[col_id])
            inst = U.parse_instante(r[col_tempo])
            if inst is not None:
                por_sub[norm].add(inst.strftime("%Y-%m-%d %H:%M:%S"))
        for sub, presentes in por_sub.items():
            faltantes = [h for h in esperado if h not in presentes]
            self.lacunas.append(
                (fonte, sub, len(esperado), len(presentes), len(faltantes),
                 ", ".join(faltantes) if faltantes else "")
            )
        return por_sub

    def detectar_extremos(self, fonte, rows, medidas, col_id, col_tempo):
        por_sub = defaultdict(list)  # (sub, coluna) -> [(valor, instante)]
        for r in rows:
            sub = U.normalizar_id(r[col_id])
            inst = U.parse_instante(r[col_tempo])
            inst_s = inst.strftime("%Y-%m-%d %H:%M:%S") if inst else r[col_tempo]
            for c in medidas:
                num, status = U.parse_numero(r[c])
                if status in ("ok", "decimal_virgula"):
                    por_sub[(sub, c)].append((num, inst_s))
        for (sub, c), pontos in por_sub.items():
            valores = [v for v, _ in pontos]
            q1, med, q3 = quartis(valores)
            if q1 is None:
                continue
            iqr = q3 - q1
            lim_inf = q1 - self.mult_iqr * iqr
            lim_sup = q3 + self.mult_iqr * iqr
            for valor, inst in pontos:
                motivos = []
                fora_iqr = iqr > 0 and (valor < lim_inf or valor > lim_sup)
                negativo = c in POSITIVAS and valor < 0
                acima_mediana = c in CARGAS and med > 0 and valor > self.fator_mediana * med
                if fora_iqr:
                    motivos.append(f"fora de [Q1-{self.mult_iqr:g}*IQR, Q3+{self.mult_iqr:g}*IQR]")
                if negativo:
                    motivos.append("negativo em coluna nao-negativa")
                if acima_mediana:
                    motivos.append(f"> {self.fator_mediana:g}x a mediana do subsistema")
                if not motivos:
                    continue
                # Decisao OPERACIONAL didatica: o criterio de mediana/negativo
                # e forte, mas NAO prova impossibilidade fisica. Chamamos de
                # 'quarentena didatica'; o IQR isolado apenas 'revisar'.
                criticidade = "quarentena_didatica" if (negativo or acima_mediana) else "revisar"
                self.extremos.append(
                    (fonte, c, sub, inst, valor, q1, med, q3, iqr, lim_sup,
                     criticidade, self.mult_iqr, self.fator_mediana, "; ".join(motivos))
                )

    def geracao_vs_carga(self, fonte, rows, col_id):
        acc = defaultdict(lambda: {"n": 0, "ger": 0.0, "carga": 0.0})
        for r in rows:
            sub = U.normalizar_id(r[col_id])
            campos = {
                "val_gerhidraulica", "val_gertermica", "val_gereolica",
                "val_gersolar", "val_carga",
            }
            if not campos.issubset(r.keys()):
                continue
            nums = {}
            ok = True
            for c in campos:
                num, status = U.parse_numero(r[c])
                if status not in ("ok", "decimal_virgula"):
                    ok = False
                    break
                nums[c] = num
            if not ok:
                continue
            soma_ger = sum(nums[c] for c in
                           ("val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar"))
            acc[sub]["n"] += 1
            acc[sub]["ger"] += soma_ger
            acc[sub]["carga"] += nums["val_carga"]
        for sub, a in sorted(acc.items()):
            if a["n"] == 0:
                continue
            mg, mc = a["ger"] / a["n"], a["carga"] / a["n"]
            self.geracao_carga.append(
                (sub, a["n"], round(mg, 3), round(mc, 3), round(mg - mc, 3),
                 "geracao NAO e imposta igual a carga (ha intercambio)")
            )

    def persistir(self):
        self._ins("INSERT INTO aula2.diagnostico_ausencias VALUES (%s,%s,%s,%s)", self.ausencias)
        self._ins("INSERT INTO aula2.diagnostico_duplicatas VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  self.duplicatas)
        self._ins("INSERT INTO aula2.diagnostico_categorias VALUES (%s,%s,%s,%s,%s)",
                  self.categorias)
        self._ins("INSERT INTO aula2.diagnostico_formatos VALUES (%s,%s,%s,%s,%s)",
                  self.formatos)
        self._ins("INSERT INTO aula2.diagnostico_lacunas VALUES (%s,%s,%s,%s,%s,%s)",
                  self.lacunas)
        self._ins("INSERT INTO aula2.diagnostico_extremos VALUES "
                  "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  self.extremos)
        self._ins("INSERT INTO aula2.diagnostico_geracao_carga VALUES (%s,%s,%s,%s,%s,%s)",
                  self.geracao_carga)

    def resumo(self):
        return {
            "ausencias": Counter(a[2] for a in self.ausencias),
            "duplicatas_exatas": sum(1 for d in self.duplicatas if d[1] == "duplicata_exata"),
            "conflitos_chave": sum(1 for d in self.duplicatas if d[1] == "conflito_chave"),
            "categorias_fora_padrao": len(self.categorias),
            "formatos": len(self.formatos),
            "lacunas_total_horas": sum(l[4] for l in self.lacunas),
            "extremos_suspeitos": len(self.extremos),
        }


def ler_tabela(conn, tabela: str) -> tuple[list[str], list[dict]]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {tabela}")
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return cols, rows


def medidas_de(cols: list[str]) -> list[str]:
    return [c for c in cols if c.startswith("val_")]


def main(argv=None) -> int:
    inicio = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--parametros", default=None,
                        help="JSON com mult_iqr/fator_mediana (default: aluno/parametros_aula2.json)")
    args = parser.parse_args(argv)
    parametros = carregar_parametros()
    if args.parametros:
        parametros = json.loads((U.ROOT / args.parametros).read_text(encoding="utf-8"))
    conn = U.conectar_destino()
    try:
        diag = Diagnostics(conn, parametros)
        diag.criar_tabelas()

        _, bal = ler_tabela(conn, "aula2.stg_balanco")
        _, cur = ler_tabela(conn, "aula2.stg_curva")
        med_bal = medidas_de(list(bal[0].keys()))
        med_cur = medidas_de(list(cur[0].keys()))

        diag.ausencias_e_formatos("balanco", bal, med_bal,
                                  "id_subsistema", "nom_subsistema", "din_instante")
        diag.ausencias_e_formatos("curva", cur, med_cur,
                                  "id_subsistema", "nom_subsistema", "din_instante")
        diag.detectar_duplicatas("balanco", bal, ["nom_subsistema"] + med_bal,
                                 "id_subsistema", "din_instante")
        diag.detectar_duplicatas("curva", cur, ["nom_subsistema"] + med_cur,
                                 "id_subsistema", "din_instante")
        diag.detectar_lacunas("balanco", bal, "id_subsistema", "din_instante")
        diag.detectar_lacunas("curva", cur, "id_subsistema", "din_instante")
        diag.detectar_extremos("balanco", bal, med_bal, "id_subsistema", "din_instante")
        diag.detectar_extremos("curva", cur, med_cur, "id_subsistema", "din_instante")
        diag.geracao_vs_carga("balanco", bal, "id_subsistema")
        diag.persistir()

        resumo = diag.resumo()
        resumo["ausencias"] = dict(resumo["ausencias"])
        resumo["duracao_s"] = round(time.time() - inicio, 2)
        resumo["mult_iqr"] = diag.mult_iqr
        resumo["fator_mediana"] = diag.fator_mediana
        U.salvar_json("04_diagnosticar.json", resumo)
        LOG.info("diagnostico: %s", resumo)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
