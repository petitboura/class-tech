"""Tests du palier 100 % (fonctions pures, sans téléphone).

Sans dépendance externe : tourne avec pytest comme avec un simple
`python tests/test_diagnostic_100.py` depuis le dossier backend/.
Seules les fonctions pures (pont_adb, analyse_materiel,
analyse_systeme) sont testées ici ; les wrappers MCP fins restent
couverts par le contrôle d'enregistrement (mcp installé).
"""

import os
import sys
import tempfile
import wave
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.analyse_materiel import (  # noqa: E402
    analyser_boutons,
    analyser_camera,
    analyser_ecoute_boutons,
    analyser_ecran,
    analyser_gps,
    analyser_haut_parleur,
    analyser_micro,
    analyser_vibreur,
    generer_bip_wav,
    lister_peripheriques_entree,
)
from core.analyse_systeme import (  # noqa: E402
    analyser_cpu,
    analyser_memoire,
    analyser_mises_a_jour,
    analyser_permissions,
    analyser_securite,
    analyser_top,
    formater_date_patch,
    formater_mo,
    normaliser_permission,
)
from core.pont_adb import analyser_sortie_devices  # noqa: E402

GETEVENT_PLEIN = """add device 1: /dev/input/event2
  name:     "Atmel maXTouch Touchscreen"
  events:
    KEY (0001): 0066
    ABS (0003): 0000  : value 0, min 0, max 1079, fuzz 0, flat 0, resolution 0
                0001  : value 0, min 0, max 1919, fuzz 0, flat 0, resolution 0
                0035  : value 0, min 0, max 1079, fuzz 0, flat 0, resolution 0
                0036  : value 0, min 0, max 1919, fuzz 0, flat 0, resolution 0
add device 2: /dev/input/event1
  name:     "gpio-keys"
  events:
    KEY (0001): 0072 0073 0074
"""

GETEVENT_SANS_TACTILE = """add device 1: /dev/input/event1
  name:     "gpio-keys"
  events:
    KEY (0001): 0072 0073 0074
"""


def test_devices_trie_prets_non_autorises_autres():
    sortie = "List of devices attached\nABC123\tdevice\nDEF456\tunauthorized\nGHI789\toffline\n"
    tri = analyser_sortie_devices(sortie)
    assert tri == {"prets": ["ABC123"], "non_autorises": ["DEF456"], "autres": ["GHI789"]}


def test_devices_vide():
    assert analyser_sortie_devices("List of devices attached\n\n") == {
        "prets": [], "non_autorises": [], "autres": [],
    }
    assert analyser_sortie_devices("") == {"prets": [], "non_autorises": [], "autres": []}


def test_peripheriques_tactile_et_boutons():
    peripheriques = lister_peripheriques_entree(GETEVENT_PLEIN)
    assert len(peripheriques) == 2
    tactile = peripheriques[0]
    assert "Touch" in tactile["nom"]
    assert tactile["touches"] == [0x66]
    assert 0x35 in tactile["absolus"]
    assert 0x36 in tactile["absolus"]
    assert 1079 not in tactile["absolus"]
    touches = peripheriques[1]
    assert touches["touches"] == [0x72, 0x73, 0x74]


def test_ecran_tactile_complet():
    analyse = analyser_ecran(GETEVENT_PLEIN, "Physical size: 1080x2400\n", "Physical density: 440\n", "  mScreenState=ON\n")
    assert analyse["tactile_detecte"] is True
    assert analyse["multitouch"] is True
    assert analyse["taille"] == "1080x2400"
    assert analyse["densite"] == "440"
    assert analyse["ecran_allume"] is True
    assert "multipoint" in analyse["resume"]


def test_ecran_sans_tactile():
    analyse = analyser_ecran(GETEVENT_SANS_TACTILE, "", "", "")
    assert analyse["tactile_detecte"] is False
    assert "Aucun écran tactile" in analyse["resume"]


