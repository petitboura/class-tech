"""Tests matériel unitaires du téléphone (palier 100 %, sans root).

Chaque outil lit l'état réel du téléphone branché via adb (voir
pont_adb), l'analyse avec analyse_materiel, et renvoie un texte en
français. Quand le verdict final dépend des sens de l'utilisateur
(voir, entendre, sentir), l'outil le dit et pose la question, sans
jamais inventer le résultat.

Outils sensibles (action réelle, confirmation demandée par Classinus) :
tester_haut_parleur (joue un bip), tester_vibreur (fait vibrer),
tester_camera (ouvre l'appli photo, seulement si ouvrir_appli est vrai).
"""

from __future__ import annotations

import os
import tempfile

from core.analyse_materiel import (
    analyser_boutons,
    analyser_camera,
    analyser_ecoute_boutons,
    analyser_ecran,
    analyser_gps,
    analyser_haut_parleur,
    analyser_micro,
    analyser_vibreur,
    generer_bip_wav,
)
from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import DELAI_ADB_SECONDES, executer_adb_serie, preparer_acces

# Nom du bip de test sur le téléphone (dossier partagé, effacé après).
FICHIER_BIP_TELEPHONE = "/sdcard/classtech_bip.wav"

# Valeurs texte comprises comme "oui" pour ouvrir_appli (le pont MCP
# transmet parfois des chaines). Tout le reste veut dire non, y
# compris la chaine "false" (audit risques : "false" est truthy).
OUVRIR_APPLI_OUI = ("true", "1", "oui", "vrai", "yes")


def _avec_note(acces: dict, texte: str) -> str:
    """Ajoute la note (plusieurs téléphones) devant la réponse."""
    if acces.get("note"):
        return f"{acces['note']} {texte}"
    return texte


def veut_ouvrir_appli(valeur) -> bool:
    """Vrai si l'appel demande vraiment d'ouvrir l'appli. Pure."""
    if valeur is True:
        return True
    if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
        return valeur == 1
    if isinstance(valeur, str):
        return valeur.strip().lower() in OUVRIR_APPLI_OUI
    return False


@mcp_diagnostic.tool()
def tester_ecran_tactile() -> str:
    """Teste l'écran tactile : détection, multipoint, résolution.

    Lit la liste des périphériques tactiles du téléphone, puis guide
    l'utilisateur pour toucher chaque coin de l'écran.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, getevent, _ = executer_adb_serie(adb, serie, ["shell", "getevent", "-p"])
    if not ok:
        return _avec_note(acces, "Lecture tactile impossible sur ce téléphone.")
    ok_taille, taille, _ = executer_adb_serie(adb, serie, ["shell", "wm", "size"])
    ok_densite, densite, _ = executer_adb_serie(adb, serie, ["shell", "wm", "density"])
    ok_ecran, ecran, _ = executer_adb_serie(
        adb, serie, ["shell", "dumpsys display | grep mScreenState"]
    )
    analyse = analyser_ecran(
        getevent,
        taille if ok_taille else "",
        densite if ok_densite else "",
        ecran if ok_ecran else "",
    )
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def tester_gps() -> str:
    """Teste le GPS : mode de localisation, signal, position récente.

    Lit les réglages et le service de localisation, puis guide
    l'utilisateur pour un test à découvert avec une appli de carte.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok_mode, mode, _ = executer_adb_serie(adb, serie, ["shell", "settings", "get", "secure", "location_mode"])
    ok_loc, loc, _ = executer_adb_serie(adb, serie, ["shell", "dumpsys", "location"])
    if not ok_mode and not ok_loc:
        return _avec_note(acces, "Localisation illisible sur ce téléphone.")
    analyse = analyser_gps(mode if ok_mode else "", loc if ok_loc else "")
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def tester_micro() -> str:
    """Teste le micro : présence détectée par le système audio.

    Lit l'état audio du téléphone, puis guide l'utilisateur pour
    enregistrer et réécouter un mémo vocal.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(adb, serie, ["shell", "dumpsys", "audio"])
    if not ok:
        return _avec_note(acces, "État audio illisible sur ce téléphone.")
    analyse = analyser_micro(sortie)
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def tester_haut_parleur() -> str:
    """Teste le haut-parleur : état audio, puis bip de test audible.

    Joue un bip sur le téléphone (action réelle). La réponse demande à
    l'utilisateur s'il a entendu le bip : seul son oui compte comme test
    réussi, l'outil ne conclut jamais seul.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(adb, serie, ["shell", "dumpsys", "audio"])
    etat = analyser_haut_parleur(sortie).get("resume", "") if ok else "État audio illisible."
    try:
        with tempfile.TemporaryDirectory(prefix="classtech") as dossier:
            local = os.path.join(dossier, "bip.wav")
            generer_bip_wav(local)
            pousse = executer_adb_serie(
                adb, serie, ["push", local, FICHIER_BIP_TELEPHONE], delai=DELAI_ADB_SECONDES
            )
            joue = (False, "", "")
            if pousse[0]:
                joue = executer_adb_serie(
                    adb,
                    serie,
                    ["shell", "am", "start", "-a", "android.intent.action.VIEW",
                     "-d", f"file://{FICHIER_BIP_TELEPHONE}", "-t", "audio/wav"],
                    delai=DELAI_ADB_SECONDES,
                )
            executer_adb_serie(adb, serie, ["shell", "rm", "-f", FICHIER_BIP_TELEPHONE])
    except OSError:
        return _avec_note(acces, f"{etat} Bip impossible : écriture temporaire impossible sur ce PC.")
    if joue[0]:
        texte = (
            f"{etat} J'ai lancé un bip de test sur le téléphone. "
            "L'avez-vous entendu clairement ?"
        )
    else:
        texte = (
            f"{etat} Je n'ai pas pu jouer le bip de test directement. "
            "Ouvrez une vidéo ou une musique sur le téléphone et dites "
            "si le son sort bien du haut-parleur."
        )
    return _avec_note(acces, texte)


