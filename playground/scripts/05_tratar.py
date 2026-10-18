#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""05 - Trata a copia de laboratorio com politicas explicitas e flags.

Politicas (todas registradas em aula2.quarentena e/ou na coluna flags):
  1. categoria: trim + upper no codigo; nome canonico por codigo.
  2. data/hora: aceita 'YYYY-MM-DD HH:MM:SS' e ISO com 'T'; nao inventa hora.
  3. numero: '.' decimal; converte virgula decimal; celula vazia/marcador
     invalido/nao finito ('nan'/'inf') -> NULL + flag (nao imputa por padrao).
  4. duplicata exata: mantem 1 (menor linha_lab) e registra a descartada.
     A comparacao usa TODAS as colunas de negocio; a chave e agrupada por
     id/instante NORMALIZADOS, entao aliases de id e datas ISO sao cobertos.
  5. conflito de chave: quarentena da chave inteira (nao escolhe valor).
  6. extremo: decidimos operacionalmente (criterio DIDATICO, nao prova de
     impossibilidade fisica) que valor acima de `fator_mediana` x mediana do
     subsistema ou negativo em coluna nao-negativa vai para a QUARENTENA
     DIDATICA (celula -> NULL). O valor original e preservado em
     aula2.quarentena. Extremo apenas no limite do IQR e marcado para
     revisao e NAO removido. A politica grava os thresholds REAIS usados pelo
     04 (lidos de aula2.diagnostico_extremos), nao um texto fixo.
  7. lacuna de hora: registrada, nao fabricada. Com --imputar, preenche
     SOMENTE as lacunas (horas ausentes), pela mediana da MESMA hora-do-dia
     do subsistema. A imputacao NAO altera celulas existentes e o limite
     min/max e o intervalo dos VALORES observados do grupo, nao um limite de
     tamanho da lacuna; nao ha parametro de tamanho maximo de lacuna.

A integracao do cenario tratado (aula2.integrado_limpo) so ocorre depois de
nova verificacao de unicidade. Tudo roda em UMA transacao: se algo falhar, o
rollback preserva as saidas anteriores (nao destroi resultados sem rollback).

Uso:
    docker compose run --rm etl python scripts/05_tratar.py
    docker compose run --rm etl python scripts/05_tratar.py --imputar
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

import _common as U

LOG = U.get_logger("05_tratar")
MED_BAL = ["val_gerhidraulica", "val_gertermica", "val_gereolica", "val_gersolar",
           "val_carga", "val_intercambio"]
MED_CUR = ["val_cargaenergiahomwmed"]


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


def grid_esperado():
    ini = datetime.strptime(U.RECORTE_INI, "%Y-%m-%d %H:%M:%S")
    fim = datetime.strptime(U.RECORTE_FIM, "%Y-%m-%d %H:%M:%S")
    out, t = [], ini
    while t < fim:
        out.append(t)
        t += timedelta(hours=1)
    return out


def ler(conn, tabela):
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {tabela} ORDER BY linha_lab")
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def conjuntos_diagnostico(conn):
    """Le o diagnostico do 04 usando as chaves NORMALIZADAS e a criticidade.

    A classificacao (duplicata exata x conflito e quarentena didatica x
    revisar) e decidida no 04; aqui so a consumimos, evitando reclassificar
    por texto e garantindo consistencia diagnostico/tratamento.
    """
    conflitos = set()
    exatos = defaultdict(set)
    quarentena_didatica = set()
    revisar = set()
    criterio = {}
    with conn.cursor() as cur:
        cur.execute("SELECT fonte, id_normalizado, instante_normalizado "
                    "FROM aula2.diagnostico_duplicatas WHERE tipo='conflito_chave'")
        for fonte, idn, instn in cur.fetchall():
            conflitos.add((fonte, idn, instn))
        cur.execute("SELECT fonte, id_normalizado, instante_normalizado "
                    "FROM aula2.diagnostico_duplicatas WHERE tipo='duplicata_exata'")
        for fonte, idn, instn in cur.fetchall():
            exatos[fonte].add((idn, instn))
        cur.execute("SELECT fonte, coluna, id_subsistema, din_instante, criticidade, "
                    "mult_iqr, fator_mediana FROM aula2.diagnostico_extremos")
        for fonte, col, sub, inst, criticidade, mult_iqr, fator in cur.fetchall():
            if criticidade == "quarentena_didatica":
                quarentena_didatica.add((fonte, sub, inst, col))
            else:
                revisar.add((fonte, sub, inst, col))
            if mult_iqr is not None:
                criterio["mult_iqr"] = float(mult_iqr)
            if fator is not None:
                criterio["fator_mediana"] = float(fator)
    return conflitos, exatos, quarentena_didatica, revisar, criterio