def test_gps_haute_precision_avec_position():
    sortie = (
        "Current Location Providers:\n  gps=true, network=true, passive=true\n"
        "Last Known Locations:\n  last location=Location[gps 48,85,2,35]\n"
    )
    analyse = analyser_gps("3\n", sortie)
    assert analyse["mode_libelle"] == "haute précision (GPS et réseau)"
    assert analyse["gps_actif"] is True
    assert analyse["position_connue"] is True
    assert "GPS est actif" in analyse["resume"]


def test_gps_coupe():
    analyse = analyser_gps("0\n", "")
    assert analyse["mode_libelle"] == "localisation coupée"
    assert analyse["gps_actif"] is False
    assert "coupée" in analyse["resume"]


def test_micro_detecte_ou_non():
    oui = analyser_micro("input devices:\n  AUDIO_DEVICE_IN_BUILTIN_MIC: Built-in Microphone\n")
    assert oui["micro_detecte"] is True
    non = analyser_micro("input devices:\n  AUDIO_DEVICE_IN_DEFAULT: Default\n")
    assert non["micro_detecte"] is False
    assert "mémo vocal" in non["resume"]


def test_haut_parleur_volumes():
    sortie = (
        "STREAM_MUSIC: Muted: false, Min: 0, Max: 15, Current: 2 (speaker): 7\n"
        "STREAM_RING: Muted: true, Min: 0, Max: 7, Current: 2 (speaker): 0\n"
        "Audio mode: MODE_NORMAL\n"
    )
    analyse = analyser_haut_parleur(sortie)
    assert analyse["volumes"]["music"] == {"muet": False, "maximum": 15, "courant": 7}
    assert analyse["volumes"]["ring"]["muet"] is True
    assert analyse["mode"] == "MODE_NORMAL"
    assert "7 sur 15" in analyse["resume"]
    assert "coupé ou à zéro" in analyse["resume"]


def test_vibreur_present_ou_non():
    oui = analyser_vibreur("VibratorService state:\n  capabilities: VIBRATE\n", True)
    assert oui["present"] is True
    non = analyser_vibreur("", False)
    assert non["present"] is False


def test_camera_deux_et_zero():
    sortie = (
        "Number of camera devices: 2\nDevice 0 facing: BACK\nDevice 1 facing: FRONT\n"
    )
    analyse = analyser_camera(sortie)
    assert analyse["nombre"] == 2
    assert analyse["facades"] == ["arrière", "avant"]
    assert "2 caméras" in analyse["resume"]
    vide = analyser_camera("Number of camera devices: 0\n")
    assert vide["nombre"] == 0
    assert "Aucune caméra" in vide["resume"]


def test_boutons_inventaire():
    analyse = analyser_boutons(GETEVENT_PLEIN)
    assert analyse["boutons"] == ["accueil", "volume bas", "volume haut", "marche/arrêt"]


def test_ecoute_boutons_nommee_et_brute():
    sortie = (
        "[ 1234.567] /dev/input/event1: EV_KEY       KEY_VOLUMEUP         DOWN\n"
        "[ 1234.589] /dev/input/event1: EV_KEY       KEY_VOLUMEUP         UP\n"
        "[ 1235.001] /dev/input/event1: 0001 0072 00000001\n"
    )
    analyse = analyser_ecoute_boutons(sortie)
    assert "volumeup" in analyse["touches_appuyees"]
    assert "volume bas" in analyse["touches_appuyees"]
    assert len(analyse["touches_appuyees"]) == 2


def test_ecoute_boutons_silence():
    analyse = analyser_ecoute_boutons("")
    assert analyse["touches_appuyees"] == []
    assert "Aucune touche" in analyse["resume"]


def test_generer_bip_wav_valide():
    with tempfile.TemporaryDirectory(prefix="classtech-test") as dossier:
        chemin = os.path.join(dossier, "bip.wav")
        generer_bip_wav(chemin, duree_ms=100)
        assert os.path.getsize(chemin) > 1000
        with wave.open(chemin, "rb") as wav:
            assert wav.getnchannels() == 1
            assert wav.getframerate() == 22050
            assert wav.getnframes() > 1000


