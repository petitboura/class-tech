"""Tests des 14 outils telephone du palier 80 %.

Demande les dependances installees (mcp) : depuis le dossier backend/,
`pip install -r requirements.txt` puis `pytest tests` (ou ce fichier seul
avec `python tests/test_outils_80.py`).

Aucun telephone requis : les parseurs sont testes sur des exemples
realistes de sorties Android, et les appels reels sans telephone
renvoient le message d'absence standard.
"""

import asyncio
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.outils_telephone_applis import (  # noqa: E402
    formater_applis,
    formater_crashs,
    formater_inutilisees,
    lire_crashs_recents,
    lister_applis,
    lister_applis_inutilisees,
    parse_dropbox_crashs,
    parse_liste_packages,
    parse_logcat_crash,
    parse_usagestats,
    selectionner_inutilisees,
)
from core.outils_telephone_base import (  # noqa: E402
    detecter_telephone,
    parse_getprop,
    texte_detection,
)
from core.outils_telephone_batterie import (  # noqa: E402
    formater_batterie,
    formater_conso,
    lire_batterie,
    lire_conso_batterie,
    parse_conso_batterystats,
    parse_dumpsys_battery,
    parse_paquets_uid,
    uid_android_vers_nombre,
)
from core.outils_telephone_capteurs import (  # noqa: E402
    formater_capteurs,
    parse_sensorservice,
)
from core.outils_telephone_capteurs import tester_capteurs as outil_tester_capteurs  # noqa: E402
from core.outils_telephone_reseau import (  # noqa: E402
    formater_reseau,
    formater_wifi,
    lire_etat_reseau,
    lire_infos_wifi,
    parse_connectivite,
    parse_wifi,
)
from core.outils_telephone_stockage import (  # noqa: E402
    _octets_liberes,
    formater_gros_fichiers,
    formater_stockage,
    lire_stockage,
    lister_gros_fichiers,
    parse_df,
    parse_gros_fichiers,
    taille_en_octets,
    vider_cache_applis,
)
from core.outils_telephone_systeme import (  # noqa: E402
    formater_erreurs,
    formater_version,
    lire_erreurs_recentes,
    lire_version_systeme,
    parse_logcat_erreurs,
)
from api.main import _hote_de_valeur, hotes_publics_autorises  # noqa: E402
from core.pont_adb import resumer_liaison  # noqa: E402
from core.registre_outils import (  # noqa: E402
    CATEGORIES_OUTILS,
    OUTILS_PALIER_80,
    OUTILS_SENSIBLES,
    REGISTRE_AFFICHAGE_OUTILS,
)
from core.serveur_mcp_diagnostic import mcp_diagnostic  # noqa: E402

GETPROP_EXEMPLE = """[ro.product.manufacturer]: [Samsung]
[ro.product.brand]: [samsung]
[ro.product.model]: [Galaxy A54]
[ro.build.version.release]: [14]
[ro.build.version.sdk]: [34]
[ro.build.version.security_patch]: [2026-09-01]
[ro.build.id]: [UP1A.231005.007]
ligne cassee sans crochet
"""

BATTERIE_EXEMPLE = """Current Battery Service state:
  AC powered: false
  USB powered: true
  Wireless powered: false
  status: 2
  health: 2
  present: true
  level: 87
  scale: 100
  voltage: 4192
  temperature: 285
  technology: Li-ion
"""

BATTERYSTATS_EXEMPLE = """Statistics since last charge:
  System starts: 0
Estimated power use (mAh):
    Capacity: 4000, Computed drain: 812.4, actual drain: 790.2
    Screen: 301.5
    Uid u0a123 (com.reseaux.gourmand): 145.2
    Uid u0a456: 88.0
    Uid u0a789 (com.jeu.video): 12.7
    Idle: 45.1
"""

PM_UID_EXEMPLE = """package:com.reseaux.gourmand uid:10123
package:com.messagerie.app uid:10456
package:com.jeu.video uid:10789
"""

DF_EXEMPLE = """Filesystem      Size  Used Avail Use% Mounted on
/dev/block/dm-5
                110G   95G   15G  87% /data
/dev/fuse       120G  118G  2.0G  99% /sdcard
"""

