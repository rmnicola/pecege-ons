#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Funcoes puras (apenas biblioteca padrao) usadas pelo laboratorio.

Ficam aqui, separadas de _common.py, para poderem ser testadas sem
PostgreSQL/Docker e para concentrar a regra de parsing e de classificacao de
chaves. Os scripts continuam acessando via _common (que reexporta).
"""

from __future__ import annotations

import math
from datetime import datetime

# Nomes canonicos de subsistema por codigo (id_subsistema e a chave estavel).
NOMES_CANONICOS = {
    "N": "NORTE",
    "NE": "NORDESTE",
    "S": "SUL",
    "SE": "SUDESTE",
    "SIN": "SISTEMA INTERLIGADO NACIONAL",
}
SUBSISTEMAS_SISTEMA = ["N", "NE", "S", "SE"]   # 4 subsistemas fisicos
AGREGADOS = ["SIN"]                             # agregado nacional (so no balanco)

_MARCADORES_AUSENTES = {"NA", "N/A", "NULL", "-", "--"}


# ---------------------------------------------------------------------------
# Parsing explicito
# ---------------------------------------------------------------------------
def parse_instante(valor):
    """Aceita 'YYYY-MM-DD HH:MM:SS' e ISO 'YYYY-MM-DDTHH:MM:SS'.

    Retorna datetime ou None. Nao inventa hora ausente.
    """
    if valor is None:
        return None
    t = str(valor).strip()
    if not t:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    return None


def parse_numero(valor):
    """Retorna (numero, status).

    status:
      ok               -> float FINITO em formato '.'
      decimal_virgula  -> numero com virgula decimal, convertido (finito)
      nao_finito       -> 'nan'/'inf'/'-inf'/overflow (float nao finito)
      vazio            -> celula ausente/vazia
      invalido         -> texto nao numerico (nao converter)

    Valores nao finitos (ex.: 'nan', '+nan', 'inf', '-inf', '1e999') NAO sao
    aceitos como medicao valida.
    """
    if valor is None:
        return None, "vazio"
    t = str(valor).strip()
    if t == "":
        return None, "vazio"
    if t.upper() in _MARCADORES_AUSENTES:
        return None, "invalido"
    try:
        num = float(t)
    except ValueError:
        num = None
    if num is not None:
        return (num, "ok") if math.isfinite(num) else (None, "nao_finito")
    # decimal com virgula: so converte se casar com o padrao brasileiro
    if "," in t and "." not in t:
        try:
            num = float(t.replace(",", "."))
        except ValueError:
            return None, "invalido"
        return (num, "decimal_virgula") if math.isfinite(num) else (None, "nao_finito")
    return None, "invalido"


def normalizar_id(valor):
    return (valor or "").strip().upper()


def normalizar_nome(valor):
    nome = (valor or "").strip().upper()
    # o balanco usa 'SUDESTE/CENTRO-OESTE'; a curva usa 'SUDESTE'. O codigo
    # estavel e 'SE'; o nome e padronizado.
    if nome.startswith("SUDESTE"):
        return "SUDESTE"
    return nome


# ---------------------------------------------------------------------------
# Chaves e duplicatas
# ---------------------------------------------------------------------------
def chave_normalizada(linha, col_id, col_tempo):
    """Chave POTENCIAL (id normalizado, instante normalizado).

    Serve apenas para AGRUPAR; o valor bruto nunca e sobrescrito. Se o
    instante nao for parseavel, usa o texto bruto entre marcadores para nao
    juntar horarios diferentes.
    """
    idn = normalizar_id(linha.get(col_id))
    bruto_tempo = linha.get(col_tempo)
    inst = parse_instante(bruto_tempo)
    if inst is None:
        instn = f"\x00bruto\x00{'' if bruto_tempo is None else str(bruto_tempo)}"
    else:
        instn = inst.strftime("%Y-%m-%d %H:%M:%S")
    return idn, instn


def _valor_cmp(valor):
    return "" if valor is None else str(valor)


def classificar_grupos_chave(linhas, colunas_comparacao, col_id, col_tempo):
    """Agrupa por chave normalizada e classifica duplicatas.

    colunas_comparacao: colunas de negocio a comparar (ex.: nome + medidas).
    As colunas de chave (id/instante) sao normalizadas apenas para agrupar;
    a comparacao de conteudo usa os valores crus dessas colunas de negocio.

    Retorna lista de dicts (um por grupo com mais de uma linha):
      tipo: 'duplicata_exata' (mesmo conteudo) ou 'conflito_chave'
      id_normalizado, instante_normalizado
      id_bruto_exemplo, instante_bruto_exemplo
      ocorrencias, colunas_divergentes, colunas_divergentes_lista, detalhe
    """
    grupos = {}
    for linha in linhas:
        grupos.setdefault(chave_normalizada(linha, col_id, col_tempo), []).append(linha)

    resultado = []
    for (idn, instn), itens in sorted(grupos.items()):
        if len(itens) < 2:
            continue
        assinaturas = [tuple(_valor_cmp(r.get(c)) for c in colunas_comparacao) for r in itens]
        exato = len(set(assinaturas)) == 1
        divergentes = [
            c for c in colunas_comparacao
            if len({_valor_cmp(r.get(c)) for r in itens}) > 1
        ]
        detalhe = "; ".join(
            f"{c}=" + "|".join(sorted({_valor_cmp(r.get(c)) for r in itens}))
            for c in divergentes
        )
        primeiro = itens[0]
        resultado.append({
            "tipo": "duplicata_exata" if exato else "conflito_chave",
            "id_normalizado": idn,
            "instante_normalizado": instn,
            "id_bruto_exemplo": _valor_cmp(primeiro.get(col_id)),
            "instante_bruto_exemplo": _valor_cmp(primeiro.get(col_tempo)),
            "ocorrencias": len(itens),
            "colunas_divergentes": len(divergentes),
            "colunas_divergentes_lista": ",".join(divergentes),
            "detalhe": detalhe[:400],
        })
    return resultado
