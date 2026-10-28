"""Tests des 5 outils sensibles non-root (audit A).

vider_cache_applis, tester_haut_parleur, tester_vibreur,
tester_camera, revoquer_permission : chaque fonction outil est
testee avec un telephone simule (doublures de preparer_acces,
executer_adb_serie, preparer_appel, executer_shell), jamais d'ADB
reel. Demande mcp installe (import des modules d'outils).
Depuis backend/ : `pytest tests/test_audit_a_sensibles.py`
(ou `python tests/test_audit_a_sensibles.py`).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ACCES_OK = {"adb": "adb", "serie": "T", "erreur": None, "note": None}


def _interdire_adb_reel(monkeypatch):
    """Rend tout appel ADB reel impossible en test (audit A)."""
    def interdit(*args, **kwargs):
        raise AssertionError("appel adb reel interdit en test")

    monkeypatch.setattr("core.pont_adb.executer_adb", interdit)
    monkeypatch.setattr("core.pont_adb.executer_adb_serie", interdit)
    monkeypatch.setattr("core.pont_adb.executer_shell", interdit)


def _simuler_adb(monkeypatch, nom_module, reponses):
    """Doublure de executer_adb_serie avec sorties figees.

    reponses : [(fragment, (ok, sortie, erreur))], le premier
    fragment contenu dans la commande gagne. Une reponse peut etre
    une liste : chaque appel consomme la suivante (utile pour deux
    lectures identiques, comme df avant/apres). Renvoie les
    commandes recues, dans l'ordre.
    """
    commandes = []

    def faux_executer(adb, serie, morceaux, delai=None):
        commande = " ".join(morceaux)
        commandes.append(commande)
        for fragment, reponse in reponses:
            if fragment in commande:
                if isinstance(reponse, list):
                    return reponse.pop(0)
                return reponse
        return (False, "", "commande non simulee")

    _interdire_adb_reel(monkeypatch)
    monkeypatch.setattr(nom_module + ".preparer_acces", lambda: dict(ACCES_OK))
    monkeypatch.setattr(nom_module + ".executer_adb_serie", faux_executer)
    return commandes


def _simuler_appel(monkeypatch, nom_module, reponses):
    """Doublure de executer_shell (palier 80), memes conventions."""
    commandes = []

    def faux_executer(commande, appareil_id, delai=None):
        commandes.append(commande)
        for fragment, reponse in reponses:
            if fragment in commande:
                if isinstance(reponse, list):
                    return dict(reponse.pop(0))
                return dict(reponse)
        return {"ok": False, "sortie": "", "erreur": "commande non simulee"}

    _interdire_adb_reel(monkeypatch)
    monkeypatch.setattr(nom_module + ".preparer_appel", lambda: ("T", None))
    monkeypatch.setattr(nom_module + ".executer_shell", faux_executer)
    return commandes


DF_AVANT = (
    "Filesystem 1K-blocks Used Available Use% Mounted on\n"
    "/dev/block/dm-0 100000000 60000000 40000000 60% /data\n"
)
DF_APRES = (
    "Filesystem 1K-blocks Used Available Use% Mounted on\n"
    "/dev/block/dm-0 100000000 59500000 40500000 59% /data\n"
)


def test_vider_cache_mesure_avant_apres(monkeypatch):
    import core.outils_telephone_stockage as stockage
    commandes = _simuler_appel(monkeypatch, "core.outils_telephone_stockage", [
        ("df /data", [
            {"ok": True, "sortie": DF_AVANT, "erreur": ""},
            {"ok": True, "sortie": DF_APRES, "erreur": ""},
        ]),
        ("pm trim-caches", {"ok": True, "sortie": "", "erreur": ""}),
    ])
    texte = stockage.vider_cache_applis(500)
    assert "488 Mo liberes" in texte
    assert any(c.startswith("pm trim-caches 524288000") for c in commandes)


def test_vider_cache_refus_et_invalide(monkeypatch):
    import core.outils_telephone_stockage as stockage
    _simuler_appel(monkeypatch, "core.outils_telephone_stockage", [
        ("df /data", {"ok": True, "sortie": DF_AVANT, "erreur": ""}),
        ("pm trim-caches", {"ok": False, "sortie": "", "erreur": "refuse"}),
    ])
    assert "Nettoyage refuse" in stockage.vider_cache_applis()
    assert "taille invalide" in stockage.vider_cache_applis("beaucoup")
    assert "taille invalide" in stockage.vider_cache_applis(50)


AUDIO_FIXTURE = (
    "STREAM_MUSIC: Muted: false Max: 15 (speaker): 10\n"
    "MODE_NORMAL\n"
)


def test_haut_parleur_bip_et_nettoyage(monkeypatch):
    import core.outils_materiel_100 as materiel
    commandes = _simuler_adb(monkeypatch, "core.outils_materiel_100", [
        ("dumpsys audio", (True, AUDIO_FIXTURE, "")),
        ("push", (True, "1 file pushed", "")),
        ("am start", (True, "Starting: Intent", "")),
        ("rm -f", (True, "", "")),
    ])
    texte = materiel.tester_haut_parleur()
    assert "lancé un bip" in texte
    assert "avez-vous entendu" in texte.lower()
    assert any("rm -f /sdcard/classtech_bip.wav" in c for c in commandes)


def test_haut_parleur_push_impossible(monkeypatch):
    import core.outils_materiel_100 as materiel
    _simuler_adb(monkeypatch, "core.outils_materiel_100", [
        ("dumpsys audio", (True, AUDIO_FIXTURE, "")),
        ("push", (False, "", "no space")),
        ("rm -f", (True, "", "")),
    ])
    assert "pas pu jouer le bip" in materiel.tester_haut_parleur()


def test_vibreur(monkeypatch):
    import core.outils_materiel_100 as materiel
    _simuler_adb(monkeypatch, "core.outils_materiel_100", [
        ("dumpsys vibrator", (True, "VibratorService: capabilities=1\n", "")),
        ("vibrate", (True, "", "")),
    ])
    assert "une seconde" in materiel.tester_vibreur()
    _simuler_adb(monkeypatch, "core.outils_materiel_100", [
        ("dumpsys vibrator", (True, "VibratorService: capabilities=1\n", "")),
        ("vibrate", (False, "", "Unknown command: vibrate")),
    ])
    assert "proche" in materiel.tester_vibreur()


CAMERA_FIXTURE = (
    "Number of camera devices: 2\n"
    "Camera device 0 facing: back\n"
    "Camera device 1 facing: front\n"
)


def test_camera(monkeypatch):
    import core.outils_materiel_100 as materiel
    _simuler_adb(monkeypatch, "core.outils_materiel_100", [
        ("dumpsys media.camera", (True, CAMERA_FIXTURE, "")),
        ("am start", (True, "Starting: Intent", "")),
    ])
    assert "2 caméras" in materiel.tester_camera()
    assert "prenez une photo" in materiel.tester_camera().lower()
    assert "ouvert l'appli photo" in materiel.tester_camera(ouvrir_appli=True)


DUMPSYS_REVOKE_CONFIRME = (
    "Package [com.exemple.appli] (abc):\n"
    "    runtime permissions:\n"
    "      android.permission.CAMERA: granted=false\n"
)
DUMPSYS_REVOKE_RATE = (
    "Package [com.exemple.appli] (abc):\n"
    "    runtime permissions:\n"
    "      android.permission.CAMERA: granted=true\n"
)


def test_parse_verification_revoke():
    from core.outils_securite_100 import parse_verification_revoke
    assert parse_verification_revoke(
        DUMPSYS_REVOKE_CONFIRME, ["android.permission.CAMERA"]) == \
        {"android.permission.CAMERA": True}
    assert parse_verification_revoke(
        DUMPSYS_REVOKE_RATE, ["android.permission.CAMERA"]) == \
        {"android.permission.CAMERA": False}
    assert parse_verification_revoke(
        DUMPSYS_REVOKE_CONFIRME, ["android.permission.RECORD_AUDIO"]) == \
        {"android.permission.RECORD_AUDIO": None}
    assert parse_verification_revoke("", ["android.permission.CAMERA"]) == \
        {"android.permission.CAMERA": None}


def test_revoquer_permission_confirme_et_douteux(monkeypatch):
    import core.outils_securite_100 as securite
    _simuler_adb(monkeypatch, "core.outils_securite_100", [
        ("pm revoke", (True, "", "")),
        ("dumpsys package", (True, DUMPSYS_REVOKE_CONFIRME, "")),
    ])
    texte = securite.revoquer_permission("com.exemple.appli", "camera")
    assert "Permission retirée" in texte and "CAMERA" in texte
    _simuler_adb(monkeypatch, "core.outils_securite_100", [
        ("pm revoke", (True, "", "")),
        ("dumpsys package", (True, DUMPSYS_REVOKE_RATE, "")),
    ])
    texte = securite.revoquer_permission("com.exemple.appli", "camera")
    assert "non confirmé" in texte


def test_revoquer_permission_erreurs(monkeypatch):
    import core.outils_securite_100 as securite
    _simuler_adb(monkeypatch, "core.outils_securite_100", [
        ("pm revoke", (False, "", "Unknown package: com.x")),
        ("dumpsys package", (False, "", "")),
    ])
    assert "introuvable" in securite.revoquer_permission("com.x", "camera")
    assert "invalide" in securite.revoquer_permission("pas un paquet!", "camera")
    assert "inconnue" in securite.revoquer_permission("com.x", "teleportation")


if __name__ == "__main__":
    import importlib

    class Rustine:
        def setattr(self, cible, valeur):
            module, _, attr = cible.rpartition(".")
            setattr(importlib.import_module(module), attr, valeur)

    rustine = Rustine()
    test_vider_cache_mesure_avant_apres(rustine)
    test_vider_cache_refus_et_invalide(rustine)
    test_haut_parleur_bip_et_nettoyage(rustine)
    test_haut_parleur_push_impossible(rustine)
    test_vibreur(rustine)
    test_camera(rustine)
    test_parse_verification_revoke()
    test_revoquer_permission_confirme_et_douteux(rustine)
    test_revoquer_permission_erreurs(rustine)
    print("OK : outils sensibles non-root.")