LS_EXEMPLE = """-rw-rw---- 1 root sdcard_rw 1.2G 2026-10-20 14:01 /sdcard/video.mp4
-rw-rw---- 1 root sdcard_rw 850M 2026-09-01 09:12 /sdcard/sauvegarde.zip
-rw-rw---- 1 root sdcard_rw 95M 2026-10-27 08:00 /sdcard/photo.jpg
total 2.1G
"""

PAQUETS_EXEMPLE = """package:com.jeu.video
package:com.banque.app versionCode:42 minSdk:29
package:com.jeu.video
"""

CRASH_EXEMPLE = """10-27 10:11:12.345 E/AndroidRuntime( 1234): FATAL EXCEPTION: main
10-27 10:11:12.346 E/AndroidRuntime( 1234): Process: com.jeu.video, PID: 1234
10-27 10:11:12.347 E/AndroidRuntime( 1234): java.lang.NullPointerException: appel sur objet nul
10-27 11:02:01.100 E/AndroidRuntime( 5678): FATAL EXCEPTION: pool
10-27 11:02:01.101 E/AndroidRuntime( 5678): Process: com.reseaux.gourmand, PID: 5678
10-27 11:02:01.102 E/AndroidRuntime( 5678): android.os.NetworkOnMainThreadException
"""

DROPBOX_EXEMPLE = """data_app_crash @ 2026-10-27 10:11:12
Process: com.jeu.video
data_app_anr @ 2026-10-26 08:00:00
Subject: com.reseaux.gourmand
"""

USAGE_EXEMPLE = """  package=com.jeu.video lastTimeUsed=1729930000000 lastTimeVisible=1729930001000
  package=com.jeu.video lastTimeUsed=1729000000000 totalTimeUsed=1000
  package=com.banque.app lastTimeUsed=0 totalTimeUsed=0
"""

ERREURS_EXEMPLE = """10-27 10:11:12.345 E/WifiService(  500): echec de connexion
10-27 10:12:00.001 E/WifiService(  500): delai depasse
10-27 10:13:44.210 E/AudioFlinger(  300): underrun audio
ligne cassee
10-27 10:14:00.000 W/WifiService(  500): pas une erreur
"""

CONNECTIVITE_EXEMPLE = """Active default network: 105
NetworkAgentInfo [WIFI () - 105]
  state: CONNECTED
  isDefaultNetwork: true
NetworkAgentInfo [MOBILE () - 106]
  state: DISCONNECTED
"""

WIFI_EXEMPLE = """Wifi is enabled
mWifiInfo SSID: "Maison-5G", BSSID: aa:bb:cc:dd:ee:ff, RSSI: -52, Link speed: 433Mbps, Frequency: 5240MHz
"""

CAPTEURS_EXEMPLE = """Sensor List:
0x00000001) BMI160 Accelerometer | STMicroelectronics | ver: 1 | type: android.sensor.accelerometer(1)
0x00000002) BMI160 Gyroscope | STMicroelectronics | ver: 1 | type: android.sensor.gyroscope(4)
0x00000003) Proximity sensor | Samsung | ver: 1 | type: android.sensor.proximity(8)
Active sensors:
0x00000001) BMI160 Accelerometer (handle=0x00000001, connections=1)
"""


def appeler(fonction, *args, **kwargs):
    """Appelle un outil MCP de facon synchrone, qu'il soit sync ou async."""
    resultat = fonction(*args, **kwargs)
    if inspect.isawaitable(resultat):
        return asyncio.run(resultat)
    return resultat


def test_detection_getprop():
    infos = parse_getprop(GETPROP_EXEMPLE)
    assert infos["ro.product.model"] == "Galaxy A54"
    assert infos["ro.build.version.release"] == "14"
    assert parse_getprop("") == {}
    liaison = {"pret": True, "appareil_choisi": {"id": "ABC123"}, "appareils": []}
    texte = texte_detection(liaison, GETPROP_EXEMPLE)
    assert "Galaxy A54" in texte
    assert "Android 14" in texte
    assert "2026-09-01" in texte
    liaison_absente = {"pret": False, "message": "pas de telephone"}
    assert texte_detection(liaison_absente, "") == "pas de telephone"


