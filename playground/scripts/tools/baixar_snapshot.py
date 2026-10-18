#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baixa os recortes oficiais do ONS e registra a proveniencia.

Este utilitario NAO faz parte do pipeline de aula; ele e usado pelo professor
para (re)gerar os snapshots em data/oficial/. Ele:

  * baixa as fontes oficiais de 2025 em streaming, calculando o sha256 do
    arquivo anual inteiro (hash de ORIGEM) sem persistir o CSV anual;
  * grava apenas o recorte [2025-01-01 00:00:00, 2025-01-08 00:00:00) em
    data/oficial/, preservando o texto original das linhas;
  * calcula o sha256 do RECORTE gravado;
  * baixa os dicionarios JSON oficiais;
  * grava data/oficial/PROVENIENCIA.json com URL, instante de extracao,
    hash de origem, hash do recorte e contagens/cobertura.

Uso (host, precisa de internet):
    python scripts/tools/baixar_snapshot.py

Uso via container (quando quiser rede a partir do Compose):
    docker compose run --rm etl python scripts/tools/baixar_snapshot.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuracao (fonte da verdade do contrato)
# ---------------------------------------------------------------------------
BASE = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset"
FONTES = {
    "balanco": {
        "csv_url": f"{BASE}/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_2025.csv",
        "json_url": f"{BASE}/balanco_energia_subsistema_ho/DicionarioDados_Balanco_Energia_Subsistema.json",
        "json_nome": "DicionarioDados_Balanco_Energia_Subsistema.json",
        "recorte_nome": "balanco_oficial_2025-01-01_2025-01-08.csv",
        "coluna_tempo": 2,
        "coluna_subsistema": 0,
        "separador": ";",
    },
    "curva": {
        "csv_url": f"{BASE}/curva-carga-ho/CURVA_CARGA_2025.csv",
        "json_url": f"{BASE}/curva-carga-ho/DicionarioDados_CurvaCarga.json",
        "json_nome": "DicionarioDados_CurvaCarga.json",
        "recorte_nome": "curva_oficial_2025-01-01_2025-01-08.csv",
        "coluna_tempo": 2,
        "coluna_subsistema": 0,
        "separador": ";",
    },
}
RECORTE_INI = "2025-01-01 00:00:00"   # inclusive
RECORTE_FIM = "2025-01-08 00:00:00"   # exclusive
RAIZ = Path(__file__).resolve().parents[2]      # .../playground
SAIDA = RAIZ / "data" / "oficial"
UA = "pecege-ons-etl-lab/1.0 (contato: laboratorio-didatico)"


def _log(msg: str) -> None:
    print(f"[baixar_snapshot] {msg}", flush=True)


def _abrir(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=300)


def baixar_recorte(cfg: dict) -> dict:
    """Stream do CSV anual -> sha256 de origem + recorte em disco."""
    url = cfg["csv_url"]
    _log(f"abrindo {url}")
    resp = _abrir(url)
    last_mod = resp.headers.get("Last-Modified")
    content_length = resp.headers.get("Content-Length")
    sep = cfg["separador"].encode()
    col_t = cfg["coluna_tempo"]
    col_s = cfg["coluna_subsistema"]

    sha_origem = hashlib.sha256()
    sha_recorte = hashlib.sha256()
    destino = SAIDA / cfg["recorte_nome"]
    n_origem = 0
    n_recorte = 0
    subs = set()
    horas = set()
    cabecalho = None
    buffer = b""
    with open(destino, "wb") as out:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            sha_origem.update(chunk)
            buffer += chunk
            *linhas, buffer = buffer.split(b"\n")
            for linha in linhas:
                n_origem += 1
                if cabecalho is None:
                    cabecalho = linha
                    out.write(cabecalho + b"\n")
                    sha_recorte.update(cabecalho + b"\n")
                    continue
                campos = linha.split(sep)
                if len(campos) <= col_t:
                    continue
                try:
                    inst = campos[col_t].decode("utf-8").strip()
                except UnicodeDecodeError:
                    continue
                if RECORTE_INI <= inst < RECORTE_FIM:
                    out.write(linha + b"\n")
                    sha_recorte.update(linha + b"\n")
                    n_recorte += 1
                    subs.add(campos[col_s].decode("utf-8").strip())
                    horas.add(inst)
        if buffer:  # ultima linha sem \n
            n_origem += 1
            campos = buffer.split(sep)
            if len(campos) > col_t:
                inst = campos[col_t].decode("utf-8", "replace").strip()
                if RECORTE_INI <= inst < RECORTE_FIM:
                    out.write(buffer + b"\n")
                    sha_recorte.update(buffer + b"\n")
                    n_recorte += 1
                    subs.add(campos[col_s].decode("utf-8", "replace").strip())
                    horas.add(inst)

    info = {
        "csv_url": url,
        "http_last_modified": last_mod,
        "http_content_length": int(content_length) if content_length else None,
        "linhas_arquivo_anual": n_origem - 1,  # desconta cabecalho
        "sha256_arquivo_origem": sha_origem.hexdigest(),
        "recorte_arquivo": cfg["recorte_nome"],
        "recorte_inicio_inclusive": RECORTE_INI,
        "recorte_fim_exclusive": RECORTE_FIM,
        "recorte_linhas": n_recorte,
        "recorte_sha256": sha_recorte.hexdigest(),
        "recorte_subsistemas": sorted(subs),
        "recorte_horas_distintas": len(horas),
        "recorte_bytes": destino.stat().st_size,
    }
    _log(
        f"{cfg['recorte_nome']}: {n_recorte} linhas, "
        f"{len(subs)} subsistemas, {len(horas)} horas, "
        f"origem={info['sha256_arquivo_origem'][:12]}..., "
        f"recorte={info['recorte_sha256'][:12]}..."
    )
    return info


def baixar_json(cfg: dict) -> dict:
    url = cfg["json_url"]
    _log(f"baixando {url}")
    data = _abrir(url).read()
    destino = SAIDA / cfg["json_nome"]
    destino.write_bytes(data)
    return {
        "json_url": url,
        "json_arquivo": cfg["json_nome"],
        "json_bytes": len(data),
        "json_sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    SAIDA.mkdir(parents=True, exist_ok=True)
    _log(f"snapshot em {SAIDA}")
    proveniencia = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gerador": "scripts/tools/baixar_snapshot.py",
        "observacao": (
            "sha256_arquivo_origem cobre o CSV anual completo, obtido em "
            "streaming e descartado; recorte_sha256 cobre somente o arquivo "
            "de recorte gravado. Valores preservados byte-a-byte do original."
        ),
        "fontes": {},
    }
    for nome, cfg in FONTES.items():
        try:
            recorte = baixar_recorte(cfg)
            dicionario = baixar_json(cfg)
        except Exception as exc:  # noqa: BLE001
            _log(f"FALHA em {nome}: {exc!r}")
            return 1
        proveniencia["fontes"][nome] = {**recorte, **dicionario}

    destino = SAIDA / "PROVENIENCIA.json"
    destino.write_text(
        json.dumps(proveniencia, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _log(f"proveniencia gravada em {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