class Tratador:
    def __init__(self, conn, fonte, linhas, medidas, conflitos, exatos,
                 quarentena_didatica, revisar, imputar, criterio):
        self.conn = conn
        self.fonte = fonte
        self.linhas = linhas
        self.medidas = medidas
        self.conflitos = conflitos
        self.exatos = exatos
        self.quarentena_didatica = quarentena_didatica
        self.revisar = revisar
        self.imputar = imputar
        self.criterio = criterio or {}
        self.limpo = []       # tuplas para COPY
        self.quarentena = []
        self.lacunas = []
        self.imputacoes = []

    def _politica_extremo(self) -> str:
        mult = self.criterio.get("mult_iqr")
        fator = self.criterio.get("fator_mediana")
        p = []
        if fator is not None:
            p.append(f"> {fator:g}x a mediana do subsistema")
        p.append("negativo em coluna nao-negativa")
        base = " ou ".join(p)
        extra = f" (mult_iqr={mult:g})" if mult is not None else ""
        return (f"criterio DIDATICO de suspeito grave: {base}{extra}; "
                f"celula -> NULL; valor original preservado")

    # -------------------------------------------------------------- parsing
    def _normalizar(self, r):
        norm_id = U.normalizar_id(r["id_subsistema"])
        norm_nom = U.normalizar_nome(r["nom_subsistema"])
        raw_tempo = (r["din_instante"] or "").strip()
        inst = U.parse_instante(raw_tempo)
        flags = []
        if r["id_subsistema"] != norm_id:
            flags.append("padronizacao_id")
        if r["nom_subsistema"] != norm_nom:
            flags.append("padronizacao_nome")
        if inst is None:
            flags.append("data_invalida")
        elif raw_tempo != inst.strftime("%Y-%m-%d %H:%M:%S"):
            flags.append("formato_data_convertido")
        return norm_id, norm_nom, inst, flags

    def _medida(self, r, campo, sub, inst_s, flags):
        num, status = U.parse_numero(r[campo])
        valor = None
        if status == "ok":
            valor = num
        elif status == "decimal_virgula":
            valor = num
            flags.append(f"formato_numero_convertido:{campo}")
        elif status == "vazio":
            flags.append(f"celula_vazia:{campo}")
            self.quarentena.append((self.fonte, r.get("linha_lab"), sub, inst_s, campo,
                                    r[campo], "celula_vazia",
                                    "manter NULL; sem imputacao por padrao"))
        elif status == "nao_finito":
            flags.append(f"numero_nao_finito:{campo}")
            self.quarentena.append((self.fonte, r.get("linha_lab"), sub, inst_s, campo,
                                    r[campo], "numero_nao_finito",
                                    "nan/inf nao e medicao valida; NULL + flag"))
        else:
            flags.append(f"numero_invalido:{campo}")
            self.quarentena.append((self.fonte, r.get("linha_lab"), sub, inst_s, campo,
                                    r[campo], "numero_invalido",
                                    "texto nao numerico; nao converter; NULL + flag"))
        if (self.fonte, sub, inst_s, campo) in self.quarentena_didatica:
            flags.append(f"extremo_quarentena_didatica:{campo}")
            self.quarentena.append((self.fonte, r.get("linha_lab"), sub, inst_s, campo,
                                    r[campo], "extremo_quarentena_didatica",
                                    self._politica_extremo()))
            valor = None
        elif (self.fonte, sub, inst_s, campo) in self.revisar:
            flags.append(f"extremo_revisar:{campo}")
        return valor

    # --------------------------------------------------------------- execute
    def executar(self):
        # chaves comparadas por id/instante NORMALIZADOS (mesma regra do 04):
        # conflitos e duplicatas escondidos por espaco/caixa/ISO sao cobertos.
        exato_keys = set(self.exatos)
        conflito_keys = {(idn, instn) for (fonte, idn, instn) in self.conflitos
                         if fonte == self.fonte}

        for r in self.linhas:
            if U.chave_normalizada(r, "id_subsistema", "din_instante") in conflito_keys:
                norm_id, _, inst, _ = self._normalizar(r)
                inst_s = inst.strftime("%Y-%m-%d %H:%M:%S") if inst else r["din_instante"]
                self.quarentena.append(
                    (self.fonte, r.get("linha_lab"), norm_id, inst_s, "(linha)",
                     "chave duplicada com valores divergentes", "conflito_chave",
                     "quarentena da chave inteira; nao escolher valor")
                )

        vistos = set()
        for r in self.linhas:
            chave = U.chave_normalizada(r, "id_subsistema", "din_instante")
            if chave in conflito_keys:
                continue
            if chave in exato_keys:
                if chave in vistos:
                    norm_id = U.normalizar_id(r["id_subsistema"])
                    inst = U.parse_instante(r["din_instante"])
                    inst_s = inst.strftime("%Y-%m-%d %H:%M:%S") if inst else r["din_instante"]
                    self.quarentena.append(
                        (self.fonte, r.get("linha_lab"), norm_id, inst_s, "(linha inteira)",
                         "linha identica repetida (mesma chave normalizada)", "duplicata_exata",
                         "manter 1 copia (menor linha_lab); descartar repetida")
                    )
                    continue
                vistos.add(chave)

            norm_id, norm_nom, inst, flags = self._normalizar(r)
            if inst is None:
                self.quarentena.append(
                    (self.fonte, r.get("linha_lab"), norm_id, r["din_instante"], "din_instante",
                     r["din_instante"], "data_invalida", "descartar linha na integracao")
                )
                continue
            inst_s = inst.strftime("%Y-%m-%d %H:%M:%S")
            valores = [self._medida(r, c, norm_id, inst_s, flags) for c in self.medidas]
            self.limpo.append((norm_id, norm_nom, inst_s, *valores,
                               ",".join(flags), r.get("linha_lab")))
        self._lacunas()
        if self.imputar:
            self._imputar()

    def _lacunas(self):
        presentes = {(linha[0], linha[2]) for linha in self.limpo}
        for sub in sorted({linha[0] for linha in self.limpo}):
            for t in grid_esperado():
                ts = t.strftime("%Y-%m-%d %H:%M:%S")
                if (sub, ts) not in presentes:
                    self.lacunas.append((self.fonte, sub, ts,
                                         "lacuna; nao imputar por padrao", False))

    def _imputar(self):
        """Imputacao com hipotese explicita: mediana da mesma hora-do-dia."""
        por_sub = defaultdict(list)
        for linha in self.limpo:
            por_sub[linha[0]].append(linha)
        novas_lacunas = []
        for lac in self.lacunas:
            _, sub, ts, _, imputado = lac
            if imputado:
                novas_lacunas.append(lac)
                continue
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            disponiveis = [
                ln for ln in por_sub.get(sub, [])
                if datetime.strptime(ln[2], "%Y-%m-%d %H:%M:%S").hour == dt.hour
            ]
            if not disponiveis:
                novas_lacunas.append(lac)
                continue
            novos = [sub, U.NOMES_CANONICOS.get(sub, sub), ts]
            for i, c in enumerate(self.medidas):
                vals = [ln[3 + i] for ln in disponiveis if ln[3 + i] is not None]
                if not vals:
                    novos.append(None)
                    continue
                imput = statistics.median(vals)
                # este clamp limita o VALOR ao intervalo observado do grupo;
                # NAO e um limite de tamanho de lacuna (nao ha esse parametro).
                imput = max(min(imput, max(vals)), min(vals))
                novos.append(imput)
            novos.append("imputado_hora_do_dia")
            novos.append(None)
            self.limpo.append(tuple(novos))
            self.imputacoes.append((self.fonte, sub, ts, "mediana_hora_do_dia",
                                    f"somente lacuna; grupo=hora {dt.hour:02d}; "
                                    f"limite de VALOR=[min,max] observados"))
            novas_lacunas.append((self.fonte, sub, ts, "mediana da mesma hora-do-dia", True))
        self.lacunas = novas_lacunas