def test_batterie():
    infos = parse_dumpsys_battery(BATTERIE_EXEMPLE)
    assert infos["level"] == "87"
    texte = formater_batterie(infos)
    assert "87 %" in texte
    assert "28.5" in texte
    assert "en charge" in texte
    assert "bonne" in texte
    assert "USB" in texte
    assert formater_batterie({}) != ""


def test_conso_batterie():
    lignes, drain = parse_conso_batterystats(BATTERYSTATS_EXEMPLE)
    assert [uid for uid, _p, _m in lignes] == ["u0a123", "u0a456", "u0a789"]
    assert drain == (812.4, 790.2)
    assert uid_android_vers_nombre("u0a123") == "10123"
    assert uid_android_vers_nombre("invalide") is None
    table = parse_paquets_uid(PM_UID_EXEMPLE)
    assert table["10123"] == ["com.reseaux.gourmand"]
    texte = formater_conso(lignes, table, drain, 10)
    assert "com.reseaux.gourmand" in texte
    assert "com.messagerie.app" in texte
    assert "Total calcule 812 mAh" in texte
    assert formater_conso([], {}, None) != ""


def test_stockage_df():
    disques = parse_df(DF_EXEMPLE)
    assert len(disques) == 2
    assert disques[0]["point"] == "/data"
    assert disques[1]["pct"] == 99
    texte = formater_stockage(disques)
    assert "presque plein" in texte
    assert formater_stockage([]) != ""
    assert taille_en_octets("1.2G") == int(1.2 * 1024 ** 3)
    assert taille_en_octets("850M") == 850 * 1024 ** 2
    assert taille_en_octets("nimporte") == -1


def test_gros_fichiers():
    trouves = parse_gros_fichiers(LS_EXEMPLE)
    assert [c for c, _t, _o in trouves] == [
        "/sdcard/video.mp4", "/sdcard/sauvegarde.zip", "/sdcard/photo.jpg"]
    texte = formater_gros_fichiers(trouves, 100, "/sdcard", limite=2)
    assert "video.mp4" in texte
    assert "1 autres" in texte
    assert "Aucun fichier" in formater_gros_fichiers([], 100, "/sdcard")
    avant = [{"point": "/data", "total": "x", "utilise": "x", "dispo": "1000", "pct": 50}]
    apres = [{"point": "/data", "total": "x", "utilise": "x", "dispo": "2000", "pct": 40}]
    assert _octets_liberes(avant, apres) == 1
    assert _octets_liberes([], apres) is None


def test_liste_applis():
    paquets = parse_liste_packages(PAQUETS_EXEMPLE)
    assert paquets == ["com.jeu.video", "com.banque.app"]
    texte = formater_applis(paquets, "installees", 1)
    assert "2 applis" in texte
    assert "1 autres" in texte


def test_crashs():
    crashs = parse_logcat_crash(CRASH_EXEMPLE)
    assert len(crashs) == 2
    assert crashs[0]["paquet"] == "com.jeu.video"
    assert "NullPointerException" in crashs[0]["erreur"]
    assert crashs[1]["paquet"] == "com.reseaux.gourmand"
    assert "2 plantage" in formater_crashs(crashs)
    replis = parse_dropbox_crashs(DROPBOX_EXEMPLE)
    assert len(replis) == 2
    assert replis[1]["paquet"] == "com.reseaux.gourmand"
    assert "Aucun plantage" in formater_crashs([])


def test_applis_inutilisees():
    usages = parse_usagestats(USAGE_EXEMPLE)
    assert usages["com.jeu.video"] == 1729930000000
    assert usages["com.banque.app"] == 0
    maintenant = 1761600000000
    inutilisees = selectionner_inutilisees(
        usages, ["com.jeu.video", "com.banque.app"], 90, maintenant)
    assert inutilisees[0] == ("com.banque.app", None)
    assert inutilisees[1][0] == "com.jeu.video"
    texte = formater_inutilisees(inutilisees, 90, 30)
    assert "com.banque.app" in texte
    assert "Aucune appli" in formater_inutilisees([], 90, 30)


