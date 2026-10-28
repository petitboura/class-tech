"""Tests des 4 outils iPhone portes (detection, batterie, stockage, version).

Demande les dependances installees (mcp) : depuis le dossier backend/,
`pip install -r requirements.txt` puis `pytest tests` (ou ce fichier seul
avec `python tests/test_outils_iphone.py`).

Aucun iPhone requis : les formateurs sont testes sur des exemples
realistes de sorties libimobiledevice, et les appels reels sans iPhone
renvoient le message d'absence standard.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.outils_iphone_base import (  # noqa: E402
    detecter_iphone,
    formater_batterie_ios,
    formater_detection_ios,
    formater_stockage_ios,
    formater_version_ios,
    lire_batterie_iphone,
    lire_stockage_iphone,
    lire_version_iphone,
    octets_vers_go,
    texte_detection_ios,
)
from core.registre_outils import REGISTRE_AFFICHAGE_OUTILS  # noqa: E402

LIAISON_PRETE = {
    "outils_trouves": True,
    "udids": ["00008110-000A1B2C3D4E5F6A"],
    "udid_choisi": "00008110-000A1B2C3D4E5F6A",
    "confiance": True,
    "pret": True,
    "message": None,
}

SORTIE_IDEVICEINFO = """DeviceName: iPhone de Bourama
ProductName: iPhone OS
ProductType: iPhone16,2
ProductVersion: 17.5.1
BuildVersion: 21F90
ModelNumber: MT123ZD/A
"""


def test_detection_prete():
    texte = texte_detection_ios(LIAISON_PRETE, SORTIE_IDEVICEINFO)
    assert "iPhone detecte et pret" in texte
    assert "iOS 17.5.1" in texte
    assert "iPhone de Bourama" in texte


def test_detection_non_prete():
    liaison = dict(LIAISON_PRETE, pret=False, message="Branche l'iPhone.")
    assert formater_detection_ios(liaison, {}) == "Branche l'iPhone."


def test_detection_sans_tiret_double():
    assert "--" not in texte_detection_ios(LIAISON_PRETE, SORTIE_IDEVICEINFO)


def test_batterie():
    texte = formater_batterie_ios({"BatteryCurrentCapacity": "82",
                                   "BatteryIsCharging": "true"})
    assert "82 %" in texte
    assert "en charge" in texte
    assert formater_batterie_ios({}) == "Etat batterie illisible pour le moment."


def test_octets_vers_go():
    assert octets_vers_go("1073741824") == 1.0
    assert octets_vers_go("") is None
    assert octets_vers_go("pas un nombre") is None


def test_stockage():
    texte = formater_stockage_ios({"TotalDiskCapacity": "128000000000",
                                   "AmountDataAvailable": "45000000000"})
    assert "Go libres" in texte
    assert "128000000000" not in texte
    assert formater_stockage_ios({}) == "Espace disque illisible pour le moment."


def test_stockage_presque_plein():
    texte = formater_stockage_ios({"TotalDiskCapacity": "100000000000",
                                   "AmountDataAvailable": "5000000000"})
    assert "presque plein" in texte


def test_version():
    texte = formater_version_ios({"ProductVersion": "17.5.1", "BuildVersion": "21F90"})
    assert "iOS 17.5.1" in texte
    assert formater_version_ios({}) == "Version systeme illisible pour le moment."


def test_registre_iphone():
    for nom in ("detecter_iphone", "lire_batterie_iphone",
                "lire_stockage_iphone", "lire_version_iphone"):
        entree = REGISTRE_AFFICHAGE_OUTILS[nom]
        assert entree["label"]
        assert entree["icone"]
        assert entree["onglet"] == "diagnostiquer"


def test_outils_sans_iphone():
    # Sans iPhone branché : message d'absence standard, jamais d'exception.
    for outil in (detecter_iphone, lire_batterie_iphone,
                  lire_stockage_iphone, lire_version_iphone):
        assert isinstance(outil(), str)
