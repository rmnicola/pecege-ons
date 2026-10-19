"""Pipeline componível: conhece só os contratos de fonte e destino."""

from typing import Protocol

import pandas as pd

CHAVE = ["id_subsistema", "instante"]


class Fonte(Protocol):
    nome: str

    def extrair(self, inicio: str, fim: str) -> pd.DataFrame:
        """Devolve id_subsistema, instante e valor para [inicio, fim)."""


class Destino(Protocol):
    def gravar(self, dados: pd.DataFrame) -> None: ...


def executar(fontes: list[Fonte], destino: Destino, inicio: str, fim: str) -> pd.DataFrame:
    dados = None
    for fonte in fontes:
        tabela = fonte.extrair(inicio, fim)
        tabela = tabela.rename(columns={"valor": fonte.nome})
        dados = tabela if dados is None else dados.merge(
            tabela, on=CHAVE, how="left", validate="one_to_one")
    assert dados.notna().all().all(), "há valores ausentes depois da junção"
    destino.gravar(dados.sort_values(CHAVE))
    return dados
