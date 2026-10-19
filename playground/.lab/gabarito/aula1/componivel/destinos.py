"""Destinos que cumprem o contrato: gravar(dados)."""

from pathlib import Path


class CsvLocal:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def gravar(self, dados):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados.to_csv(self.caminho, index=False)
        print(f"{len(dados)} linhas gravadas em {self.caminho}")
