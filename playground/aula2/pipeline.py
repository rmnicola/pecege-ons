"""Pipeline da aula 1, com um encaixe a mais: a transformação também é uma peça."""

from typing import Callable, Protocol

import pandas as pd

CHAVE = ["id_subsistema", "instante"]


class Fonte(Protocol):
    nome: str

    def extrair(self, inicio: str, fim: str) -> pd.DataFrame: ...


class Destino(Protocol):
    def gravar(self, dados: pd.DataFrame) -> None: ...


class Transformada:
    """Envolve uma fonte e aplica uma transformação ao que ela extrai.

    Para o pipeline, continua sendo uma fonte: mesmo nome, mesmo extrair().
    """

    def __init__(self, fonte: Fonte, transformar: Callable[[pd.DataFrame], pd.DataFrame]):
        self.fonte = fonte
        self.nome = fonte.nome
        self.transformar = transformar

    def extrair(self, inicio, fim):
        return self.transformar(self.fonte.extrair(inicio, fim))


def executar(fontes: list[Fonte], destino: Destino, inicio: str, fim: str) -> pd.DataFrame:
    dados = None
    for fonte in fontes:
        tabela = fonte.extrair(inicio, fim)
        # valor vira o nome da fonte; colunas como valor_imputado acompanham o nome.
        tabela = tabela.rename(columns={c: c.replace("valor", fonte.nome, 1)
                                        for c in tabela.columns if c.startswith("valor")})
        dados = tabela if dados is None else dados.merge(
            tabela, on=CHAVE, how="left", validate="one_to_one")
    assert dados.notna().all().all(), "há valores ausentes depois da junção"
    destino.gravar(dados.sort_values(CHAVE))
    return dados