def test_version_systeme():
    texte = formater_version(parse_getprop(GETPROP_EXEMPLE))
    assert "Android 14" in texte
    assert "2026-09-01" in texte
    assert formater_version({}) != ""


def test_erreurs_recentes():
    total, compteur, exemples = parse_logcat_erreurs(ERREURS_EXEMPLE)
    assert total == 3
    assert compteur["WifiService"] == 2
    assert len(exemples) == 3
    texte = formater_erreurs(total, compteur, exemples)
    assert "3 erreur" in texte
    assert "WifiService (2)" in texte
    assert "Aucune erreur" in formater_erreurs(0, compteur, [])


def test_reseau():
    connectivite = parse_connectivite(CONNECTIVITE_EXEMPLE)
    assert connectivite["connectes"] == ["wifi"]
    assert connectivite["defaut"] == "wifi"
    assert "wifi" in formater_reseau(connectivite, "0")
    assert "avion" in formater_reseau(connectivite, "1")
    assert "Aucun reseau" in formater_reseau({"connectes": [], "defaut": ""}, "0")


def test_wifi():
    infos = parse_wifi(WIFI_EXEMPLE)
    assert infos["ssid"] == "Maison-5G"
    assert infos["rssi"] == "-52"
    assert infos["debit"] == "433Mbps"
    texte = formater_wifi(infos)
    assert "Maison-5G" in texte
    assert "coupe" in formater_wifi({"active": False})
    assert "non connecte" in formater_wifi({"active": True, "ssid": ""})


def test_capteurs():
    donnees = parse_sensorservice(CAPTEURS_EXEMPLE)
    assert len(donnees["capteurs"]) == 3
    assert donnees["actifs"] == ["BMI160 Accelerometer"]
    texte = formater_capteurs(donnees)
    assert "3 capteur" in texte
    assert "Gyroscope" in texte
    assert "Aucun capteur" in formater_capteurs({"capteurs": [], "actifs": []})


def test_aucun_tiret_double_dans_les_textes():
    # Regle MUSE.md : jamais de "--" dans un texte affiche.
    liaisons = {"pret": True, "appareil_choisi": {"id": "X"}, "appareils": []}
    lignes_conso, drain_conso = parse_conso_batterystats(BATTERYSTATS_EXEMPLE)
    textes = [
        texte_detection(liaisons, GETPROP_EXEMPLE),
        formater_batterie(parse_dumpsys_battery(BATTERIE_EXEMPLE)),
        formater_conso(lignes_conso, {}, drain_conso, 10),
        formater_stockage(parse_df(DF_EXEMPLE)),
        formater_gros_fichiers(parse_gros_fichiers(LS_EXEMPLE), 100, "/sdcard"),
        formater_applis(parse_liste_packages(PAQUETS_EXEMPLE), "installees", 50),
        formater_crashs(parse_logcat_crash(CRASH_EXEMPLE)),
        formater_inutilisees([("com.x", 100)], 90, 30),
        formater_version(parse_getprop(GETPROP_EXEMPLE)),
        formater_erreurs(*parse_logcat_erreurs(ERREURS_EXEMPLE)),
        formater_reseau(parse_connectivite(CONNECTIVITE_EXEMPLE), "0"),
        formater_wifi(parse_wifi(WIFI_EXEMPLE)),
        formater_capteurs(parse_sensorservice(CAPTEURS_EXEMPLE)),
    ]
    for texte in textes:
        assert "--" not in texte, texte[:80]


def test_validation_parametres_sans_telephone():
    # Les controles d'entree repondent avant tout appel ADB.
    assert "Erreur" in appeler(lire_conso_batterie, limite=999)
    assert "Erreur" in appeler(lister_applis, quelles="nimporte")
    assert "Erreur" in appeler(lister_applis, limite=0)
    assert "Erreur" in appeler(lister_gros_fichiers, taille_min_mo=0)
    assert "Erreur" in appeler(lister_gros_fichiers, dossier="/system")
    assert "Erreur" in appeler(vider_cache_applis, espace_voulu_mo=10)
    assert "Erreur" in appeler(lister_applis_inutilisees, jours=2)
    assert "Erreur" in appeler(lire_erreurs_recentes, limite=5)
    assert "Erreur" in appeler(lire_crashs_recents, limite=0)


