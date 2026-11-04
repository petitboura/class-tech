"""Page de santé du relais PC : version, nombre d'outils, outils hors relais."""

import os
import sys

os.environ.setdefault("MCP_HOTE_PUBLIC", "test")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "relais"))

from fastapi.testclient import TestClient  # noqa: E402

import serveur_relais  # noqa: E402
from core.outils_diagnostic_commun import VERSION_SERVEUR  # noqa: E402


def test_sante_donne_version_et_nombre_d_outils():
    reponse = TestClient(serveur_relais.app).get("/relais/sante").json()
    assert reponse["ok"] is True
    assert reponse["version"] == VERSION_SERVEUR
    assert reponse["nombre_outils"] == len(reponse["outils"])


def test_sante_liste_les_outils_declares_mais_non_relayes():
    reponse = TestClient(serveur_relais.app).get("/relais/sante").json()
    hors = reponse["outils_hors_relais"]
    assert isinstance(hors, list)
    # Rien de ce que le relais exécute ne doit apparaître comme absent.
    assert not set(hors) & set(reponse["outils"])
    # Les outils root sont refusés par construction : jamais listés ici.
    assert not any(nom.startswith("root") for nom in hors)
