"""Le relais PC : 5 outils sensibles acceptes, root toujours refuse.

Les 5 outils sensibles agissent vraiment sur le telephone : Classinus exige
la confirmation de l'utilisateur AVANT de les envoyer au relais. Le relais,
lui, ne doit plus les refuser. Les outils root restent refuses par
construction. Aucun telephone n'est necessaire : sans adb, les outils
repondent par un message clair, sans effet.
"""

import os
import sys

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RACINE, "relais"))

fastapi_testclient = pytest.importorskip("fastapi.testclient")

import serveur_relais  # noqa: E402

SENSIBLES = (
    "vider_cache_applis",
    "tester_haut_parleur",
    "tester_vibreur",
    "tester_camera",
    "revoquer_permission",
)


PROFONDS = (
    "lire_temperatures_internes",
    "lire_historique_batterie",
    "lire_trafic_par_appli",
    "lire_fluidite_ecran",
    "lire_saturation_systeme",
    "lire_reveils_planifies",
    "lire_journaux_systeme",
    "lire_carte_systeme",
    "lire_memoire_dans_le_temps",
    "lire_verrous_veille",
)


@pytest.fixture(scope="module")
def client():
    return fastapi_testclient.TestClient(serveur_relais.app)


def test_les_5_outils_sensibles_sont_dans_le_relais():
    for nom in SENSIBLES:
        assert nom in serveur_relais.OUTILS_LECTURE


@pytest.mark.parametrize("nom", ["root_redemarrer", "root_forcer_trim", "root_lire_infos_root"])
def test_root_toujours_refuse(client, nom):
    reponse = client.post(f"/relais/outil/{nom}", json={}).json()
    assert reponse["ok"] is False
    assert "root" in reponse["erreur"]


def test_outil_inconnu_refuse(client):
    reponse = client.post("/relais/outil/n_importe_quoi", json={}).json()
    assert reponse["ok"] is False
    assert "inconnu" in reponse["erreur"]


def test_revoquer_permission_sans_arguments_donne_une_erreur_claire(client):
    reponse = client.post("/relais/outil/revoquer_permission", json={}).json()
    assert reponse["ok"] is False
    assert "Arguments" in reponse["erreur"]


def test_les_10_outils_profonds_sont_dans_le_relais():
    for nom in PROFONDS:
        assert nom in serveur_relais.OUTILS_LECTURE


@pytest.mark.parametrize("nom", PROFONDS)
def test_outil_profond_est_execute_et_pas_refuse(client, nom):
    reponse = client.post(f"/relais/outil/{nom}", json={}).json()
    assert reponse["ok"] is True
    assert "inconnu" not in str(reponse.get("erreur", ""))
    assert "refusé" not in str(reponse.get("erreur", ""))