def test_formater_mo_et_date():
    assert formater_mo(512) == "512 Mo"
    assert formater_mo(3072) == "3,0 Go"
    assert formater_date_patch("2026-09-05") == "5 septembre 2026"
    assert formater_date_patch("pas une date") is None
    assert formater_date_patch("") is None


def test_memoire_correcte_juste_critique():
    base = "MemTotal:        8192000 kB\nMemAvailable:    {dispo} kB\n"
    large = analyser_memoire(base.format(dispo=4096000))
    assert large["pct_disponible"] == 50
    assert "Niveau correct" in large["resume"]
    juste = analyser_memoire(base.format(dispo=1024000))
    assert juste["pct_disponible"] in (12, 13)
    assert "un peu juste" in juste["resume"]
    critique = analyser_memoire(base.format(dispo=409600))
    assert critique["pct_disponible"] == 5
    assert "Très peu" in critique["resume"]
    illisible = analyser_memoire("du bruit\n")
    assert illisible["pct_disponible"] is None
    assert "illisible" in illisible["resume"]


def test_cpu_coeurs_et_charge():
    cpuinfo = (
        "processor\t: 0\nHardware\t: Qualcomm Snapdragon\n"
        "processor\t: 1\nprocessor\t: 2\nprocessor\t: 3\n"
    )
    calme = analyser_cpu(cpuinfo, "0.50 0.40 0.30 1/200 12345\n")
    assert calme["coeurs"] == 4
    assert "Snapdragon" in calme["modele"]
    assert "calme" in calme["resume"]
    charge = analyser_cpu(cpuinfo, "9.00 5.00 2.00 1/200 12345\n")
    assert "très sollicité" in charge["resume"]
    vide = analyser_cpu("", "")
    assert vide["coeurs"] is None
    assert "illisible" in vide["resume"]


def test_top_cpu_et_ram():
    top = (
        "Tasks: 200 total\n"
        " 1234 u0_a10 10 -10 2,1G 180M 90M S 45% com.gros.jeu\n"
        " 5678 u0_a20 10 -10 1,2G 90M 40M S 12% com.reseau.social\n"
    )
    meminfo = (
        "  184320K: com.gros.jeu (pid 1234 / activities)\n"
        "   92160K: com.reseau.social (pid 5678 / activities)\n"
    )
    analyse = analyser_top(top, meminfo)
    assert analyse["top_cpu"][0]["nom"] == "com.gros.jeu"
    assert analyse["top_cpu"][0]["cpu_pct"] == 45.0
    assert analyse["top_ram"][0] == {"paquet": "com.gros.jeu", "mo": 180}
    assert "com.gros.jeu" in analyse["resume"]
    assert "180 Mo" in analyse["resume"]


def test_permissions_tierces_et_systeme():
    sortie = (
        "Packages:\n"
        "Package [com.lampe.torche] (id=10001):\n"
        "  userId=10001\n"
        "  codePath=/data/app/com.lampe.torche\n"
        "  runtime permissions:\n"
        "    android.permission.CAMERA: granted=true, flags=[ GRANTED_BY_DEFAULT ]\n"
        "    android.permission.ACCESS_FINE_LOCATION: granted=true, flags=[]\n"
        "    android.permission.INTERNET: granted=true, flags=[]\n"
        "Package [com.android.systeme] (id=1000):\n"
        "  codePath=/system/priv-app/Systeme\n"
        "  runtime permissions:\n"
        "    android.permission.READ_CONTACTS: granted=true, flags=[]\n"
        "    android.permission.RECORD_AUDIO: granted=false, flags=[]\n"
    )
    tierces = analyser_permissions(sortie, "tierces")
    assert tierces["total"] == 1
    assert tierces["applications"][0]["paquet"] == "com.lampe.torche"
    assert len(tierces["applications"][0]["permissions"]) == 2
    assert "dont 1 avec 2 ou plus" in tierces["resume"]
    systeme = analyser_permissions(sortie, "systeme")
    assert systeme["total"] == 1
    assert systeme["applications"][0]["paquet"] == "com.android.systeme"
    assert len(systeme["applications"][0]["permissions"]) == 1
    toutes = analyser_permissions(sortie, "toutes")
    assert toutes["total"] == 2