@mcp_diagnostic.tool()
def tester_vibreur() -> str:
    """Teste le vibreur : présence, puis vibration de test.

    Fait vibrer le téléphone si le modèle le permet (action réelle).
    Sinon, guide l'utilisateur (appel entrant ou alarme) et lui demande
    ce qu'il a senti.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(adb, serie, ["shell", "dumpsys", "vibrator"])
    analyse = analyser_vibreur(sortie, ok)
    declenche, _, erreur = executer_adb_serie(adb, serie, ["shell", "cmd", "vibrator", "vibrate", "1000"])
    if declenche:
        texte = analyse["resume"] + " J'ai lancé une vibration d'une seconde. L'avez-vous sentie ?"
    elif "unknown" in erreur.lower() or "can't find" in erreur.lower() or "not found" in erreur.lower():
        texte = (
            analyse["resume"]
            + " Je ne peux pas déclencher la vibration sur ce modèle. "
            "Demandez à un proche de vous appeler, ou réglez une alarme "
            "dans une minute : le téléphone vibre-t-il ?"
        )
    else:
        texte = analyse["resume"] + " La vibration de test n'a pas abouti : le téléphone vibre-t-il quand on vous appelle ?"
    return _avec_note(acces, texte)


@mcp_diagnostic.tool()
def tester_camera(ouvrir_appli: bool = False) -> str:
    """Teste la caméra : nombre et façades détectées par le téléphone.

    Si ouvrir_appli est vrai, ouvre aussi l'appli photo (action réelle)
    pour que l'utilisateur prenne une photo de test et décrive le résultat.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(adb, serie, ["shell", "dumpsys", "media.camera"])
    if not ok:
        return _avec_note(acces, "Caméras illisibles sur ce téléphone.")
    analyse = analyser_camera(sortie)
    texte = analyse["resume"]
    if veut_ouvrir_appli(ouvrir_appli):
        lance, _, _ = executer_adb_serie(
            adb, serie, ["shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA"]
        )
        if lance:
            texte += " J'ai ouvert l'appli photo : prenez une photo et dites si elle est nette."
        else:
            texte += " Je n'ai pas pu ouvrir l'appli photo : ouvrez-la vous-même, prenez une photo et dites si elle est nette."
    else:
        texte += " Pour finir le test, prenez une photo et dites si elle est nette."
    return _avec_note(acces, texte)


@mcp_diagnostic.tool()
def tester_boutons(ecouter_secondes: int = 0) -> str:
    """Teste les boutons physiques : inventaire, puis écoute en direct.

    Sans paramètre, liste les boutons déclarés par le téléphone et
    explique la suite. Avec ecouter_secondes (5 à 60), écoute les
    touches vraiment appuyées pendant ce temps et les rapporte.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(adb, serie, ["shell", "getevent", "-p"])
    if not ok:
        return _avec_note(acces, "Boutons illisibles sur ce téléphone.")
    analyse = analyser_boutons(sortie)
    duree = max(0, min(int(ecouter_secondes or 0), 60))
    if duree < 5:
        texte = (
            analyse["resume"]
            + " Pour finir le test, appuyez sur chaque bouton pendant que "
            "j'écoute : relancez ce test avec une durée d'écoute (par "
            "exemple 15 secondes)."
        )
        return _avec_note(acces, texte)
    ecoute = executer_adb_serie(
        adb, serie, ["shell", f"timeout {duree} getevent -lt"], delai=duree + 15
    )
    analyse_ecoute = analyser_ecoute_boutons(ecoute[1] if ecoute[1] else "")
    if not ecoute[0] and not ecoute[1]:
        return _avec_note(
            acces,
            analyse["resume"] + " L'écoute en direct a échoué sur ce modèle : "
            "appuyez sur chaque bouton et dites ceux qui ne répondent pas.",
        )
    return _avec_note(acces, analyse["resume"] + " " + analyse_ecoute["resume"])
