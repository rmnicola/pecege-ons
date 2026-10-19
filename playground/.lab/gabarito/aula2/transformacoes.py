"""Solução da parte 1: regras explícitas para cada problema das fontes da aula 2.

Defeitos tratados: defeitos.md, nesta pasta.
"""

import numpy as np
import pandas as pd

CHAVE = ["id_subsistema", "instante"]
SUBSISTEMAS = ["N", "NE", "SE", "S"]
LIMITE_MAD = 10                 # carga: desvio da mediana maior que 10 MAD é implausível
FAIXA_TEMPERATURA = (-10, 50)   # °C: fora disso, não é temperatura do ar no Brasil


def completar_e_imputar(d: pd.DataFrame) -> pd.DataFrame:
    """Cria as horas que faltam e preenche ausentes por interpolação dentro de cada subsistema."""
    inicio = d["instante"].min().floor("D")
    fim = d["instante"].max().floor("D") + pd.Timedelta(hours=23)
    horas = pd.date_range(inicio, fim, freq="h")
    grade = pd.MultiIndex.from_product([SUBSISTEMAS, horas], names=CHAVE)
    d = d.set_index(CHAVE)[["valor"]].reindex(grade).reset_index()
    d["valor_imputado"] = d["valor"].isna()
    d["valor"] = d.groupby("id_subsistema")["valor"].transform(
        lambda serie: serie.interpolate(limit_direction="both"))
    return d


def limpar_carga(bruto: pd.DataFrame) -> pd.DataFrame:
    d = bruto.copy()
    # Categoria: espaços e caixa diferentes representam o mesmo subsistema.
    d["id_subsistema"] = d["id_subsistema"].str.strip().str.upper()
    # Datas: aceita "2025-01-01 00:00:00" e "2025-01-01T00:00:00".
    d["instante"] = pd.to_datetime(d["instante"], format="ISO8601")
    # Números: vírgula decimal vira ponto; texto inválido e vazio viram ausentes.
    texto = d["valor"].fillna("").str.strip()
    texto = texto.str.replace(",", ".", regex=False)
    d["valor"] = pd.to_numeric(texto, errors="coerce")
    # Duplicata exata: mesma chave e mesmo valor, basta uma.
    d = d.drop_duplicates(CHAVE + ["valor"])
    # Conflito de chave: valores diferentes para a mesma hora. Não há como saber
    # qual está certo: os dois saem e a hora é imputada.
    conflito = d.duplicated(CHAVE, keep=False)
    d.loc[conflito, "valor"] = np.nan
    d = d.drop_duplicates(CHAVE)
    # Extremo: desvio da mediana do subsistema maior que LIMITE_MAD vezes o MAD.
    mediana = d.groupby("id_subsistema")["valor"].transform("median")
    desvio = (d["valor"] - mediana).abs()
    mad = desvio.groupby(d["id_subsistema"]).transform("median")
    d.loc[desvio > LIMITE_MAD * mad, "valor"] = np.nan
    return completar_e_imputar(d)


def limpar_clima(bruto: pd.DataFrame) -> pd.DataFrame:
    d = bruto.copy()
    d["instante"] = pd.to_datetime(d["instante"])
    d["valor"] = pd.to_numeric(d["valor"], errors="coerce")
    # Sentinela: -999 significa "sem dado".
    d.loc[d["valor"] == -999, "valor"] = np.nan
    # Unidade: converte Fahrenheit para Celsius, linha a linha.
    fahrenheit = d["unidade"] == "°F"
    d.loc[fahrenheit, "valor"] = (d.loc[fahrenheit, "valor"] - 32) * 5 / 9
    # Faixa física: fora dela, o valor é descartado e imputado.
    minimo, maximo = FAIXA_TEMPERATURA
    d.loc[~d["valor"].between(minimo, maximo), "valor"] = np.nan
    # Hora repetida: mesma cidade e hora, fica a primeira.
    d = d.drop_duplicates(CHAVE)
    return completar_e_imputar(d)
