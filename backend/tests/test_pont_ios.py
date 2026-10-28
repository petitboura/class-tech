"""Tests du pont iOS PC vers iPhone (libimobiledevice, lecture seule).

Sans dependance externe : tourne avec pytest comme avec un simple
`python tests/test_pont_ios.py` depuis le dossier backend/.
Aucun iPhone requis : les parseurs sont testes sur des exemples
realistes, et les appels reels sans iPhone renvoient simplement le
message d'absence, qui est lui aussi verifie.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.pont_ios import (  # noqa: E402
    choisir_iphone,
    erreur_courte_ios,
    iphones_connectes,
    message_aucun_iphone,
    message_outils_ios_absents,
    parse_ideviceinfo,
    parse_sortie_idevice_id,
    parse_validation_appairage,
    preparer_appel_ios,
    resumer_liaison_ios,
    trouver_outil_ios,
)

SORTIE_IDEVIDE = ""
SORTIE_ID_UN = "00008110-000A1B2C3D4E5F6A\n"
SORTIE_ID_DEUX = "00008110-000A1B2C3D4E5F6A\n00008110-000A1B2C3D4E5F6B\n"

SORTIE_IDEVICEINFO = """DeviceName: iPhone de Bourama
ProductName: iPhone OS
ProductType: iPhone16,2
ProductVersion: 17.5.1
BuildVersion: 21F90
ModelNumber: MT123ZD/A
SerialNumber: F2LXABCD1234
UniqueDeviceID: 00008110-000A1B2C3D4E5F6A
"""

SORTIE_BATTERIE = """BatteryCurrentCapacity: 82
BatteryIsCharging: true
"""

SORTIE_STOCKAGE = """TotalDiskCapacity: 128000000000
AmountDataAvailable: 45000000000
"""


def test_parse_idevice_id_vide():
    assert parse_sortie_idevice_id(SORTIE_IDEVIDE) == []
    assert parse_sortie_idevice_id(None) == []


def test_parse_idevice_id_un():
    assert parse_sortie_idevice_id(SORTIE_ID_UN) == ["00008110-000A1B2C3D4E5F6A"]


def test_parse_idevice_id_deux():
    assert parse_sortie_idevice_id(SORTIE_ID_DEUX) == [
        "00008110-000A1B2C3D4E5F6A",
        "00008110-000A1B2C3D4E5F6B",
    ]


def test_parse_idevice_id_ignore_erreurs():
    texte = "ERROR: No device found!\n00008110-000A1B2C3D4E5F6A\n"
    assert parse_sortie_idevice_id(texte) == ["00008110-000A1B2C3D4E5F6A"]


def test_parse_ideviceinfo():
    infos = parse_ideviceinfo(SORTIE_IDEVICEINFO)
    assert infos["DeviceName"] == "iPhone de Bourama"
    assert infos["ProductVersion"] == "17.5.1"
    assert infos["UniqueDeviceID"] == "00008110-000A1B2C3D4E5F6A"
    assert parse_ideviceinfo("") == {}


def test_parse_ideviceinfo_domaines():
    batterie = parse_ideviceinfo(SORTIE_BATTERIE)
    assert batterie == {"BatteryCurrentCapacity": "82", "BatteryIsCharging": "true"}
    stockage = parse_ideviceinfo(SORTIE_STOCKAGE)
    assert stockage["TotalDiskCapacity"] == "128000000000"


def test_choisir_iphone():
    assert choisir_iphone([]) is None
    assert choisir_iphone(["A", "B"]) == "A"


def test_parse_validation_appairage():
    assert parse_validation_appairage("SUCCESS: Validated pairing with device", True)
    assert not parse_validation_appairage("SUCCESS: Validated pairing with device", False)
    assert not parse_validation_appairage("ERROR: No device found!", False)
    assert not parse_validation_appairage("", True)


def test_erreur_courte_ios():
    assert erreur_courte_ios("") == "commande refusee par l'iPhone."
    assert "--" not in erreur_courte_ios("a -- b " * 100)
    assert len(erreur_courte_ios("x" * 500)) <= 201


def test_messages_sans_tiret_double():
    assert "--" not in message_outils_ios_absents()
    assert "--" not in message_aucun_iphone([])
    assert "--" not in message_aucun_iphone(["A"], confiance_refusee=True)


def test_message_aucun_iphone_guide():
    assert "USB" in message_aucun_iphone([])
    assert "confiance" in message_aucun_iphone(["A"], confiance_refusee=True)


def test_trouver_outil_sans_crash():
    trouve = trouver_outil_ios("idevice_id_qui_n_existe_pas")
    assert trouve is None


def test_liaison_sans_iphone_ne_leve_jamais():
    udids, raison = iphones_connectes()
    assert raison in ("ok", "outils_absents", "erreur")
    assert isinstance(udids, list)
    liaison = resumer_liaison_ios()
    assert set(liaison) == {"outils_trouves", "udids", "udid_choisi",
                            "confiance", "pret", "message"}
    udid, message = preparer_appel_ios()
    if liaison["pret"]:
        assert udid and message is None
    else:
        assert udid is None and message
