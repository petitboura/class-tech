"""Tests des outils sensibles du palier 100 % (audit risques B).

tester_haut_parleur, tester_vibreur, tester_camera,
revoquer_permission : outils appeles avec le pont moque (_echange :
AUCUN appel ADB reel, aucun telephone touche), sur des sorties
Android realistes figees ici.

Depuis backend/ : `pytest tests/test_outils_sensibles_100.py`
(ou `python tests/test_outils_sensibles_100.py`).
Demande mcp installe (import des modules d'outils).
"""

import contextlib
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import outils_materiel_100 as materiel  # noqa: E402
from core import outils_securite_100 as securite  # noqa: E402


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


def _acces_ok():
    return {"adb": "adb", "serie": "ABC123", "erreur": None, "note": None}


def _defense_adb(*args, **kwargs):
    raise AssertionError("ADB reel ne doit pas etre touche")


DUMPSYS_CAMERA_DEUX = (
    "Camera service statistics:\n"
    "  Number of camera devices: 2\n"
    "  Device 0 facing: BACK\n"
    "  Device 1 facing: FRONT\n"
)

DUMPSYS_VIBRATEUR = (
    "VibratorService state:\n"
    "  capabilities: VIBRATE\n"
    "  vibratorInfo: id=0\n"
)

DUMPSYS_AUDIO = (
    "STREAM_MUSIC: Muted: false Max: 15 (speaker): 7\n"
    "STREAM_RING: Muted: false Max: 7 (speaker): 5\n"
)

DUMPSYS_PAQUET = (
    "Packages:\n"
    "  Package [com.exemple.appli] (123):\n"
    "    userId=10123\n"
    "    runtime permissions:\n"
    "      android.permission.CAMERA: granted={camera}, flags=[ GRANTED_BY_DEFAULT ]\n"
    "      android.permission.RECORD_AUDIO: granted=true, flags=[ GRANTED_BY_DEFAULT ]\n"
    "    install permissions:\n"
    "      android.permission.INTERNET: granted=true\n"
    "    User 0:\n"
    "      installed=true\n"
)


# --- tester_camera : ouvrir_appli strict ---

def test_veut_ouvrir_appli():
    veut = materiel.veut_ouvrir_appli
    assert veut(True) is True
    assert veut(1) is True
    assert veut("true") is True
    assert veut(" VRAI ") is True
    assert veut("oui") is True
    assert veut("yes") is True
    assert veut(False) is False
    assert veut(0) is False
    assert veut(None) is False
    assert veut("") is False
    assert veut("false") is False
    assert veut("False") is False
    assert veut("non") is False
    assert veut("0") is False


def test_camera_chaine_false_nouvre_rien():
    envoyes = []

    def faux_executer(adb, serie, morceaux, delai=None):
        envoyes.append(morceaux)
        return True, DUMPSYS_CAMERA_DEUX, ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            reponse = materiel.tester_camera(ouvrir_appli="false")
    assert "2 caméras" in reponse
    assert "Pour finir le test" in reponse
    assert not any("STILL_IMAGE_CAMERA" in m for m in envoyes)


def test_camera_ouverture_demandee():
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[-1] == "android.media.action.STILL_IMAGE_CAMERA":
            return True, "Starting: Intent {}", ""
        return True, DUMPSYS_CAMERA_DEUX, ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            reponse = materiel.tester_camera(ouvrir_appli=True)
    assert "J'ai ouvert l'appli photo" in reponse


def test_camera_ouverture_ratee_et_lecture_ratee():
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[-1] == "android.media.action.STILL_IMAGE_CAMERA":
            return False, "", "Error: Activity not started"
        return True, DUMPSYS_CAMERA_DEUX, ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            assert "Je n'ai pas pu ouvrir" in materiel.tester_camera(ouvrir_appli=True)
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      lambda a, s, m, delai=None: (False, "", "boom")):
            assert "illisibles" in materiel.tester_camera()


# --- tester_vibreur : cas supporte, non supporte, rate ---

def test_vibreur_succes():
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[-1] == "1000":
            return True, "", ""
        return True, DUMPSYS_VIBRATEUR, ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            reponse = materiel.tester_vibreur()
    assert "détecté" in reponse and "une seconde" in reponse


def test_vibreur_non_supporte_et_rate():
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[-1] == "1000":
            return False, "", "cmd: unknown command 'vibrator'"
        return True, DUMPSYS_VIBRATEUR, ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            assert "Je ne peux pas déclencher" in materiel.tester_vibreur()
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      lambda a, s, m, delai=None: (False, "", "timeout")
                      if m[-1] == "1000" else (True, DUMPSYS_VIBRATEUR, "")):
            assert "n'a pas abouti" in materiel.tester_vibreur()


# --- tester_haut_parleur : bip joue, push rate ---

