"""Desafio, parte 1: transformar os dados brutos de cada fonte até o formato do contrato.

Cada função recebe o que a fonte extraiu e devolve, uma linha por subsistema e hora:

    id_subsistema   N, NE, SE ou S
    instante        datetime, hora cheia, de 01/01 00h a 07/01 23h
    valor           número (float), sem ausentes
    valor_imputado  True quando o valor foi preenchido ou substituído por você

Princípios: cada correção é uma regra explícita; nada some sem registro;
quem usar o CSV precisa saber o que foi alterado (valor_imputado).

Antes de corrigir, investigue: imprima amostras, conte, agrupe, procure o
que foge do esperado em cada coluna. Os problemas não estão listados aqui.
"""

import pandas as pd


def limpar_carga(bruto: pd.DataFrame) -> pd.DataFrame:
    # Dicas:
    # - Todas as colunas chegam como texto. Compare os códigos de subsistema
    #   distintos com os quatro esperados.
    # - Nem todo texto em "valor" é um número escrito do jeito que o Python
    #   espera; e nem toda célula tem texto.
    # - Datas podem chegar em mais de um formato.
    # - Conte linhas por chave: repetidas são iguais ou divergem? Se divergem,
    #   escolher uma delas é uma decisão; registre qual foi e por quê.
    # - Para cada subsistema, compare cada valor com o comportamento típico
    #   daquele subsistema (mediana, quantis). O que é fisicamente impossível?
    # - Conte as horas de cada subsistema. Uma hora que não existe não aparece
    #   como célula vazia: ela precisa ser criada antes de ser preenchida.
    # - Para preencher, pense na série temporal: o que é razoável para uma
    #   hora entre duas horas conhecidas?
    raise NotImplementedError("limpar_carga")


def limpar_clima(bruto: pd.DataFrame) -> pd.DataFrame:
    # Dicas:
    # - Olhe a coluna unidade: todas as cidades medem na mesma escala?
    # - Ausente nem sempre chega como vazio: procure valores que significam
    #   "sem dado".
    # - Uma temperatura plausível no Brasil em janeiro fica dentro de que
    #   faixa? Defina o limite e justifique.
    # - Confira se cada cidade tem uma linha por hora.
    raise NotImplementedError("limpar_clima")
