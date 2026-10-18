#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera a copia didatica "suja" (laboratorio) a partir do snapshot oficial.

Determinismo: as alteracoes sao aplicadas em coordenadas fixas
(id_subsistema, din_instante) e nao usam aleatoriedade. Rodar duas vezes
produz o mesmo arquivo byte-a-byte.

Regras:
  * o snapshot em data/oficial/ nunca e alterado;
  * cada defeito tem tipo, alvo, valor oficial e valor de laboratorio;
  * o manifesto completo fica em gabarito/MANIFESTO_LABORATORIO.json
    (reservado ao professor); o aluno descobre os defeitos pelo diagnostico;
  * data/clean_ref/ guarda a referencia limpa do MESMO recorte, usada apenas
    como oracle de avaliacao, nunca como fonte de producao.

Uso (host):
    python scripts/tools/gerar_laboratorio.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OFICIAL = ROOT / "data" / "oficial"
LAB = ROOT / "data" / "laboratorio"
CLEAN = ROOT / "data" / "clean_ref"
PROF = ROOT / "gabarito"
SEP = ";"


def log(msg: str) -> None:
    print(f"[gerar_laboratorio] {msg}", flush=True)


def ler(path: Path):
    linhas = path.read_text(encoding="utf-8").splitlines()
    cabecalho = linhas[0].split(SEP)
    corpo = [ln.split(SEP) for ln in linhas[1:] if ln.strip() != ""]
    return cabecalho, corpo


def escrever(path: Path, cabecalho: list[str], corpo: list[list[str]]) -> str:
    import hashlib

    texto = SEP.join(cabecalho) + "\n"
    for linha in corpo:
        texto += SEP.join(linha) + "\n"
    path.write_text(texto, encoding="utf-8")
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class Base:
    """Mantem linhas por chave e a ordem original."""

    def __init__(self, nome: str, caminho: Path):
        self.nome = nome
        self.caminho = caminho
        self.cabecalho, self.corpo = ler(caminho)
        # copia profunda do estado original para a referencia limpa (oracle)
        self.originais = [list(linha) for linha in self.corpo]
        self.idx = {c: i for i, c in enumerate(self.cabecalho)}
        self.chave_idx = (self.idx["id_subsistema"], self.idx["din_instante"])
        self.mapa = {}
        self.extras: list[list[str]] = []
        for linha in self.corpo:
            self.mapa[self.chave(linha)] = linha

    def chave(self, linha: list[str]) -> tuple[str, str]:
        return (linha[self.chave_idx[0]], linha[self.chave_idx[1]])

    def pegar(self, sub: str, inst: str) -> list[str]:
        return self.mapa[(sub, inst)]

    def campo(self, sub: str, inst: str, coluna: str) -> str:
        return self.pegar(sub, inst)[self.idx[coluna]]

    def definir(self, sub: str, inst: str, coluna: str, valor: str) -> None:
        self.pegar(sub, inst)[self.idx[coluna]] = valor

    def remover(self, sub: str, inst: str) -> None:
        alvo = (sub, inst)
        self.corpo = [ln for ln in self.corpo if self.chave(ln) != alvo]
        self.mapa.pop(alvo, None)

    def duplicar(self, sub: str, inst: str, alteracoes: dict | None = None) -> list[str]:
        copia = list(self.pegar(sub, inst))
        for coluna, valor in (alteracoes or {}).items():
            copia[self.idx[coluna]] = valor
        self.extras.append(copia)
        return copia

    def saida(self) -> list[list[str]]:
        return self.corpo + self.extras