def criar_tabelas(conn, commit: bool = True):
    U.executar_ddl(conn, """
DROP TABLE IF EXISTS aula2.limpo_balanco CASCADE;
CREATE TABLE aula2.limpo_balanco (
    id_subsistema text NOT NULL,
    nom_subsistema text,
    din_instante timestamp NOT NULL,
    val_gerhidraulica numeric, val_gertermica numeric, val_gereolica numeric,
    val_gersolar numeric, val_carga numeric, val_intercambio numeric,
    flags text, linha_lab_origem bigint
);
DROP TABLE IF EXISTS aula2.limpo_curva CASCADE;
CREATE TABLE aula2.limpo_curva (
    id_subsistema text NOT NULL,
    nom_subsistema text,
    din_instante timestamp NOT NULL,
    val_cargaenergiahomwmed numeric,
    flags text, linha_lab_origem bigint
);
DROP TABLE IF EXISTS aula2.quarentena CASCADE;
CREATE TABLE aula2.quarentena (
    fonte text, linha_lab bigint, id_subsistema text, din_instante text,
    campo text, valor_original text, motivo text, politica text
);
DROP TABLE IF EXISTS aula2.lacunas CASCADE;
CREATE TABLE aula2.lacunas (
    fonte text, id_subsistema text, din_instante text, hipotese text, imputado boolean
);
DROP TABLE IF EXISTS aula2.imputacoes CASCADE;
CREATE TABLE aula2.imputacoes (
    fonte text, id_subsistema text, din_instante text,
    metodo text, detalhe text
);
""", commit=commit)


