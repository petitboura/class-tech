"""Tests des 10 diagnostics profonds (palier 100 %, sans root).

Fonctions d'analyse testees sur des exemples realistes de sorties
Android, plus un test de cablage qui appelle les 10 outils avec un
telephone simule (doublures de preparer_acces et executer_adb_serie),
jamais d'ADB reel. Depuis backend/ :
`pytest tests/test_diagnostic_profond.py`
(ou `python tests/test_diagnostic_profond.py`).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.analyse_profonde import (  # noqa: E402
    analyser_carte_systeme,
    analyser_fluidite,
    analyser_historique_batterie,
    analyser_journaux,
    analyser_memoire_temps,
    analyser_reveils,
    analyser_saturation,
    analyser_temperatures,
    analyser_trafic_applis,
    analyser_verrous_veille,
    associer_uid_paquets,
)

ACCES_OK = {"adb": "adb", "serie": "T", "erreur": None, "note": None}

THERMAL_EXEMPLE = """Temperature{mValue=32.9, mType=3, mName=battery}
Temperature{mValue=41.2, mType=3, mName=cpu0}
Temperature{mValue=36.5, mType=3, mName=skin}
"""

BATTERYSTATS_EXEMPLE = """Statistics since last charge:
  System starts: 0
Time on battery: 5h 12m 30s
Computed drain: 812.4, actual drain: 790.2
Estimated power use (mAh):
    Uid u0a123 (com.reseaux.gourmand): 145.2
    Uid u0a456: 88.0
+wake_lock
+wake_lock
*alarm*
"""

PM_UID_EXEMPLE = """package:com.reseaux.gourmand uid:10123
package:com.photo.appareil uid:10456
"""

NETSTATS_EXEMPLE = """iface=wlan0 uid=10123 set=0 tag=0
  rxBytes=12345678 rxPackets=100 txBytes=1234567 txPackets=50
iface=wlan0 uid=1000 set=0 tag=0
  rxBytes=5000 rxPackets=10 txBytes=1000 txPackets=2
iface=wlan0 uid=10777 set=0 tag=0
  rxBytes=999 rxPackets=1 txBytes=1 txPackets=1
"""

GFXINFO_EXEMPLE = """Graphics info for pid 1234 [com.jeu.lourd]:
  Total frames rendered: 200
  Janky frames: 80 (40.0%)
Graphics info for pid 5678 [com.messages.simples]:
  Total frames rendered: 500
  Janky frames: 5 (1.0%)
"""

PSI_EXEMPLE = """some avg10=2.50 avg60=1.20 avg300=0.50 total=123456
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
"""

PSI_SATURE = """some avg10=45.00 avg60=30.00 avg300=10.00 total=999999
full avg10=5.00 avg60=2.00 avg300=1.00 total=1111
"""

ALARM_EXEMPLE = """com.reveils.spammeur
  12 wakeups
com.calme.horloge
  2 wakeups
"""

JOBS_EXEMPLE = """JOB #com.reveils.spammeur/u0a123: rubbish
JOB #com.sauvegarde.nuit/u0a200: rubbish
"""

CRASH_EXEMPLE = """Process: com.appli.fragile
Subject: crash
Process: com.appli.fragile
Subject: crash
Process: com.autre.buggee
Subject: crash
"""

SYSTEM_EXEMPLE = """10-28 12:00:01.000  1000  1000 E ActivityManager: ANR in com.lenteur
10-28 12:00:02.000  1000  1000 E ActivityManager: slow operation
10-28 12:00:03.000  1000  1000 E Netd: timeout
"""

DROPBOX_EXEMPLE = """system_app_crash (2026-10-28 12:00:01)
data_app_crash (2026-10-28 12:00:02)
system_app_crash (2026-10-28 11:00:00)
"""

GETPROP_EXEMPLE = """[ro.product.brand]: [samsung]
[ro.product.model]: [SM-A055F]
[ro.build.version.release]: [13]
[ro.build.version.sdk]: [33]
[ro.build.version.security_patch]: [2023-08-01]
"""

SERVICES_EXEMPLE = """Found 152 services:
0\tactivity: [android.app.IActivityManager]
1\tbattery: []
"""

LSHAL_EXEMPLE = """android.hardware.camera.provider@2.6::ICameraProvider/default
android.hardware.sensors@2.0::ISensors/default
"""

PROCSTATS_EXEMPLE = """  * com.memoire.gourmande / u0a123:
    PSS: min=400000 avg=600000 max=800000
  * com.petite.utilitaire / u0a200:
    PSS: min=50000 avg=80000 max=100000
