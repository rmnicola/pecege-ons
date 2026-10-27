"""O pipeline: conhece só os contratos de fonte e de destino. Não precisa mexer aqui.

Qualquer objeto com o método certo serve como fonte ou como destino: é o padrão
strategy. Para mudar de onde os dados vêm ou para onde vão, você troca a estratégia
em executar.py; este arquivo não muda.
"""

from typing import Protocol

import pandas as pd

CHAVE = ["id_subsistema", "instante"]


class Fonte(Protocol):
    def extrair(self, inicio: str, fim: str) -> pd.DataFrame:
        """Devolve id_subsistema, instante e as colunas de valor, de inicio até antes de fim."""


class Destino(Protocol):
    def gravar(self, dados: pd.DataFrame) -> None:
        """Grava a tabela pronta."""


def executar(fontes: list[Fonte], destino: Destino, inicio: str, fim: str) -> pd.DataFrame:
    dados = None
    for fonte in fontes:
        tabela = fonte.extrair(inicio, fim)
        print(f"{type(fonte).__name__}: {len(tabela)} linhas")
        if dados is None:
            dados = tabela
        else:
            dados = dados.merge(tabela, on=CHAVE, how="left", validate="one_to_one")
    dados = dados.sort_values(CHAVE).reset_index(drop=True)
    print(f"Juntas: {len(dados)} linhas, {dados.isna().sum().sum()} valores vazios")
    destino.gravar(dados)
    return dados
