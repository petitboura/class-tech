"""Tests du pont ADB PC vers telephone (palier 80 %).

Sans dependance externe : tourne avec pytest comme avec un simple
`python tests/test_pont_adb.py` depuis le dossier backend/.
Aucun telephone requis : les appels reels renvoient simplement le
message d'absence, qui est lui aussi verifie.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.pont_adb import (  # noqa: E402
    appareils_connectes,
    choisir_appareil,
    message_adb_absent,
    message_aucun_telephone,
    parametre_shell_valide,
    parse_sortie_devices,
    preparer_appel,
    resumer_liaison,
    trouver_adb,
)

SORTIE_VIDE = "List of devices attached\n\n"
SORTIE_UN_APPAREIL = (
    "List of devices attached\n"
    "ABC123\tdevice product:a54x device:a54x model:Galaxy_A54\n"
)
SORTIE_NON_AUTORISE = "List of devices attached\nXYZ999\tunauthorized\n"


def test_parse_devices_vide():
    assert parse_sortie_devices(SORTIE_VIDE) == []
    assert parse_sortie_devices("") == []


def test_parse_devices_un_appareil():
    appareils = parse_sortie_devices(SORTIE_UN_APPAREIL)
    assert appareils == [{"id": "ABC123", "etat": "device"}]


def test_parse_devices_non_autorise():
    appareils = parse_sortie_devices(SORTIE_NON_AUTORISE)
    assert appareils == [{"id": "XYZ999", "etat": "unauthorized"}]


def test_choisir_appareil():
    assert choisir_appareil([]) is None
    assert choisir_appareil([{"id": "X", "etat": "unauthorized"}]) is None
    appareils = [
        {"id": "X", "etat": "offline"},
        {"id": "Y", "etat": "device"},
    ]
    assert choisir_appareil(appareils) == {"id": "Y", "etat": "device"}


def test_parametre_shell_valide():
    assert parametre_shell_valide("/sdcard")
    assert parametre_shell_valide("/sdcard/Mes photos")
    assert not parametre_shell_valide("")
    assert not parametre_shell_valide("/sdcard; rm -rf /")
    assert not parametre_shell_valide("/sdcard && id")
    assert not parametre_shell_valide("/sdcard | head")
    assert not parametre_shell_valide("/sdcard/../system")
    assert not parametre_shell_valide("x" * 201)


def test_messages_sans_tiret_double():
    # Regle MUSE.md : jamais de "--" dans un texte affiche.
    assert "--" not in message_adb_absent()
    assert "--" not in message_aucun_telephone([])
    assert "--" not in message_aucun_telephone([{"id": "X", "etat": "offline"}])


def test_message_aucun_telephone_guide():
    texte = message_aucun_telephone([])
    assert "USB" in texte
    assert "developpeur" in texte
    texte_offline = message_aucun_telephone([{"id": "X", "etat": "offline"}])
    assert "X" in texte_offline


def test_trouver_adb_coherent():
    chemin = trouver_adb()
    assert chemin is None or os.path.isfile(chemin)


def test_liaison_reelle_coherente():
    liaison = resumer_liaison()
    assert set(liaison) == {"adb_trouve", "adb_chemin", "appareils",
                            "appareil_choisi", "pret", "message"}
    if liaison["pret"]:
        assert liaison["message"] is None
        assert liaison["appareil_choisi"]["etat"] == "device"
    else:
        assert liaison["message"]
        assert "--" not in liaison["message"]
    appareils, raison = appareils_connectes()
    assert raison in ("ok", "adb_absent", "erreur")
    assert isinstance(appareils, list)
    appareil_id, erreur = preparer_appel()
    assert (appareil_id is None) != (erreur is None)


if __name__ == "__main__":
    test_parse_devices_vide()
    test_parse_devices_un_appareil()
    test_parse_devices_non_autorise()
    test_choisir_appareil()
    test_parametre_shell_valide()
    test_messages_sans_tiret_double()
    test_message_aucun_telephone_guide()
    test_trouver_adb_coherent()
    test_liaison_reelle_coherente()
    print("OK : pont ADB.")