"""

POWER_EXEMPLE = """mWakefulness=Awake
Wake Locks: size=2
PARTIAL_WAKE_LOCK 'MusiqueEnFond' (uid=10123 pid=500)
PARTIAL_WAKE_LOCK 'Telechargement' (uid=10456 pid=600)
"""


def test_temperatures():
    chaud = analyser_temperatures("Temperature{mValue=47.0, mType=3, mName=cpu0}\n")
    assert "47,0" in chaud["resume"]
    assert "ombre" in chaud["resume"]
    tiede = analyser_temperatures(THERMAL_EXEMPLE)
    assert "battery (32,9" in tiede["resume"]
    assert "acceptables" in tiede["resume"]
    dixiemes = analyser_temperatures("Temperature{mValue=320, mType=3, mName=x}\n")
    assert "32,0" in dixiemes["resume"]
    assert "illisible" in analyser_temperatures("")["resume"]
    assert "illisible" in analyser_temperatures("pas de sondes\n")["resume"]


def test_historique_batterie():
    plein = analyser_historique_batterie(BATTERYSTATS_EXEMPLE)
    assert "5h 12m 30s" in plein["resume"]
    assert "812,4" in plein["resume"]
    assert "com.reseaux.gourmand" in plein["resume"]
    assert "3 réveils" in plein["resume"]
    assert plein["reveils_verrous"] == 2
    assert plein["reveils_alarmes"] == 1
    assert "illisible" in analyser_historique_batterie("")["resume"]


def test_trafic_applis():
    table = associer_uid_paquets(PM_UID_EXEMPLE)
    assert table == {"10123": ["com.reseaux.gourmand"], "10456": ["com.photo.appareil"]}
    plein = analyser_trafic_applis(NETSTATS_EXEMPLE, table)
    assert "com.reseaux.gourmand" in plein["resume"]
    assert "système Android" in plein["resume"]
    assert "uid 10777" in plein["resume"]
    assert plein["total_octets"] == 12345678 + 1234567 + 5000 + 1000 + 999 + 1
    assert "illisible" in analyser_trafic_applis("")["resume"]


def test_fluidite():
    saccade = analyser_fluidite(GFXINFO_EXEMPLE)
    assert "com.jeu.lourd" in saccade["resume"]
    assert "peine" in saccade["resume"]
    fluide = analyser_fluidite(
        "Graphics info for pid 1 [com.calme]:\n"
        "Total frames rendered: 100\nJanky frames: 2 (2.0%)\n"
    )
    assert "fluide" in fluide["resume"]
    assert "ouvrez une appli" in analyser_fluidite("")["resume"]


def test_saturation():
    calme = analyser_saturation(PSI_EXEMPLE, PSI_EXEMPLE, PSI_EXEMPLE)
    assert "respire" in calme["resume"]
    sature = analyser_saturation(PSI_SATURE, PSI_EXEMPLE, PSI_EXEMPLE)
    assert "souffle" in sature["resume"]
    assert "illisible" in analyser_saturation("", "", "")["resume"]


def test_reveils():
    plein = analyser_reveils(ALARM_EXEMPLE, JOBS_EXEMPLE)
    assert "14 réveils" in plein["resume"]
    assert "com.reveils.spammeur (12 réveils)" in plein["resume"]
    assert "2 tâches planifiées" in plein["resume"]
    assert "illisible" in analyser_reveils("", "")["resume"]


def test_journaux():
    plein = analyser_journaux(CRASH_EXEMPLE, SYSTEM_EXEMPLE, DROPBOX_EXEMPLE)
    assert "com.appli.fragile (2)" in plein["resume"]
    assert "ActivityManager (2)" in plein["resume"]
    assert "3 rapports conservés" in plein["resume"]
    assert "illisible" in analyser_journaux("", "", "")["resume"]


def test_carte_systeme():
    plein = analyser_carte_systeme(GETPROP_EXEMPLE, SERVICES_EXEMPLE, LSHAL_EXEMPLE)
    assert "samsung SM-A055F" in plein["resume"]
    assert "Android 13" in plein["resume"]
    assert "152 services" in plein["resume"]
    assert "2 composants" in plein["resume"]
    assert "illisible" in analyser_carte_systeme("", "", "")["resume"]


def test_memoire_temps():
    plein = analyser_memoire_temps(PROCSTATS_EXEMPLE)
    assert "com.memoire.gourmande" in plein["resume"]
    assert "beaucoup" in plein["resume"]
    assert plein["applis"][0]["moyenne_mo"] == round(600000 / 1024)
    assert "illisible" in analyser_memoire_temps("")["resume"]


def test_verrous_veille():
    plein = analyser_verrous_veille(POWER_EXEMPLE)
    assert "2 verrous" in plein["resume"]
    assert "MusiqueEnFond" in plein["resume"]
    libre = analyser_verrous_veille("mWakefulness=Asleep\nWake Locks: size=0\n")
    assert "peut dormir" in libre["resume"]
    assert "illisible" in analyser_verrous_veille("vide\n")["resume"]


OUTILS_PROFONDS = [
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
]


def _simuler_adb_vide(monkeypatch):
    """Téléphone qui ne partage rien : chaque outil doit le dire."""
    def interdit(*args, **kwargs):
        raise AssertionError("appel adb reel interdit en test")

    monkeypatch.setattr("core.pont_adb.executer_adb", interdit)
    monkeypatch.setattr("core.pont_adb.executer_adb_serie", interdit)
    monkeypatch.setattr("core.pont_adb.executer_shell", interdit)
    monkeypatch.setattr(
        "core.outils_profondeur_100.preparer_acces", lambda: dict(ACCES_OK)
    )
    monkeypatch.setattr(
        "core.outils_profondeur_100.executer_adb_serie",
        lambda adb, serie, morceaux, delai=None: (True, "", ""),
    )


def test_outils_profonds_cablage(monkeypatch):
    import core.outils_profondeur_100 as profondeur
    _simuler_adb_vide(monkeypatch)
    for nom in OUTILS_PROFONDS:
        texte = getattr(profondeur, nom)()
        assert isinstance(texte, str) and texte, nom
        assert "illis" in texte, nom


if __name__ == "__main__":
    import importlib

    class Rustine:
        def setattr(self, cible, valeur):
            module, _, attr = cible.rpartition(".")
            setattr(importlib.import_module(module), attr, valeur)

    rustine = Rustine()
    test_temperatures()
    test_historique_batterie()
    test_trafic_applis()
    test_fluidite()
    test_saturation()
    test_reveils()
    test_journaux()
    test_carte_systeme()
    test_memoire_temps()
    test_verrous_veille()
    test_outils_profonds_cablage(rustine)
    print("OK : diagnostics profonds.")
