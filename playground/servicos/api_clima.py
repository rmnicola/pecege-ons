#!/usr/bin/env python3
"""API local que imita a Historical Weather da Open-Meteo, com defeitos de propósito.

Serve GET /v1/archive com os mesmos parâmetros usados na aula 1 (latitude,
longitude, start_date, end_date, hourly=temperature_2m). Os dados vêm das
respostas reais salvas em aluno/aula1/dados/ (01 a 07/01/2025); sobre elas são
aplicados defeitos fixos, documentados em gabarito/aula2/defeitos.md.

Só a biblioteca padrão. No playground roda como o serviço api-clima:
    http://api-clima:8080/v1/archive
"""

from __future__ import annotations

import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DADOS = Path(__file__).resolve().parents[1] / "aluno" / "aula1" / "dados"
CIDADES = {"N": (-1.46, -48.49), "NE": (-8.05, -34.88), "SE": (-23.55, -46.63), "S": (-30.03, -51.23)}
DISTANCIA_MAXIMA = 1.0  # graus: mais longe que isso, a API não reconhece o ponto


def _carregar() -> dict[str, dict]:
    return {sub: json.loads((DADOS / f"clima_{sub}.json").read_text(encoding="utf-8")) for sub in CIDADES}


def _com_defeitos(sub: str, resposta: dict) -> dict:
    """Aplica os defeitos de cada cidade. Determinístico: a mesma resposta sempre."""
    r = json.loads(json.dumps(resposta))
    horas, temps = r["hourly"]["time"], r["hourly"]["temperature_2m"]
    pos = {h: i for i, h in enumerate(horas)}
    if sub == "N":  # lacuna: três horas seguidas sem valor
        for h in ("2025-01-03T13:00", "2025-01-03T14:00", "2025-01-03T15:00"):
            temps[pos[h]] = None
    elif sub == "NE":  # valor-sentinela no lugar de ausente
        for h in ("2025-01-04T02:00", "2025-01-05T22:00"):
            temps[pos[h]] = -999.0
    elif sub == "SE":  # unidade diferente: toda a série em Fahrenheit
        r["hourly"]["temperature_2m"] = temps = [round(t * 9 / 5 + 32, 1) for t in temps]
        r["hourly_units"]["temperature_2m"] = "°F"
    elif sub == "S":  # hora repetida e um pico impossível
        i = pos["2025-01-02T10:00"]
        horas.insert(i + 1, horas[i])
        temps.insert(i + 1, temps[i])
        temps[horas.index("2025-01-06T15:00")] = 61.3
    return r


def _filtrar(resposta: dict, inicio: str, fim: str) -> dict:
    """Recorta [start_date, end_date], com end_date inclusivo como na Open-Meteo."""
    horas, temps = resposta["hourly"]["time"], resposta["hourly"]["temperature_2m"]
    manter = [i for i, h in enumerate(horas) if inicio <= h[:10] <= fim]
    resposta["hourly"] = {"time": [horas[i] for i in manter], "temperature_2m": [temps[i] for i in manter]}
    return resposta


class Manipulador(BaseHTTPRequestHandler):
    def _responder(self, status: int, corpo: dict) -> None:
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path == "/saude":
            self._responder(200, {"ok": True})
            return
        if url.path != "/v1/archive":
            self._responder(404, {"error": True, "reason": "Endpoint não encontrado. Use /v1/archive."})
            return
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            lat, lon = float(q["latitude"]), float(q["longitude"])
            inicio, fim = q["start_date"], q["end_date"]
        except (KeyError, ValueError):
            self._responder(400, {"error": True, "reason": "Informe latitude, longitude, start_date e end_date."})
            return
        if q.get("hourly", "temperature_2m") != "temperature_2m":
            self._responder(400, {"error": True, "reason": "Esta API local só oferece hourly=temperature_2m."})
            return
        sub, dist = min(((s, math.dist((lat, lon), c)) for s, c in CIDADES.items()), key=lambda x: x[1])
        if dist > DISTANCIA_MAXIMA:
            self._responder(400, {"error": True, "reason": "Sem dados para este ponto. Use as coordenadas das cidades da aula."})
            return
        self._responder(200, _filtrar(_com_defeitos(sub, RESPOSTAS[sub]), inicio, fim))

    def log_message(self, formato: str, *args) -> None:
        print(f"api-clima: {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


RESPOSTAS = _carregar()

if __name__ == "__main__":
    print("api-clima ouvindo na porta 8080", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Manipulador).serve_forever()