def main() -> int:
    LAB.mkdir(parents=True, exist_ok=True)
    CLEAN.mkdir(parents=True, exist_ok=True)
    PROF.mkdir(parents=True, exist_ok=True)

    bal = Base("balanco", OFICIAL / "balanco_oficial_2025-01-01_2025-01-08.csv")
    cur = Base("curva", OFICIAL / "curva_oficial_2025-01-01_2025-01-08.csv")

    defeitos: list[dict] = []

    def registro(base: Base, tipo: str, sub: str, inst: str, campo: str,
                valor_oficial, valor_lab, politica: str, acao: str) -> None:
        defeitos.append({
            "id": f"{base.nome[0].upper()}{len([d for d in defeitos]) + 1:02d}",
            "arquivo": base.nome,
            "tipo": tipo,
            "acao": acao,
            "descricao": POLITICAS[tipo],
            "alvo": {"id_subsistema": sub, "din_instante": inst},
            "campo": campo,
            "valor_oficial": valor_oficial,
            "valor_laboratorio": valor_lab,
            "politica_tratamento": politica,
        })

    # ------------------------------------------------------------------ BALANCO
    # B01 espaco + caixa no id
    v = bal.campo("S", "2025-01-02 03:00:00", "id_subsistema")
    bal.definir("S", "2025-01-02 03:00:00", "id_subsistema", " s ")
    registro(bal, "categoria_caixa_espaco", "S", "2025-01-02 03:00:00",
             "id_subsistema", v, " s ",
             "trim + upper -> 'S'; flag padronizacao; chave recuperada", "alterar")
    # B02 caixa no nome
    v = bal.campo("NE", "2025-01-02 04:00:00", "nom_subsistema")
    bal.definir("NE", "2025-01-02 04:00:00", "nom_subsistema", "nordeste")
    registro(bal, "categoria_caixa_espaco", "NE", "2025-01-02 04:00:00",
             "nom_subsistema", v, "nordeste",
             "trim + upper + canonico -> 'NORDESTE'; flag padronizacao", "alterar")
    # B03 numero invalido
    v = bal.campo("SE", "2025-01-03 06:00:00", "val_gertermica")
    bal.definir("SE", "2025-01-03 06:00:00", "val_gertermica", "N/A")
    registro(bal, "numero_invalido", "SE", "2025-01-03 06:00:00",
             "val_gertermica", v, "N/A",
             "nao converter; NULL + flag numero_invalido; quarentena do valor", "alterar")
    # B04 celula vazia
    v = bal.campo("SE", "2025-01-03 07:00:00", "val_gereolica")
    bal.definir("SE", "2025-01-03 07:00:00", "val_gereolica", "")
    registro(bal, "celula_vazia", "SE", "2025-01-03 07:00:00",
             "val_gereolica", v, "(vazio)",
             "manter NULL + flag celula_vazia; sem imputacao por padrao", "alterar")
    # B05 decimal com virgula
    v = bal.campo("N", "2025-01-04 08:00:00", "val_carga")
    bal.definir("N", "2025-01-04 08:00:00", "val_carga", v.replace(".", ","))
    registro(bal, "formato_decimal", "N", "2025-01-04 08:00:00",
             "val_carga", v, v.replace(".", ","),
             "converter virgula decimal -> numero; flag formato_convertido", "alterar")
    # B06 marcador de ausencia
    v = bal.campo("NE", "2025-01-04 09:00:00", "val_intercambio")
    bal.definir("NE", "2025-01-04 09:00:00", "val_intercambio", "-")
    registro(bal, "numero_invalido", "NE", "2025-01-04 09:00:00",
             "val_intercambio", v, "-",
             "nao converter; NULL + flag numero_invalido; quarentena do valor", "alterar")
    # B07 hora faltante
    v = bal.campo("N", "2025-01-03 05:00:00", "val_carga")
    bal.remover("N", "2025-01-03 05:00:00")
    registro(bal, "hora_faltante", "N", "2025-01-03 05:00:00",
             "(linha inteira)", f"linha com val_carga={v}", "(linha ausente)",
             "registrar lacuna; nao fabricar linha; imputacao opcional com flag", "remover")
    # B08 duplicata exata
    copia = bal.duplicar("NE", "2025-01-02 10:00:00")
    registro(bal, "duplicata_exata", "NE", "2025-01-02 10:00:00",
             "(linha inteira)", SEP.join(copia), SEP.join(copia),
             "manter 1 (escolha deterministica), flag duplicata_exata", "duplicar")
    # B09 conflito de chave
    orig = bal.campo("SE", "2025-01-04 12:00:00", "val_carga")
    divergente = str(round(float(orig) + 5000.0, 6))
    bal.duplicar("SE", "2025-01-04 12:00:00", {"val_carga": divergente})
    registro(bal, "conflito_chave", "SE", "2025-01-04 12:00:00",
             "val_carga", orig, f"{orig} + {divergente} (2 versoes)",
             "quarentena de toda a chave; nao escolher valor arbitrariamente", "duplicar_alterado")
    # B10 extremo suspeito
    orig = bal.campo("SE", "2025-01-05 18:00:00", "val_carga")
    extremo = str(round(float(orig) * 50.0, 6))
    bal.definir("SE", "2025-01-05 18:00:00", "val_carga", extremo)
    registro(bal, "extremo_suspeito", "SE", "2025-01-05 18:00:00",
             "val_carga", orig, extremo,
             "flag extremo e quarentena didatica (criterio >fator_mediana ou negativo); NAO remover automaticamente valores presentes no snapshot original", "alterar")
    # B11 formato de data ISO
    v = bal.campo("SIN", "2025-01-06 07:00:00", "din_instante")
    bal.definir("SIN", "2025-01-06 07:00:00", "din_instante", "2025-01-06T07:00:00")
    registro(bal, "formato_data", "SIN", "2025-01-06 07:00:00",
             "din_instante", v, "2025-01-06T07:00:00",
             "aceitar ISO com 'T'; flag formato_data_convertido", "alterar")
    # B12 caixa no id sem espaco
    v = bal.campo("N", "2025-01-06 08:00:00", "id_subsistema")
    bal.definir("N", "2025-01-06 08:00:00", "id_subsistema", "n")
    registro(bal, "categoria_caixa_espaco", "N", "2025-01-06 08:00:00",
             "id_subsistema", v, "n",
             "trim + upper -> 'N'; flag padronizacao; chave recuperada", "alterar")

    # -------------------------------------------------------------------- CURVA
    v = cur.campo("S", "2025-01-02 03:00:00", "id_subsistema")
    cur.definir("S", "2025-01-02 03:00:00", "id_subsistema", " s ")
    registro(cur, "categoria_caixa_espaco", "S", "2025-01-02 03:00:00",
             "id_subsistema", v, " s ",
             "trim + upper -> 'S'; flag padronizacao; chave recuperada", "alterar")
    v = cur.campo("NE", "2025-01-02 04:00:00", "nom_subsistema")
    cur.definir("NE", "2025-01-02 04:00:00", "nom_subsistema", "nordeste")
    registro(cur, "categoria_caixa_espaco", "NE", "2025-01-02 04:00:00",
             "nom_subsistema", v, "nordeste",
             "trim + upper + canonico -> 'NORDESTE'; flag padronizacao", "alterar")
    v = cur.campo("SE", "2025-01-03 06:00:00", "val_cargaenergiahomwmed")
    cur.definir("SE", "2025-01-03 06:00:00", "val_cargaenergiahomwmed", "N/A")
    registro(cur, "numero_invalido", "SE", "2025-01-03 06:00:00",
             "val_cargaenergiahomwmed", v, "N/A",
             "nao converter; NULL + flag numero_invalido; quarentena do valor", "alterar")
    v = cur.campo("SE", "2025-01-03 07:00:00", "val_cargaenergiahomwmed")
    cur.definir("SE", "2025-01-03 07:00:00", "val_cargaenergiahomwmed", "")
    registro(cur, "celula_vazia", "SE", "2025-01-03 07:00:00",
             "val_cargaenergiahomwmed", v, "(vazio)",
             "manter NULL + flag celula_vazia; sem imputacao por padrao", "alterar")
    v = cur.campo("N", "2025-01-04 08:00:00", "val_cargaenergiahomwmed")
    cur.definir("N", "2025-01-04 08:00:00", "val_cargaenergiahomwmed", v.replace(".", ","))
    registro(cur, "formato_decimal", "N", "2025-01-04 08:00:00",
             "val_cargaenergiahomwmed", v, v.replace(".", ","),
             "converter virgula decimal -> numero; flag formato_convertido", "alterar")
    v = cur.campo("N", "2025-01-03 05:00:00", "val_cargaenergiahomwmed")
    cur.remover("N", "2025-01-03 05:00:00")
    registro(cur, "hora_faltante", "N", "2025-01-03 05:00:00",
             "(linha inteira)", f"linha com val={v}", "(linha ausente)",
             "registrar lacuna; nao fabricar linha; imputacao opcional com flag", "remover")
    copia = cur.duplicar("NE", "2025-01-02 10:00:00")
    registro(cur, "duplicata_exata", "NE", "2025-01-02 10:00:00",
             "(linha inteira)", SEP.join(copia), SEP.join(copia),
             "manter 1 (escolha deterministica), flag duplicata_exata", "duplicar")
    orig = cur.campo("SE", "2025-01-04 12:00:00", "val_cargaenergiahomwmed")
    divergente = str(round(float(orig) + 5000.0, 6))
    cur.duplicar("SE", "2025-01-04 12:00:00", {"val_cargaenergiahomwmed": divergente})
    registro(cur, "conflito_chave", "SE", "2025-01-04 12:00:00",
             "val_cargaenergiahomwmed", orig, f"{orig} + {divergente} (2 versoes)",
             "quarentena de toda a chave; nao escolher valor arbitrariamente", "duplicar_alterado")
    orig = cur.campo("SE", "2025-01-05 18:00:00", "val_cargaenergiahomwmed")
    cur.definir("SE", "2025-01-05 18:00:00", "val_cargaenergiahomwmed",
                str(round(float(orig) * 50.0, 6)))
    registro(cur, "extremo_suspeito", "SE", "2025-01-05 18:00:00",
             "val_cargaenergiahomwmed", orig, str(round(float(orig) * 50.0, 6)),
             "flag extremo e quarentena didatica (criterio >fator_mediana ou negativo); NAO remover automaticamente valores presentes no snapshot original", "alterar")
    v = cur.campo("SE", "2025-01-06 07:00:00", "din_instante")
    cur.definir("SE", "2025-01-06 07:00:00", "din_instante", "2025-01-06T07:00:00")
    registro(cur, "formato_data", "SE", "2025-01-06 07:00:00",
             "din_instante", v, "2025-01-06T07:00:00",
             "aceitar ISO com 'T'; flag formato_data_convertido", "alterar")

    # --------------------------------------------------------------- gravacao
    resumo = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for base in (bal, cur):
        saida_lab = LAB / base.caminho.name.replace("oficial", "laboratorio")
        sha_lab = escrever(saida_lab, base.cabecalho, base.saida())
        # clean ref = copia identica do oficial (oracle)
        saida_clean = CLEAN / base.caminho.name.replace("oficial", "clean_ref")
        escrever(saida_clean, base.cabecalho, base.originais)
        resumo[base.nome] = {
            "laboratorio_arquivo": saida_lab.name,
            "laboratorio_linhas": len(base.saida()),
            "laboratorio_sha256": sha_lab,
            "clean_ref_arquivo": saida_clean.name,
            "oficial_linhas": len(base.originais),
        }
        log(f"{base.nome}: lab={saida_lab.name} ({len(base.saida())} linhas) "
            f"clean_ref={saida_clean.name}")

    manifesto = {
        "titulo": "Manifesto deterministico da copia de laboratorio",
        "aviso": "Reservado ao professor. Nao distribuir: os defeitos sao o exercicio.",
        "base": "snapshot oficial recorte 2025-01-01..2025-01-08 (data/oficial)",
        "resumo": resumo,
        "total_defeitos": len(defeitos),
        "por_tipo": contar_por_tipo(defeitos),
        "defeitos": defeitos,
    }
    caminho_manifesto = PROF / "MANIFESTO_LABORATORIO.json"
    caminho_manifesto.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log(f"manifesto: {caminho_manifesto} ({len(defeitos)} defeitos)")
    print(json.dumps(contar_por_tipo(defeitos), ensure_ascii=False))
    return 0


POLITICAS = {
    "categoria_caixa_espaco": "Espaco/caixa em codigo ou nome de subsistema.",
    "numero_invalido": "Texto nao numerico em campo de medida.",
    "celula_vazia": "Celula de medida ausente (vazia).",
    "formato_decimal": "Numero com virgula decimal.",
    "hora_faltante": "Linha de uma hora inteira ausente para um subsistema.",
    "duplicata_exata": "Linha repetida identica (mesma chave e valores).",
    "conflito_chave": "Mesma chave (subsistema, hora) com valores divergentes.",
    "extremo_suspeito": "Valor muito fora do padrao do subsistema.",
    "formato_data": "Data/hora em formato alternativo (ISO com T).",
}


def contar_por_tipo(defeitos: list[dict]) -> dict:
    from collections import Counter

    return dict(sorted(Counter(d["tipo"] for d in defeitos).items()))


if __name__ == "__main__":
    sys.exit(main())