def copiar(conn, tabela, colunas, linhas, commit: bool = True):
    U.copiar_linhas(conn, tabela, colunas, linhas, commit=commit)


def integrar_limpo(conn, commit: bool = True):
    """Integra o cenario tratado apos verificar unicidade."""
    for tab, col in (("aula2.limpo_balanco", "val_carga"),
                     ("aula2.limpo_curva", "val_cargaenergiahomwmed")):
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id_subsistema, din_instante, count(*) FROM {tab} "
                f"GROUP BY 1,2 HAVING count(*) > 1"
            )
            dups = cur.fetchall()
        if dups:
            raise SystemExit(f"apos tratamento ainda ha chave duplicada em {tab}: {dups[:3]}")
    U.executar_ddl(conn, """
DROP TABLE IF EXISTS aula2.integrado_limpo CASCADE;
CREATE TABLE aula2.integrado_limpo AS
SELECT COALESCE(b.id_subsistema, c.id_subsistema) AS id_subsistema,
       COALESCE(b.din_instante, c.din_instante) AS din_instante,
       b.nom_subsistema AS nom_subsistema_balanco,
       c.nom_subsistema AS nom_subsistema_curva,
       CASE WHEN COALESCE(b.id_subsistema, c.id_subsistema) = 'SIN'
            THEN 'agregado_sin' ELSE 'subsistema' END AS tipo_subsistema,
       b.val_gerhidraulica, b.val_gertermica, b.val_gereolica, b.val_gersolar,
       b.val_carga, b.val_intercambio,
       c.val_cargaenergiahomwmed,
       b.val_carga - c.val_cargaenergiahomwmed AS dif_carga,
       b.flags AS flags_balanco, c.flags AS flags_curva
FROM aula2.limpo_balanco b
FULL OUTER JOIN aula2.limpo_curva c
  ON b.id_subsistema = c.id_subsistema AND b.din_instante = c.din_instante;
""", commit=commit)