def test_haut_parleur_bip_ok():
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[:2] == ["shell", "dumpsys"]:
            return True, DUMPSYS_AUDIO, ""
        return True, "", ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            reponse = materiel.tester_haut_parleur()
    assert "music : 7 sur 15" in reponse
    assert "L'avez-vous entendu" in reponse


def test_haut_parleur_push_rate_nettoie_quand_meme():
    envoyes = []

    def faux_executer(adb, serie, morceaux, delai=None):
        envoyes.append(morceaux)
        if morceaux[:2] == ["shell", "dumpsys"]:
            return True, DUMPSYS_AUDIO, ""
        if morceaux[0] == "push":
            return False, "", "Protocol fault"
        return True, "", ""

    with _echange("core.outils_materiel_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_materiel_100", "executer_adb_serie",
                      faux_executer):
            reponse = materiel.tester_haut_parleur()
    assert "Je n'ai pas pu jouer" in reponse
    assert any(m[:2] == ["shell", "rm"] for m in envoyes)


# --- revoquer_permission : verification apres coup ---

def test_parse_permissions_accordees_runtime_seulement():
    accordees = securite.parse_permissions_accordees(
        DUMPSYS_PAQUET.format(camera="false"))
    assert accordees == {
        "android.permission.CAMERA": False,
        "android.permission.RECORD_AUDIO": True,
    }
    assert securite.parse_permissions_accordees("") == {}


def test_revoquer_validation_sans_adb():
    with _echange("core.outils_securite_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_securite_100", "executer_adb_serie",
                      _defense_adb):
            assert "nom d'appli invalide" in securite.revoquer_permission(
                "123 mauvais!", "camera")
            assert "permission inconnue" in securite.revoquer_permission(
                "com.exemple.appli", "teleportation")


def test_revoquer_paquet_introuvable():
    def faux_executer(adb, serie, morceaux, delai=None):
        return False, "", "Security exception: Unknown package: com.x"

    with _echange("core.outils_securite_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_securite_100", "executer_adb_serie",
                      faux_executer):
            reponse = securite.revoquer_permission("com.x", "camera")
    assert "introuvable" in reponse


def _faux_revoque(controle):
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[:3] == ["shell", "pm", "revoke"]:
            return True, "", ""
        if morceaux[:3] == ["shell", "dumpsys", "package"]:
            return controle
        raise AssertionError(f"appel inattendu : {morceaux}")

    return faux_executer


def test_revoquer_retrait_verifie():
    faux = _faux_revoque((True, DUMPSYS_PAQUET.format(camera="false"), ""))
    with _echange("core.outils_securite_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_securite_100", "executer_adb_serie",
                      faux):
            reponse = securite.revoquer_permission(
                "com.exemple.appli", "camera")
    assert "Permission retirée à com.exemple.appli : CAMERA" in reponse
    assert "Retrait vérifié" in reponse


def test_revoquer_non_confirme_et_controle_impossible():
    faux = _faux_revoque((True, DUMPSYS_PAQUET.format(camera="true"), ""))
    with _echange("core.outils_securite_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_securite_100", "executer_adb_serie",
                      faux):
            reponse = securite.revoquer_permission(
                "com.exemple.appli", "camera")
    assert "Non confirmé (toujours accordées) : CAMERA" in reponse
    faux_rate = _faux_revoque((False, "", "boom"))
    with _echange("core.outils_securite_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_securite_100", "executer_adb_serie",
                      faux_rate):
            reponse = securite.revoquer_permission(
                "com.exemple.appli", "camera")
    assert "Retrait non vérifié" in reponse


def test_revoquer_partiel():
    def faux_executer(adb, serie, morceaux, delai=None):
        if morceaux[:3] == ["shell", "pm", "revoke"]:
            if morceaux[-1] == "android.permission.ACCESS_FINE_LOCATION":
                return True, "", ""
            return False, "", "not a changeable permission type"
        return True, DUMPSYS_PAQUET.format(camera="false"), ""

    with _echange("core.outils_securite_100", "preparer_acces",
                  lambda: _acces_ok()):
        with _echange("core.outils_securite_100", "executer_adb_serie",
                      faux_executer):
            reponse = securite.revoquer_permission(
                "com.exemple.appli", "localisation")
    assert "ACCESS_FINE_LOCATION" in reponse
    assert "Reste non retiré" in reponse


if __name__ == "__main__":
    test_veut_ouvrir_appli()
    test_camera_chaine_false_nouvre_rien()
    test_camera_ouverture_demandee()
    test_camera_ouverture_ratee_et_lecture_ratee()
    test_vibreur_succes()
    test_vibreur_non_supporte_et_rate()
    test_haut_parleur_bip_ok()
    test_haut_parleur_push_rate_nettoie_quand_meme()
    test_parse_permissions_accordees_runtime_seulement()
    test_revoquer_validation_sans_adb()
    test_revoquer_paquet_introuvable()
    test_revoquer_retrait_verifie()
    test_revoquer_non_confirme_et_controle_impossible()
    test_revoquer_partiel()
    print("OK : outils sensibles 100 %.")
