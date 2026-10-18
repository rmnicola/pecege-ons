#!/usr/bin/env python3
"""Extrai os ativos oficiais; não recria ou recolore marcas."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "Template ONS.pptx"
ASSETS = ROOT / "design-system/assets/img"
MAP = {
    "image1.svg": "simbolo-pecege.svg",
    "image5.svg": "simbolo-pecege-branco.svg",
    "image6.png": "logo-ons-branco.png",
    "image4.png": "capa-ons.png",
    "image2.png": "fundo-ondas.png",
    "image7.svg": "edificio-pecege.svg",
}

def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    with ZipFile(TEMPLATE) as source:
        for original, name in MAP.items():
            (ASSETS / name).write_bytes(source.read(f"ppt/media/{original}"))
    provenance = {
        "template": "Template ONS.pptx",
        "sha256": hashlib.sha256(TEMPLATE.read_bytes()).hexdigest(),
        "assets": {name: f"ppt/media/{original}" for original, name in MAP.items()},
        "canvas_emu": [12192000, 6858000],
        "notes": "fundo-ondas.png é invertido verticalmente no layout 3; logo ONS tem recorte no template",
    }
    (ASSETS.parent / "proveniencia.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(MAP)} ativos extraídos de {TEMPLATE.name}")

if __name__ == "__main__":
    main()