def test_normaliser_permission():
    assert normaliser_permission("localisation") == [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
    ]
    assert normaliser_permission("android.permission.CAMERA") == ["android.permission.CAMERA"]
    assert normaliser_permission("  Micro  ") == ["android.permission.RECORD_AUDIO"]
    assert normaliser_permission("teleportation") == []
    assert normaliser_permission("") == []


def test_securite_tout_bon():
    donnees = {
        "patch": "2026-10-01", "bootloader": "locked", "crypto": "encrypted",
        "sources_inconnues": "0", "adb_active": "1",
    }
    analyse = analyser_securite(donnees, aujourd_hui=date(2026, 10, 28))
    assert "1 octobre 2026" in analyse["resume"]
    assert analyse["resume"].count("(bon)") == 4
    assert "couper après le diagnostic" in analyse["resume"]


def test_securite_patch_ancien_et_bootloader_ouvert():
    donnees = {
        "patch": "2025-01-05", "bootloader": "unlocked", "crypto": "encrypted",
        "sources_inconnues": "1", "adb_active": "0",
    }
    analyse = analyser_securite(donnees, aujourd_hui=date(2026, 10, 28))
    assert "très en retard" in analyse["resume"]
    assert "déverrouillé" in analyse["resume"]
    assert "autorisées" in analyse["resume"]


def test_securite_illisible():
    analyse = analyser_securite({}, aujourd_hui=date(2026, 10, 28))
    assert "non vérifié" in analyse["resume"]


def test_mises_a_jour_selon_age():
    recent = analyser_mises_a_jour("15", "2026-09-05", aujourd_hui=date(2026, 10, 28))
    assert recent["version"] == "15"
    assert recent["patch"] == "5 septembre 2026"
    assert "à jour" in recent["resume"]
    vieux = analyser_mises_a_jour("12", "2025-06-01", aujourd_hui=date(2026, 10, 28))
    assert "très en retard" in vieux["resume"]
    assert "Mise à jour logicielle" in vieux["resume"]


def test_aucun_tiret_double_dans_les_resumes():
    # Règle MUSE.md : jamais de "--" dans un texte affiché.
    resumes = [
        analyser_ecran(GETEVENT_PLEIN, "", "", "")["resume"],
        analyser_gps("3\n", "")["resume"],
        analyser_micro("")["resume"],
        analyser_haut_parleur("")["resume"],
        analyser_vibreur("", False)["resume"],
        analyser_camera("")["resume"],
        analyser_boutons(GETEVENT_PLEIN)["resume"],
        analyser_ecoute_boutons("")["resume"],
        analyser_memoire("")["resume"],
        analyser_cpu("", "")["resume"],
        analyser_top("", "")["resume"],
        analyser_permissions("")["resume"],
        analyser_securite({})["resume"],
        analyser_mises_a_jour("", "")["resume"],
    ]
    for resume in resumes:
        assert "--" not in resume, resume


if __name__ == "__main__":
    test_devices_trie_prets_non_autorises_autres()
    test_devices_vide()
    test_peripheriques_tactile_et_boutons()
    test_ecran_tactile_complet()
    test_ecran_sans_tactile()
    test_gps_haute_precision_avec_position()
    test_gps_coupe()
    test_micro_detecte_ou_non()
    test_haut_parleur_volumes()
    test_vibreur_present_ou_non()
    test_camera_deux_et_zero()
    test_boutons_inventaire()
    test_ecoute_boutons_nommee_et_brute()
    test_ecoute_boutons_silence()
    test_generer_bip_wav_valide()
    test_formater_mo_et_date()
    test_memoire_correcte_juste_critique()
    test_cpu_coeurs_et_charge()
    test_top_cpu_et_ram()
    test_permissions_tierces_et_systeme()
    test_normaliser_permission()
    test_securite_tout_bon()
    test_securite_patch_ancien_et_bootloader_ouvert()
    test_securite_illisible()
    test_mises_a_jour_selon_age()
    test_aucun_tiret_double_dans_les_resumes()
    print("OK : palier 100 %, fonctions pures.")
