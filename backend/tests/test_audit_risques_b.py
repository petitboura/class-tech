"""Tests de l'audit risques B (palier root, 28/10/2026).

Couvre chaque correction de l'audit : fonctions pures sur des
sorties Android realistes figees, outils appeles avec le pont moque
(_echange : AUCUN appel ADB reel, aucun telephone touche), et
garde-fou d'exposition (sous-processus : sans l'interrupteur, les
outils root n'apparaissent pas sur le serveur).

Depuis backend/ : `pytest tests/test_audit_risques_b.py`
(ou `python tests/test_audit_risques_b.py`).
"""

import contextlib
import importlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Interrupteur allume pour cette suite (les outils root refuses sans
# lui sont testes en le retirant temporairement, voir plus bas).
os.environ["CLASSTECH_OUTILS_ROOT"] = "1"

from core import (  # noqa: E402
    outils_root_acces,
    outils_root_batterie,
    outils_root_corrections,
    outils_root_firmware,
    outils_root_partitions,
    outils_root_processus,
    outils_root_systeme,
)
from core import pont_root  # noqa: E402


@contextlib.contextmanager
def _echange(module_nom, attr, bidon):
    """Remplace module.attr par bidon, restaure apres (pont moque)."""
    module = importlib.import_module(module_nom)
    ancien = getattr(module, attr)
    setattr(module, attr, bidon)
    try:
        yield
    finally:
        setattr(module, attr, ancien)


@contextlib.contextmanager
def _sans_flag_root():
    """Retire CLASSTECH_OUTILS_ROOT, restaure apres."""
    ancien = os.environ.pop("CLASSTECH_OUTILS_ROOT", None)
    try:
        yield
    finally:
        if ancien is not None:
            os.environ["CLASSTECH_OUTILS_ROOT"] = ancien


def _ok(sortie):
    return {"ok": True, "sortie": sortie, "erreur": ""}


def _rate(erreur):
    return {"ok": False, "sortie": "", "erreur": erreur}


# --- root_verifier_acces : gestionnaire par noms entiers ---

def test_gestionnaire_mots_entiers():
    devine = outils_root_acces.deviner_gestionnaire_root
    assert devine("magisk\nmodules\n") == "Magisk probable"
    assert devine("ksu\nmodules\n") == "KernelSU probable"
    assert devine("su\n") == "binaire su present, gestionnaire inconnu"
    assert devine("modules\nasus_config\n") == "gestionnaire inconnu"
    assert devine("nomagisk_hack\n") == "gestionnaire inconnu"
    assert devine("") == "gestionnaire inconnu"


# --- root_lire_infos_root : modules sans decalage ---

def test_modules_magisk_sans_nom_sans_decalage():
    dossiers, modules = outils_root_acces.parse_modules_magisk(
        "mod_a\nmod_b\nmod_c\n",
        "id=mod_a\nname=Module A\nid=mod_b\nid=mod_c\nname=Module C\n",
    )
    assert dossiers == ["mod_a", "mod_b", "mod_c"]
    assert modules == {
        "mod_a": "Module A", "mod_b": "mod_b", "mod_c": "Module C",
    }


def test_modules_magisk_nom_avant_id_ignore():
    _d, modules = outils_root_acces.parse_modules_magisk(
        "", "name=Orphelin\nid=seul\nname=Seul module\n",
    )
    assert modules == {"seul": "Seul module"}


# --- Fichiers et dossiers a secrets refuses ---

def test_chemin_sensible_refuse():
    refuse = outils_root_systeme.chemin_sensible_refuse
    assert refuse("/data/misc/wifi/wpa_supplicant.conf")
    assert refuse("/data/misc/wifi/WifiConfigStore.xml")
    assert refuse("/data/misc/keystore/user_0/1000_TEST")
    assert refuse("/data/misc/keychain/cacerts/abc.0")
    assert refuse("/data/system/users/0/accounts_ce.db")
    assert refuse("/data/system/gatekeeper.password.key")
    assert not refuse("/system/build.prop")
    assert not refuse("/data/adb/modules")
    assert not refuse("/data/misc/netstats")
    assert not refuse("")
    assert not refuse(None)


def test_lire_fichier_sensible_refuse_sans_adb():
    # Refus avant tout appel : aucun moquage necessaire, aucun ADB.
    reponse = outils_root_systeme.root_lire_fichier_systeme(
        "/data/misc/wifi/WifiConfigStore.xml")
    assert "secrets" in reponse
    reponse = outils_root_systeme.root_lister_fichiers_systeme(
        "/data/misc/keystore")
    assert "secrets" in reponse


def test_lire_fichier_limite_invalide_sans_adb():
    reponse = outils_root_systeme.root_lire_fichier_systeme(
        "/system/build.prop", 999)
    assert "limite invalide" in reponse


# --- root_lire_fichier_systeme : extrait honnete ---

def test_fichier_systeme_mentions_extrait():
    formate = outils_root_systeme.formater_fichier_systeme
    plein = formate("/f", "l1\nl2", False, lignes_coupees=True)
    assert "premieres lignes" in plein
    incertain = formate("/f", "l1", False, taille_inconnue=True)
    assert "inconnue" in incertain
    assert "suite non affichee" in formate("/f", "l1", True)


# --- root_lire_erreurs_noyau : total minimum ---

def test_erreurs_noyau_au_moins():
    formate = outils_root_systeme.formater_erreurs_noyau
    pleines = [f"[t] erreur {i}" for i in range(100)]
    assert "Au moins 100" in formate(pleines, 100)
    partiel = formate(["[t] erreur 1", "[t] erreur 2"], 100)
    assert "2 ligne(s)" in partiel and "Au moins" not in partiel


# --- root_lire_paniques_passees : absents ou vides ---

def test_paniques_absents_ou_vides():
    formate = outils_root_systeme.formater_paniques
    assert "absents" in formate([], 0)
    assert "vides" in formate([], 3)
    assert formate([], None) == "Aucune trace de plantage noyau precedent."
    traces = [("/proc/last_kmsg", "Kernel panic")]
    assert "1 trace" in formate(traces, 1)


# --- root_lire_partitions : df coupe, by-name, cmdline ---

DF_COUPE = (
    "Filesystem           1K-blocks      Used Available Use% Mounted on\n"
    "/dev/block/dm-5\n"
    "                      11533852   8234560   3299292  72% /data\n"
    "tmpfs                  2867268         0   2867268   0% /dev\n"
)


def test_parse_df_lignes_coupees():
    df = outils_root_partitions.parse_df(DF_COUPE)
    assert len(df) == 2
    assert df[0][0] == "/dev/block/dm-5" and df[0][5] == "/data"
    assert df[1][5] == "/dev"


def test_byname_tronque_annonce_minimum():
    byname = outils_root_partitions.parse_byname(
        "\n".join(
            f"lrwxrwxrwx 1 root root 16 2026-01-01 00:00 p{i:02d} -> ../../sda{i}"
            for i in range(60)
        )
    )
    assert len(byname) == 40
    df = [("/dev/x", "100G", "60G", "40G", "60%", "/data")]
    texte = outils_root_partitions.formater_partitions(df, {}, byname)
    assert "Au moins 40" in texte and "tronquee" in texte
    court = outils_root_partitions.formater_partitions(
        df, {}, [("boot", "x"), ("system", "y")])
    assert "2 partition(s)" in court


def test_integrite_cmdline_cassee_sans_crash():
    formate = outils_root_partitions.formater_integrite
    assert "illisible" in formate({}, "rcu_expedited=1 androidboot.verifiedbootstate=", {})
    texte = formate({}, "a=1 androidboot.verifiedbootstate=green", {})
    assert "verifie : oui" in texte


# --- root_lire_batterie_brute : status et plausibilite ---

VALEURS_BATTERIE = {
    "voltage_now": "4100000", "current_now": "-500000", "temp": "320",
    "charge_counter": "3000000", "charge_full": "4000000",
    "charge_full_design": "5000000", "cycle_count": "350",
    "capacity": "75", "health": "Good", "technology": "Li-ion",
}


def test_batterie_sens_par_status():
    formate = outils_root_batterie.formater_batterie_brute
    en_charge = dict(VALEURS_BATTERIE, status="Charging")
    texte = formate(en_charge)
    assert "500 mA (charge)" in texte and "probable" not in texte
    sans_status = formate(VALEURS_BATTERIE)
    assert "500 mA (decharge probable)" in sans_status


def test_batterie_unites_inhabituelles_brutes():
    formate = outils_root_batterie.formater_batterie_brute
    chaud = dict(VALEURS_BATTERIE, temp="32000")
    assert "temperature brute 32000" in formate(chaud)
    millivolts = dict(VALEURS_BATTERIE, voltage_now="4100")
    assert "tension brute 4100" in formate(millivolts)
    assert "32.0 C" in formate(VALEURS_BATTERIE)


# --- root_lire_temperatures : zones sans mesure comptees ---

TYPES_THERM = (
    "/sys/class/thermal/thermal_zone0/type:battery\n"
    "/sys/class/thermal/thermal_zone1/type:cpu\n"
    "/sys/class/thermal/thermal_zone2/type:gpu\n"
)
TEMPS_THERM = (
    "/sys/class/thermal/thermal_zone0/temp:32000\n"
    "/sys/class/thermal/thermal_zone1/temp:999999999\n"
)


def test_thermal_zones_sans_mesure():
    zones = outils_root_batterie.parse_thermal(TYPES_THERM, TEMPS_THERM)
    assert len(zones) == 1 and zones[0][1] == "battery"
    compte = outils_root_batterie.compter_zones_sans_mesure(TYPES_THERM, zones)
    assert compte == 2
    texte = outils_root_batterie.formater_temperatures(zones, 10, compte)
    assert "battery 32.0 C" in texte
    assert "2 capteur(s) sans mesure" in texte
    assert "sans mesure" in outils_root_batterie.formater_temperatures([], 10, 3)


# --- root_valider_slot_demarre : slot normalise ---

def test_normaliser_slot():
    normalise = outils_root_firmware.normaliser_slot
    assert normalise("[_a]\n") == "_a"
    assert normalise("_b") == "_b"
    assert normalise("[_a]\n[_b]") == "_a"
    assert normalise("") == ""
    assert normalise("coin") == ""
    assert normalise(None) == ""


def test_parse_slot_bootctl():
    parse = outils_root_firmware.parse_slot_bootctl
    assert parse("0\n") == "0"
    assert parse("1") == "1"
    assert parse("") is None
    assert parse("slot inconnu") is None
    assert parse(None) is None


def test_validation_slot_mention_definitive():
    texte = outils_root_firmware.formater_validation_slot("_a", True)
    assert "marque comme bon" in texte and "definitive" in texte


# --- root_lister_processus : format inattendu ---

def test_processus_format_inattendu():
    formate = outils_root_processus.formater_processus
    assert "inattendu" in formate([], 10, "Tasks: 5 total\nCPU: 3%\n")
    assert "illisibles" in formate([], 10, "")
    douze = [(str(i), 50.0 - i, "10M", "root", f"proc{i}") for i in range(12)]
    assert "(10 premiers sur 12.)" in formate(douze, 10)
    assert "proc0 (50 % CPU)" in formate(douze, 10)


# --- root_lire_wakelocks : troncature annoncee ---

def test_wakelocks_tronques():
    formate = outils_root_processus.formater_wakelocks
    noms = [f"verrou{i}" for i in range(12)]
    assert "(10 premiers affiches.)" in formate(12, noms, 10)
    assert "affiches" not in formate(2, ["a", "b"])


# --- root_nettoyer_fichiers_crash : commandes separees ---

def test_commande_nettoyage_crash_separee():
    commande = outils_root_corrections.commande_nettoyage_crash()
    morceaux = [m.strip() for m in commande.split(";")]
    assert len(morceaux) == 3
    assert commande.count("rm -rf") == 3
    for morceau, dossier in zip(morceaux, outils_root_corrections.DOSSIERS_CRASH):
        assert morceau == f"rm -rf {dossier}/*"


# --- root_forcer_trim : echecs partiels affiches ---

def test_formater_trim_echecs():
    formate = outils_root_corrections.formater_trim
    texte = formate([("/data", 1048576)], True, echecs=(("/cache", "absent"),))
    assert "optimise" in texte
    assert "Non trimme : /cache (absent)" in texte
    assert "refusee" in formate([], False, "/data (x), /cache (y)")


# --- root_redemarrer : coupure distinguee du refus ---

def test_coupure_liaison_probable():
    coupe = outils_root_corrections.coupure_liaison_probable
    assert coupe("error: closed")
    assert coupe("error: device offline")
    assert coupe("error: device not found")
    assert coupe("delai depasse, le telephone n'a pas repondu a temps.")
    assert not coupe("Permission denied")
    assert not coupe("")
    assert not coupe(None)


def test_formater_redemarrage_coupure():
    formate = outils_root_corrections.formater_redemarrage
    texte = formate("normal", False, "error: closed")
    assert "envoye" in texte and "Verifie" in texte
    assert "recovery" in formate("recovery", False, "error: closed")
    assert "refuse" in formate("normal", False, "Permission denied")


# --- Interrupteur CLASSTECH_OUTILS_ROOT ---

def test_outils_root_actifs():
    assert pont_root.outils_root_actifs() is True
    with _sans_flag_root():
        assert pont_root.outils_root_actifs() is False
    os.environ["CLASSTECH_OUTILS_ROOT"] = "0"
    try:
        assert pont_root.outils_root_actifs() is False
    finally:
        os.environ["CLASSTECH_OUTILS_ROOT"] = "1"
    assert "--" not in pont_root.message_root_desactive()


def test_preparer_root_refuse_sans_adb_si_eteint():
    def leve():
        raise AssertionError("ADB ne doit pas etre touche")

    with _sans_flag_root():
        with _echange("core.pont_root", "preparer_appel", leve):
            appareil, message = pont_root.preparer_root()
    assert appareil is None and "desactives" in message


def test_root_verifier_acces_refuse_si_eteint():
    with _sans_flag_root():
        reponse = outils_root_acces.root_verifier_acces()
    assert "desactives" in reponse


# --- Outils appeles avec le pont moque (aucun ADB reel) ---

def test_root_verifier_acces_pas_de_root():
    with _echange("core.outils_root_acces", "preparer_appel",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_acces", "verifier_root",
                      lambda _id: {"root": False, "uid": 2000,
                                  "detail": "uid=2000(shell)"}):
            reponse = outils_root_acces.root_verifier_acces()
    assert "indisponible" in reponse


def test_root_nettoyer_crash_envoie_trois_rm():
    envoyees = []

    def faux_executer(commande, _appareil, delai=None):
        envoyees.append(commande)
        if commande.startswith("du "):
            return _ok("12M\t/data/tombstones\n8.0K\t/data/system/dropbox\n"
                       "4.0K\t/data/anr\n")
        return _ok("")

    with _echange("core.outils_root_corrections", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_corrections", "executer_root",
                      faux_executer):
            reponse = outils_root_corrections.root_nettoyer_fichiers_crash()
    assert envoyees[1] == outils_root_corrections.commande_nettoyage_crash()
    assert ";" in envoyees[1]
    assert "supprimes" in reponse and "12M" in reponse


def test_root_vider_dalvik_absent_nefface_rien():
    envoyees = []

    def faux_executer(commande, _appareil, delai=None):
        envoyees.append(commande)
        return _rate("du: /data/dalvik-cache: No such file or directory")

    with _echange("core.outils_root_corrections", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_corrections", "executer_root",
                      faux_executer):
            reponse = outils_root_corrections.root_vider_cache_dalvik()
    assert envoyees == ["du -sh /data/dalvik-cache"]
    assert "rien supprime" in reponse


def test_root_forcer_trim_partiel():
    def faux_executer(commande, _appareil, delai=None):
        if "/data" in commande:
            return _ok("/data: 1048576 bytes trimmed\n")
        return _rate("fstrim: /cache: No such file or directory")

    with _echange("core.outils_root_corrections", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_corrections", "executer_root",
                      faux_executer):
            reponse = outils_root_corrections.root_forcer_trim()
    assert "optimise" in reponse and "Non trimme : /cache" in reponse


def test_root_forcer_trim_tout_rate():
    with _echange("core.outils_root_corrections", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_corrections", "executer_root",
                      lambda c, a, delai=None: _rate("refuse")):
            reponse = outils_root_corrections.root_forcer_trim()
    assert "refusee" in reponse


def test_root_redemarrer_coupure_et_mode_inconnu():
    assert "mode inconnu" in outils_root_corrections.root_redemarrer("usine")
    with _echange("core.outils_root_corrections", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_corrections", "executer_root",
                      lambda c, a, delai=None: _rate("error: closed")):
            reponse = outils_root_corrections.root_redemarrer("recovery")
    assert "envoye" in reponse and "recovery" in reponse


def test_root_valider_slot_deja_valide_necrit_rien():
    envoyees = []

    def faux_executer(commande, _appareil, delai=None):
        envoyees.append(commande)
        if "get-current-slot" in commande:
            return _ok("0\n")
        return _ok("")

    with _echange("core.outils_root_firmware", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_firmware", "executer_shell",
                      lambda c, a: _ok("[_a]\n")):
            with _echange("core.outils_root_firmware", "executer_root",
                          faux_executer):
                reponse = outils_root_firmware.root_valider_slot_demarre()
    assert "deja marque" in reponse
    assert not any("mark-boot-successful" in c for c in envoyees)


def test_root_valider_slot_illisible_ou_absent():
    envoyees = []
    with _echange("core.outils_root_firmware", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_firmware", "executer_shell",
                      lambda c, a: _ok("coin\n")):
            with _echange("core.outils_root_firmware", "executer_root",
                          lambda c, a, delai=None: envoyees.append(c) or _ok("")):
                assert "illisible" in outils_root_firmware.root_valider_slot_demarre()
        assert envoyees == []
        with _echange("core.outils_root_firmware", "executer_shell",
                      lambda c, a: _ok("\n")):
            with _echange("core.outils_root_firmware", "executer_root",
                          lambda c, a, delai=None: envoyees.append(c) or _ok("")):
                assert "rien a valider" in outils_root_firmware.root_valider_slot_demarre()
        assert envoyees == []


def test_root_reinitialiser_stats_batterie():
    with _echange("core.outils_root_batterie", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_batterie", "executer_root",
                      lambda c, a, delai=None: _ok("")):
            assert "remises a zero" in outils_root_batterie.root_reinitialiser_stats_batterie()
        with _echange("core.outils_root_batterie", "executer_root",
                      lambda c, a, delai=None: _rate("refuse")):
            assert "non remis a zero" in outils_root_batterie.root_reinitialiser_stats_batterie()


def test_root_lister_processus_format_inattendu():
    with _echange("core.outils_root_processus", "preparer_root",
                  lambda: ("ABC", None)):
        with _echange("core.outils_root_processus", "executer_root",
                      lambda c, a, delai=None: _ok("bonjour\n")):
            reponse = outils_root_processus.root_lister_processus()
    assert "inattendu" in reponse


# --- Garde-fou d'exposition (sous-processus, aucun ADB) ---

_CODE_LISTE_OUTILS = (
    "import asyncio, os; "
    "from core.serveur_mcp_diagnostic import mcp_diagnostic; "
    "noms = sorted(o.name for o in asyncio.run(mcp_diagnostic.list_tools())); "
    "print(len(noms)); "
    "[print(n) for n in noms]"
)

_RACINE_BACKEND = os.path.join(os.path.dirname(__file__), "..")

_NOMS_ROOT_ATTENDUS = (
    "root_verifier_acces", "root_lire_infos_root",
    "root_lister_fichiers_systeme", "root_lire_fichier_systeme",
    "root_lire_erreurs_noyau", "root_lire_paniques_passees",
    "root_lire_partitions", "root_verifier_integrite",
    "root_lire_batterie_brute", "root_lire_temperatures",
    "root_reinitialiser_stats_batterie", "root_lire_firmware",
    "root_valider_slot_demarre", "root_lister_processus",
    "root_lire_wakelocks", "root_nettoyer_fichiers_crash",
    "root_vider_cache_dalvik", "root_forcer_trim", "root_redemarrer",
)


def _outils_exposes(avec_flag):
    env = {k: v for k, v in os.environ.items()
           if k != "CLASSTECH_OUTILS_ROOT"}
    if avec_flag:
        env["CLASSTECH_OUTILS_ROOT"] = "1"
    termine = subprocess.run(
        [sys.executable, "-c", _CODE_LISTE_OUTILS],
        cwd=_RACINE_BACKEND, env=env, capture_output=True, text=True,
        timeout=180,
    )
    assert termine.returncode == 0, termine.stderr[-500:]
    lignes = termine.stdout.splitlines()
    return int(lignes[0]), lignes[1:]


def test_outils_root_absents_par_defaut():
    total, noms = _outils_exposes(avec_flag=False)
    assert total == 31
    assert not any(n.startswith("root_") for n in noms)


def test_outils_root_presents_si_flag():
    total, noms = _outils_exposes(avec_flag=True)
    assert total == 50
    for nom in _NOMS_ROOT_ATTENDUS:
        assert nom in noms


if __name__ == "__main__":
    test_gestionnaire_mots_entiers()
    test_modules_magisk_sans_nom_sans_decalage()
    test_modules_magisk_nom_avant_id_ignore()
    test_chemin_sensible_refuse()
    test_lire_fichier_sensible_refuse_sans_adb()
    test_lire_fichier_limite_invalide_sans_adb()
    test_fichier_systeme_mentions_extrait()
    test_erreurs_noyau_au_moins()
    test_paniques_absents_ou_vides()
    test_parse_df_lignes_coupees()
    test_byname_tronque_annonce_minimum()
    test_integrite_cmdline_cassee_sans_crash()
    test_batterie_sens_par_status()
    test_batterie_unites_inhabituelles_brutes()
    test_thermal_zones_sans_mesure()
    test_normaliser_slot()
    test_parse_slot_bootctl()
    test_validation_slot_mention_definitive()
    test_processus_format_inattendu()
    test_wakelocks_tronques()
    test_commande_nettoyage_crash_separee()
    test_formater_trim_echecs()
    test_coupure_liaison_probable()
    test_formater_redemarrage_coupure()
    test_outils_root_actifs()
    test_preparer_root_refuse_sans_adb_si_eteint()
    test_root_verifier_acces_refuse_si_eteint()
    test_root_verifier_acces_pas_de_root()
    test_root_nettoyer_crash_envoie_trois_rm()
    test_root_vider_dalvik_absent_nefface_rien()
    test_root_forcer_trim_partiel()
    test_root_forcer_trim_tout_rate()
    test_root_redemarrer_coupure_et_mode_inconnu()
    test_root_valider_slot_deja_valide_necrit_rien()
    test_root_valider_slot_illisible_ou_absent()
    test_root_reinitialiser_stats_batterie()
    test_root_lister_processus_format_inattendu()
    test_outils_root_absents_par_defaut()
    test_outils_root_presents_si_flag()
    print("OK : audit risques B.")