def main(argv=None) -> int:
    inicio = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--imputar", action="store_true",
                        help="imputa lacunas por mediana da mesma hora-do-dia (com flag)")
    args = parser.parse_args(argv)
    parametros = carregar_parametros()
    imputar = args.imputar or bool(parametros.get("imputar", False))

    conn = U.conectar_destino()
    try:
        # Tudo em UMA transacao: se algo falhar, o rollback preserva as saidas
        # anteriores (as tabelas limpo_*/quarentena/lacunas nao sao destruidas).
        criar_tabelas(conn, commit=False)
        bal = ler(conn, "aula2.stg_balanco")
        cur = ler(conn, "aula2.stg_curva")
        conflitos, exatos, qdidatica, revisar, criterio = conjuntos_diagnostico(conn)

        tb = Tratador(conn, "balanco", bal, MED_BAL, conflitos,
                      exatos.get("balanco", set()), qdidatica, revisar, imputar, criterio)
        tb.executar()
        tc = Tratador(conn, "curva", cur, MED_CUR, conflitos,
                      exatos.get("curva", set()), qdidatica, revisar, imputar, criterio)
        tc.executar()

        copiar(conn, "aula2.limpo_balanco",
               ["id_subsistema", "nom_subsistema", "din_instante", *MED_BAL,
                "flags", "linha_lab_origem"], tb.limpo, commit=False)
        copiar(conn, "aula2.limpo_curva",
               ["id_subsistema", "nom_subsistema", "din_instante", *MED_CUR,
                "flags", "linha_lab_origem"], tc.limpo, commit=False)
        quarentena = tb.quarentena + tc.quarentena
        copiar(conn, "aula2.quarentena",
               ["fonte", "linha_lab", "id_subsistema", "din_instante", "campo",
                "valor_original", "motivo", "politica"], quarentena, commit=False)
        lacunas = tb.lacunas + tc.lacunas
        copiar(conn, "aula2.lacunas",
               ["fonte", "id_subsistema", "din_instante", "hipotese", "imputado"],
               lacunas, commit=False)
        imputacoes = tb.imputacoes + tc.imputacoes
        copiar(conn, "aula2.imputacoes",
               ["fonte", "id_subsistema", "din_instante", "metodo", "detalhe"],
               imputacoes, commit=False)

        integrar_limpo(conn, commit=False)

        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM aula2.limpo_balanco")
            n_b = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM aula2.limpo_curva")
            n_c = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM aula2.quarentena")
            n_q = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM aula2.lacunas WHERE NOT imputado")
            n_l = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM aula2.integrado_limpo")
            n_i = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        LOG.error("05 falhou; rollback aplicado e saidas anteriores preservadas")
        raise
    finally:
        conn.close()

    resumo = {
        "script": "05_tratar", "imputar": imputar,
        "limpo_balanco": n_b, "limpo_curva": n_c,
        "quarentena": n_q, "lacunas_nao_imputadas": n_l,
        "integrados": n_i, "duracao_s": round(time.time() - inicio, 2),
    }
    U.salvar_json("05_tratar.json", resumo)
    LOG.info("tratamento: %s", resumo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
