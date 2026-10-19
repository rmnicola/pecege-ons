"""Desafio: juntar carga e temperatura num só arquivo.

O resultado vai para saida/dados.csv, com uma linha por subsistema e hora:

    id_subsistema,instante,carga_mwmed,temperatura_c

Rode quantas vezes quiser:

    python aula1/combinar.py

Faça um passo de cada vez: troque o None pelo seu código, rode e veja o que aparece.
Documentação do pandas: https://pandas.pydata.org/docs/
"""

import pandas as pd

from extrair_carga import extrair as extrair_carga
from extrair_clima import CIDADES, extrair as extrair_clima

EVENTO = {"inicio": "2025-01-01", "fim": "2025-01-08"}


# Passo 1. A carga
# linhas é uma lista de dicionários, um para cada linha do banco.
# Transforme a lista numa tabela (DataFrame) e troque os nomes das colunas:
#     din_instante            vira  instante
#     val_cargaenergiahomwmed vira  carga_mwmed
# A carga chega como Decimal: converta a coluna carga_mwmed para float.
#     pd.DataFrame  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
#     rename        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rename.html
#     astype        https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.astype.html
linhas = extrair_carga(EVENTO)
carga = linhas
print("Passo 1, carga:")
print(carga[0])


# Passo 2. A temperatura
# Para cada cidade, a API devolve uma resposta. Monte uma tabela por cidade,
# com três colunas:
#     id_subsistema  o subsistema da cidade
#     instante       resposta["hourly"]["time"]
#     temperatura_c  resposta["hourly"]["temperature_2m"]
# O horário chega como texto: converta com pd.to_datetime, para ficar igual ao da carga.
# Atenção: quantas horas chegam por cidade? E por subsistema na carga?
# A Open-Meteo inclui o último dia do período (end_date). Crie um evento só para o
# clima, terminando em 2025-01-07, e use-o na chamada de extrair_clima.
#     pd.to_datetime  https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html
# tabelas = []
# for subsistema, (cidade, lat, lon) in CIDADES.items():
#     resposta = extrair_clima(EVENTO, lat, lon)
#     tabela = None
#     tabelas.append(tabela)

# Junte as quatro tabelas, uma embaixo da outra.
#     pd.concat  https://pandas.pydata.org/docs/reference/api/pandas.concat.html
clima = None
print("Passo 2, clima:")
print(clima)


# Passo 3. Juntar
# Junte carga e clima pelas colunas id_subsistema e instante.
# Use how="left" para manter todas as horas de carga.
#     merge  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html
dados = None
print("Passo 3, dados:")
print(dados)


# Passo 4. Conferir
# Quando o passo 3 estiver pronto, tire o # das duas linhas abaixo e rode.
# O certo é 672 linhas (4 subsistemas × 168 horas) e 0 horas sem temperatura.
#     isna  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.isna.html
# print(len(dados), "linhas")
# print(dados["temperatura_c"].isna().sum(), "horas sem temperatura")


# Passo 5. Gravar
# Quando a conferência estiver certa, tire o # da linha abaixo e rode.
#     to_csv  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
# dados.to_csv("saida/dados.csv", index=False)
