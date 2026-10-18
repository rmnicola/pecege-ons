"""Desafio: combinar carga e temperatura em saida/dados.csv.

Formato esperado, uma linha por subsistema e hora:

    id_subsistema,instante,carga_mwmed,temperatura_c

Rode a partir da pasta playground:

    docker compose run --rm etl python aluno/aula1/combinar.py
"""

import pandas as pd

from extrair_carga import extrair as extrair_carga
from extrair_clima import CIDADES, extrair as extrair_clima

EVENTO = {"inicio": "2025-01-01", "fim": "2025-01-08"}

# 1. Carga: transforme as linhas de extrair_carga(EVENTO) em um DataFrame
#    com as colunas id_subsistema, instante e carga_mwmed.
#    Dicas:
#    - Cada linha chega como dicionário; o pandas sabe montar uma tabela
#      a partir de uma lista deles.
#    - Os nomes das colunas vêm do banco, não do formato esperado.
#    - Veja o tipo dos valores de carga (print, .dtypes): é o que você quer
#      gravar e comparar?
carga = ...

# 2. Clima: para cada subsistema de CIDADES, chame extrair_clima e monte um
#    DataFrame com id_subsistema, instante e temperatura_c. Junte todos.
#    Dicas:
#    - Explore uma resposta antes de usar: quais chaves ela tem? Onde estão
#      os horários e as temperaturas?
#    - Compare o instante da carga com o horário da API: é o mesmo tipo?
#    - Conte as horas que cada fonte devolve para o mesmo EVENTO. Se não
#      baterem, releia o slide da extração do clima.
#    - Monte uma tabela por cidade e empilhe as quatro no fim.
clima = ...

# 3. Combine carga e clima pela chave (id_subsistema, instante).
#    Dicas:
#    - Que tipo de junção preserva todas as horas de carga?
#    - O pandas pode verificar se a chave é única dos dois lados.
dados = ...

# 4. Confira antes de gravar: quantas linhas? Alguma sem temperatura?
#    Dica: transforme essas perguntas em assert, para o script parar se a
#    resposta estiver errada.

# 5. Grave em saida/dados.csv.
#    Dica: o índice do DataFrame não faz parte do formato esperado.
