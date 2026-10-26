#!/usr/bin/env python3
"""Génère des workflows n8n prêts à importer à partir des modèles de `workflows/`.

Les exports publiés dans ce dépôt ne contiennent ni adresse interne ni mot de passe :
les hôtes sont remplacés par des domaines `*.example` et les identifiants OpenSlice par
des marqueurs `__OPENSLICE_USERNAME__` / `__OPENSLICE_PASSWORD__`.

Ce script lit `.env`, remplace ces valeurs et écrit le résultat dans `build/`
(répertoire ignoré par Git, car il contient des secrets).

Usage :
    cp .env.example .env        # puis renseigner les valeurs
    python3 scripts/configure.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workflows"
OUT = ROOT / "build"

# (marqueur dans les modèles, variable .env). Les marqueurs les plus longs d'abord :
# "http://openslice.example:13082" doit être traité avant "http://openslice.example".
PLACEHOLDERS = [
    ("http://openslice.example:13082", "OPENSLICE_CATALOG_URL"),
    ("http://openslice.example", "OPENSLICE_URL"),
    ("http://ontology-api.example:8000", "ONTOLOGY_API_URL"),
    ("http://ollama.example:11434", "OLLAMA_URL"),
    ("http://qdrant.example:6333", "QDRANT_URL"),
    ("__OPENSLICE_USERNAME__", "OPENSLICE_USERNAME"),
    ("__OPENSLICE_PASSWORD__", "OPENSLICE_PASSWORD"),
]


def load_env(path: Path) -> dict[str, str]:
    """Lit un fichier .env simple (CLE=valeur, commentaires #)."""
    if not path.exists():
        sys.exit(f"Fichier introuvable : {path}. Copiez .env.example en .env et renseignez-le.")
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def main() -> None:
    env = load_env(ROOT / ".env")
    # Par défaut, l'API catalogue est jointe via la même URL que le reste d'OpenSlice.
    env.setdefault("OPENSLICE_CATALOG_URL", env.get("OPENSLICE_URL", ""))

    missing = [var for _, var in PLACEHOLDERS if not env.get(var)]
    if missing:
        sys.exit("Variables manquantes dans .env : " + ", ".join(missing))

    for src in sorted(SRC.rglob("*.json")):
        text = src.read_text(encoding="utf-8")
        for marker, var in PLACEHOLDERS:
            text = text.replace(marker, env[var].rstrip("/"))
        json.loads(text)  # le résultat doit rester un JSON valide
        dest = OUT / src.relative_to(SRC)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(f"✔ {dest.relative_to(ROOT)}")

    print("\nWorkflows prêts à importer dans n8n depuis build/ (ne pas committer ce dossier).")


if __name__ == "__main__":
    main()
