"""Test de la sonde ping_serveur (readiness phase 2).

Demande les dépendances installées (mcp) : depuis le dossier backend/,
`pip install -r requirements.txt` puis `pytest tests` (ou ce fichier seul
avec `python tests/test_ping_serveur.py`).
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.outils_diagnostic_commun import VERSION_SERVEUR  # noqa: E402
from core.outils_sonde import reponse_ping  # noqa: E402
from core.serveur_mcp_diagnostic import mcp_diagnostic  # noqa: E402


def test_ping_serveur_repond_ok_version_heure():
    reponse = reponse_ping()
    assert reponse.startswith("ok")
    assert VERSION_SERVEUR in reponse
    assert "UTC" in reponse


def test_ping_serveur_sans_tiret_double():
    # Règle MUSE.md : jamais de "--" dans un texte affiché.
    assert "--" not in reponse_ping()


def test_ping_serveur_enregistre_sur_le_serveur():
    outils = asyncio.run(mcp_diagnostic.list_tools())
    assert "ping_serveur" in {o.name for o in outils}


if __name__ == "__main__":
    test_ping_serveur_repond_ok_version_heure()
    test_ping_serveur_sans_tiret_double()
    test_ping_serveur_enregistre_sur_le_serveur()
    print("OK : sonde ping_serveur.")