def test_appels_sans_telephone_renvoient_un_message():
    liaison = resumer_liaison()
    if liaison["pret"]:
        return
    attendus = {
        detecter_telephone: liaison["message"],
        lire_batterie: liaison["message"],
        lire_conso_batterie: liaison["message"],
        lire_stockage: liaison["message"],
        lister_applis: liaison["message"],
        lire_crashs_recents: liaison["message"],
        lister_applis_inutilisees: liaison["message"],
        lire_version_systeme: liaison["message"],
        lire_erreurs_recentes: liaison["message"],
        lire_etat_reseau: liaison["message"],
        lire_infos_wifi: liaison["message"],
        outil_tester_capteurs: liaison["message"],
    }
    for fonction, message in attendus.items():
        assert appeler(fonction) == message
    assert appeler(lister_gros_fichiers) == liaison["message"]
    assert appeler(vider_cache_applis) == liaison["message"]


def test_registre_palier_80_complet():
    assert len(OUTILS_PALIER_80) == 14
    for nom in OUTILS_PALIER_80:
        entree = REGISTRE_AFFICHAGE_OUTILS[nom]
        assert entree.get("label"), f"{nom} sans label"
        assert len(entree["label"]) <= 18, f"{nom} : label trop long"
        assert "--" not in entree["label"]
        assert entree.get("icone"), f"{nom} sans icone"
        assert entree.get("onglet") == "diagnostiquer", f"{nom} sans onglet"
        assert nom in CATEGORIES_OUTILS["telephone"]
    assert OUTILS_SENSIBLES == {"vider_cache_applis"}


def test_hotes_publics_autorises():
    assert _hote_de_valeur("") == ""
    assert _hote_de_valeur("https://class-tech-outils.onrender.com") == "class-tech-outils.onrender.com"
    assert _hote_de_valeur("class-tech-outils.onrender.com") == "class-tech-outils.onrender.com"
    ancien_render = os.environ.get("RENDER_EXTERNAL_URL")
    ancien_mcp = os.environ.get("MCP_HOTE_PUBLIC")
    try:
        os.environ.pop("RENDER_EXTERNAL_URL", None)
        os.environ.pop("MCP_HOTE_PUBLIC", None)
        assert hotes_publics_autorises() == []
        os.environ["RENDER_EXTERNAL_URL"] = "https://class-tech-outils.onrender.com"
        assert hotes_publics_autorises() == ["class-tech-outils.onrender.com"]
    finally:
        if ancien_render is None:
            os.environ.pop("RENDER_EXTERNAL_URL", None)
        else:
            os.environ["RENDER_EXTERNAL_URL"] = ancien_render
        if ancien_mcp is None:
            os.environ.pop("MCP_HOTE_PUBLIC", None)
        else:
            os.environ["MCP_HOTE_PUBLIC"] = ancien_mcp


def test_outils_80_enregistres_sur_le_serveur():
    outils = asyncio.run(mcp_diagnostic.list_tools())
    noms = {o.name for o in outils}
    for nom in OUTILS_PALIER_80:
        assert nom in noms, f"{nom} absent du serveur"
    assert "ping_serveur" in noms


if __name__ == "__main__":
    test_detection_getprop()
    test_batterie()
    test_conso_batterie()
    test_stockage_df()
    test_gros_fichiers()
    test_liste_applis()
    test_crashs()
    test_applis_inutilisees()
    test_version_systeme()
    test_erreurs_recentes()
    test_reseau()
    test_wifi()
    test_capteurs()
    test_aucun_tiret_double_dans_les_textes()
    test_validation_parametres_sans_telephone()
    test_appels_sans_telephone_renvoient_un_message()
    test_hotes_publics_autorises()
    test_registre_palier_80_complet()
    test_outils_80_enregistres_sur_le_serveur()
    print("OK : 14 outils du palier 80.")
