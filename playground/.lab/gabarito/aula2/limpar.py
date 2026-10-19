"""Solução do desafio da aula 2 (falhas em defeitos.md, nesta pasta).

    python .lab/gabarito/aula2/limpar.py

Desafio: arrumar a carga e carregar o resultado.

A carga chega da cópia de laboratório com cinco tipos de falha, um em cada passo.
A temperatura vem da Open-Meteo, como na aula 1, e chega certa.

Parte 1, passos 1 a 6: arrumar os dados e gravar saida/dados_limpos.csv:

    id_subsistema,instante,carga_mwmed,carga_imputada,temperatura_c

Parte 2, passo 7: carregar o resultado no armazenamento S3.

Rode quantas vezes quiser:

    python aula2/limpar.py

Em cada passo, rode e veja o que o print mostra. Depois troque o lado direito
da linha marcada com "troque" pela versão corrigida e rode de novo.
Documentação do pandas: https://pandas.pydata.org/docs/
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "aula2"))
from fontes import completar_horas, enviar_para_s3, ler_carga, ler_clima  # noqa: E402

carga = ler_carga()
print("Carga:", len(carga), "linhas")
print(carga.head())


# Passo 1. Texto despadronizado
# Os códigos deveriam ser só N, NE, S e SE, mas alguns foram digitados de outro jeito.
# Tire os espaços e passe para maiúsculas.
#     str.strip  https://pandas.pydata.org/docs/reference/api/pandas.Series.str.strip.html
#     str.upper  https://pandas.pydata.org/docs/reference/api/pandas.Series.str.upper.html
carga["id_subsistema"] = carga["id_subsistema"].str.strip().str.upper()
print("Passo 1, códigos:", carga["id_subsistema"].unique())


# Passo 2. Formato errado
# A carga chega como texto, e alguns números usam vírgula no lugar do ponto.
# Troque a vírgula por ponto e converta para número com errors="coerce":
# o que não for número fica vazio.
#     str.replace    https://pandas.pydata.org/docs/reference/api/pandas.Series.str.replace.html
#     pd.to_numeric  https://pandas.pydata.org/docs/reference/api/pandas.to_numeric.html
carga["carga_mwmed"] = pd.to_numeric(carga["carga_mwmed"].str.replace(",", "."), errors="coerce")
print("Passo 2, tipo da carga:", carga["carga_mwmed"].dtype)  # o certo é float64


# Passo 3. Duplicidade
# Algumas linhas vieram repetidas, idênticas. Deixe uma de cada.
#     drop_duplicates  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop_duplicates.html
carga = carga.drop_duplicates()
print("Passo 3, linhas repetidas:", carga.duplicated().sum())  # o certo é 0


# Passo 4. Outlier
# Uma carga muito longe das outras pode ser erro de registro. Calcule o z-score:
# quantos desvios-padrão cada carga está longe da média, (carga − média) ÷ desvio-padrão.
# Depois, esvazie as cargas com |z| maior que 3: where mantém o valor quando a
# condição é verdadeira e esvazia o resto.
#     mean   https://pandas.pydata.org/docs/reference/api/pandas.Series.mean.html
#     std    https://pandas.pydata.org/docs/reference/api/pandas.Series.std.html
#     abs    https://pandas.pydata.org/docs/reference/api/pandas.Series.abs.html
#     where  https://pandas.pydata.org/docs/reference/api/pandas.Series.where.html
z = (carga["carga_mwmed"] - carga["carga_mwmed"].mean()) / carga["carga_mwmed"].std()
carga["carga_mwmed"] = carga["carga_mwmed"].where(z.abs() <= 3)
print("Passo 4, maior carga por subsistema:")
print(carga.groupby("id_subsistema")["carga_mwmed"].max())


# Passo 5. Dados faltantes
# Cada subsistema deveria ter 168 horas (7 dias × 24), mas algumas não vieram; e há
# cargas vazias (as que já vieram vazias e as esvaziadas no passo 4).
# Primeiro, crie as horas que faltam: completar_horas(carga) devolve a tabela com
# todas as horas, com a carga vazia nas que não vieram.
carga = completar_horas(carga)
print("Passo 5, horas por subsistema:")
print(carga["id_subsistema"].value_counts())  # o certo é 168 em cada
# Depois, marque quais cargas estão vazias e preencha com interpolação
# (um valor entre a hora anterior e a seguinte).
#     isna         https://pandas.pydata.org/docs/reference/api/pandas.Series.isna.html
#     interpolate  https://pandas.pydata.org/docs/reference/api/pandas.Series.interpolate.html
carga["carga_imputada"] = carga["carga_mwmed"].isna()
carga["carga_mwmed"] = carga["carga_mwmed"].interpolate()
print("Passo 5, cargas vazias:", carga["carga_mwmed"].isna().sum())  # o certo é 0
print("Passo 5, horas preenchidas:", carga["carga_imputada"].sum())


# Passo 6. Juntar e gravar
# Quando os passos 1 a 5 estiverem prontos, tire o # das linhas abaixo.
# O certo é 672 linhas e nenhum valor vazio.
clima = ler_clima()
dados = carga.merge(clima, on=["id_subsistema", "instante"], how="left")
print(len(dados), "linhas")
print(dados.isna().sum())
dados.to_csv("saida/dados_limpos.csv", index=False)


# Passo 7 (parte 2). Carregar no armazenamento S3
# Tire o # das linhas abaixo: elas gravam os dados em Parquet e enviam o arquivo.
# Confira no console: http://localhost:9001/rustfs/console/ (usuário ons_lab, senha ons_lab_s3)
#     to_parquet  https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html
dados.to_parquet("saida/dados_limpos.parquet", index=False)
enviar_para_s3("saida/dados_limpos.parquet", "carga_clima/dados.parquet")
