"""Pont PC vers telephone via ADB, paliers 80 % et 100 % (Windows d'abord).

Ce module ne declare aucun outil MCP : il fournit le transport partage
par tous les outils telephone (recherche d'ADB, liste des appareils,
execution de commandes, messages standards quand rien n'est branche).

ADB (Android Debug Bridge) est l'outil officiel Google pour parler a un
telephone branche en USB avec le mode developpeur active. Chaque outil
telephone du palier 80 % commence par preparer_appel() : si ADB manque ou si aucun
telephone n'est pret, l'outil renvoie un message clair au lieu d'echouer.
Les outils du palier 100 % passent par preparer_acces() et
executer_adb_serie() : meme pont, autre forme de reponse.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

# Nom de l'executable selon le systeme. Source unique, jamais recopie.
NOM_EXECUTABLE_ADB = "adb.exe" if os.name == "nt" else "adb"

# Delai normal d'une commande ADB, en secondes. Les commandes lentes
# (recherche de fichiers, statistiques batterie) demandent plus.
DELAI_ADB_SECONDES = 20
DELAI_ADB_LENT_SECONDES = 90

# Page officielle pour recuperer ADB seul (platform-tools). Une seule
# adresse dans tout le serveur, documentee ici.
URL_PLATFORM_TOOLS = "https://developer.android.com/tools/releases/platform-tools"

# Etats ADB consideres comme prets pour un diagnostic.
ETATS_APPAREIL_PRET = ("device",)

# Etats ADB connus mais non utilisables, avec leur explication courte.
EXPLICATIONS_ETAT_APPAREIL = {
    "unauthorized": "telephone non autorise (valide la demande sur l'ecran du telephone)",
    "offline": "telephone hors ligne (debranche puis rebranche le cable)",
    "no device": "aucun telephone vu par ADB",
}


def _chemins_adb_candidats():
    """Chemins ou chercher ADB quand il n'est pas dans le PATH."""
    candidats = []
    for variable in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        racine = os.environ.get(variable, "").strip()
        if racine:
            candidats.append(os.path.join(racine, "platform-tools", NOM_EXECUTABLE_ADB))
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            candidats.append(os.path.join(
                local, "Android", "Sdk", "platform-tools", NOM_EXECUTABLE_ADB))
        candidats.append(os.path.join("C:\\", "Android", "platform-tools", NOM_EXECUTABLE_ADB))
        candidats.append(os.path.join("C:\\", "platform-tools", NOM_EXECUTABLE_ADB))
    else:
        maison = os.path.expanduser("~")
        candidats.append(os.path.join(maison, "Android", "Sdk", "platform-tools", NOM_EXECUTABLE_ADB))
        candidats.append(os.path.join(maison, "platform-tools", NOM_EXECUTABLE_ADB))
    return candidats


def trouver_adb():
    """Chemin complet vers ADB, ou None si introuvable.

    Fonction pure cote lecture seule : ne modifie rien, ne lance rien.
    """
    dans_path = shutil.which(NOM_EXECUTABLE_ADB)
    if dans_path:
        return dans_path
    for candidat in _chemins_adb_candidats():
        if candidat and os.path.isfile(candidat):
            return candidat
    return None


def parse_sortie_devices(texte):
    """Parse la sortie de `adb devices [-l]` en liste d'appareils.

    Fonction pure, testee sans telephone. Chaque appareil donne
    {"id": numero de serie, "etat": etat ADB brut}.
    """
    appareils = []
    if not texte:
        return appareils
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("List of devices") or ligne.startswith("*"):
            continue
        morceaux = ligne.split()
        if len(morceaux) >= 2:
            appareils.append({"id": morceaux[0], "etat": morceaux[1]})
    return appareils


def appareils_connectes():
    """Appareils vus par ADB, sous forme (liste, raison).

    raison vaut "ok" en cas de succes, "adb_absent" si ADB est
    introuvable, "erreur" si la commande a echoue. Ne leve jamais.
    """
    chemin_adb = trouver_adb()
    if not chemin_adb:
        return [], "adb_absent"
    try:
        termine = subprocess.run(
            [chemin_adb, "devices", "-l"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=DELAI_ADB_LENT_SECONDES,
        )
    except (OSError, subprocess.TimeoutExpired):
        return [], "erreur"
    if termine.returncode != 0:
        return [], "erreur"
    return parse_sortie_devices(termine.stdout), "ok"


def choisir_appareil(appareils):
    """Premier appareil pret, ou None. Fonction pure."""
    for appareil in appareils:
        if appareil.get("etat") in ETATS_APPAREIL_PRET:
            return appareil
    return None


def executer_adb(arguments, delai=DELAI_ADB_SECONDES):
    """Execute `adb ...` et renvoie {"ok", "sortie", "erreur"}.

    Ne leve jamais : tout echec (ADB absent, delai depasse, code de
    retour non nul) donne ok False avec une explication en francais.
    """
    chemin_adb = trouver_adb()
    if not chemin_adb:
        return {"ok": False, "sortie": "", "erreur": "ADB introuvable sur ce PC."}
    try:
        termine = subprocess.run(
            [chemin_adb, *arguments],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=delai,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "sortie": "", "erreur": "delai depasse, le telephone n'a pas repondu a temps."}
    except OSError:
        return {"ok": False, "sortie": "", "erreur": "impossible de lancer ADB sur ce PC."}
    if termine.returncode != 0:
        detail = (termine.stderr or termine.stdout or "").strip()
        if len(detail) > 300:
            detail = detail[:300] + "…"
        return {"ok": False, "sortie": termine.stdout or "", "erreur": detail or "commande refusee par le telephone."}
    return {"ok": True, "sortie": termine.stdout or "", "erreur": ""}


def executer_shell(commande, appareil_id, delai=DELAI_ADB_SECONDES):
    """Execute une commande shell sur le telephone designe. Ne leve jamais."""
    return executer_adb(["-s", appareil_id, "shell", commande], delai=delai)


# Caracteres autorises pour un parametre injecte dans une commande shell
# (dossier, limite). Tout le reste est refuse, jamais echappe a moitié.
MOTIF_PARAMETRE_SHELL = re.compile(r"^[A-Za-z0-9_/][A-Za-z0-9_/ .():-]*$")


def parametre_shell_valide(valeur):
    """Vrai si valeur peut passer telle quelle dans une commande shell."""
    if not valeur or len(valeur) > 200:
        return False
    if ".." in valeur or ";" in valeur or "&" in valeur or "|" in valeur:
        return False
    return bool(MOTIF_PARAMETRE_SHELL.match(valeur))


def erreur_courte(erreur, maxi=200):
    """Erreur ADB/telephone nettoyee pour affichage. Fonction pure.

    Tronque a maxi caracteres et remplace les "--" (regle MUSE.md :
    jamais de tirets doubles dans un texte affiche). Les sorties
    brutes de diagnostic (dmesg, fichiers) ne passent PAS par ici :
    ce sont des donnees, pas du texte redige.
    """
    if not erreur:
        return "commande refusee par le telephone."
    texte = " ".join(str(erreur).split())
    if len(texte) > maxi:
        texte = texte[:maxi] + "…"
    return texte.replace("--", ",").strip() or "commande refusee par le telephone."


def message_adb_absent():
    """Message standard quand ADB est introuvable. Fonction pure."""
    return (
        "ADB est introuvable sur ce PC, impossible de parler au telephone. "
        "Installe les platform-tools Google puis reessaie "
        f"(page officielle : {URL_PLATFORM_TOOLS})."
    )


def message_aucun_telephone(appareils):
    """Message standard quand aucun telephone n'est pret. Fonction pure."""
    if not appareils:
        return (
            "Aucun telephone branché detecte. Branche le telephone en USB, "
            "active le mode developpeur puis le debogage USB, et valide "
            "l'autorisation sur l'ecran du telephone."
        )
    details = []
    for appareil in appareils:
        etat = appareil.get("etat", "?")
        explication = EXPLICATIONS_ETAT_APPAREIL.get(etat, f"etat {etat}")
        details.append(f"{appareil.get('id', '?')} : {explication}")
    return (
        "Telephone vu mais pas pret : " + ", ".join(details) + ". "
        "Valide l'autorisation sur l'ecran du telephone puis reessaie."
    )


def resumer_liaison():
    """Etat complet de la liaison PC vers telephone, en un dictionnaire.

    Cles : adb_trouve, adb_chemin, appareils, appareil_choisi, pret,
    message (None si pret, sinon l'explication en francais).
    """
    chemin_adb = trouver_adb()
    if not chemin_adb:
        return {
            "adb_trouve": False,
            "adb_chemin": None,
            "appareils": [],
            "appareil_choisi": None,
            "pret": False,
            "message": message_adb_absent(),
        }
    appareils, raison = appareils_connectes()
    if raison != "ok":
        return {
            "adb_trouve": True,
            "adb_chemin": chemin_adb,
            "appareils": [],
            "appareil_choisi": None,
            "pret": False,
            "message": "ADB ne repond pas sur ce PC, reessaie dans un moment.",
        }
    choisi = choisir_appareil(appareils)
    if choisi is None:
        return {
            "adb_trouve": True,
            "adb_chemin": chemin_adb,
            "appareils": appareils,
            "appareil_choisi": None,
            "pret": False,
            "message": message_aucun_telephone(appareils),
        }
    return {
        "adb_trouve": True,
        "adb_chemin": chemin_adb,
        "appareils": appareils,
        "appareil_choisi": choisi,
        "pret": True,
        "message": None,
    }


def preparer_appel():
    """Porte d'entree standard de chaque outil telephone.

    Renvoie (id_appareil, None) si tout est pret, sinon (None, message).
    """
    liaison = resumer_liaison()
    if not liaison["pret"]:
        return None, liaison["message"]
    return liaison["appareil_choisi"]["id"], None


# Palier 100 % : acces par numero de serie, sur le meme pont.
# preparer_acces(), lister_telephones() et analyser_sortie_devices()
# sont repris tels quels du palier 100 %. trouver_adb() et
# DELAI_ADB_SECONDES restent ceux du palier 80 % (recherche elargie,
# 20 secondes) et servent aux deux jeux d'outils.


MESSAGE_ADB_MANQUANT = (
    "Je ne trouve pas le programme adb sur cet ordinateur. Installez "
    "Android Platform Tools, ajoutez adb au PATH, puis réessayez."
)

MESSAGE_TELEPHONE_MANQUANT = (
    "Aucun téléphone détecté. Branchez le téléphone au PC avec un câble "
    "USB, activez le débogage USB (options pour développeurs), puis "
    "réessayez."
)

MESSAGE_NON_AUTORISE = (
    "Le téléphone est branché mais n'a pas autorisé cet ordinateur. "
    "Regardez l'écran du téléphone et acceptez la demande d'autorisation "
    "du débogage USB, puis réessayez."
)


def analyser_sortie_devices(sortie: str) -> dict[str, list[str]]:
    """Trie la sortie de `adb devices` en trois listes de numéros.

    prets : téléphone branché et autorisé (état device).
    non_autorises : branché mais autorisation en attente (unauthorized).
    autres : hors ligne ou état inconnu (offline, etc.).
    Fonction pure, testée sans téléphone.
    """
    resultat = {"prets": [], "non_autorises": [], "autres": []}
    for ligne in sortie.splitlines():
        morceaux = ligne.split()
        if len(morceaux) != 2:
            continue
        serie, etat = morceaux
        if serie in ("List", "devices", "attached", "de"):
            continue
        if etat == "device":
            resultat["prets"].append(serie)
        elif etat == "unauthorized":
            resultat["non_autorises"].append(serie)
        else:
            resultat["autres"].append(serie)
    return resultat


def lister_telephones(adb: str) -> dict[str, list[str]]:
    """Téléphones vus par adb, triés (voir analyser_sortie_devices)."""
    try:
        termine = subprocess.run(
            [adb, "devices"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=DELAI_ADB_SECONDES,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"prets": [], "non_autorises": [], "autres": []}
    if termine.returncode != 0:
        return {"prets": [], "non_autorises": [], "autres": []}
    return analyser_sortie_devices(termine.stdout)


def executer_adb_serie(
    adb: str,
    serie: str,
    morceaux: list[str],
    delai: int = DELAI_ADB_SECONDES,
) -> tuple[bool, str, str]:
    """Exécute `adb -s serie ...morceaux`, renvoie (réussi, sortie, erreur).

    Palier 100 % (reponse en tuple). Nom distinct de executer_adb()
    du palier 80 % (reponse en dictionnaire), dont la signature differe.
    Ne lève jamais d'exception : le délai dépassé, l'interruption et
    l'échec de lancement sont renvoyés comme un échec propre, que
    l'outil appelant traduit en message simple.
    """
    try:
        termine = subprocess.run(
            [adb, "-s", serie, *morceaux],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=delai,
        )
    except subprocess.TimeoutExpired as exc:
        # Sortie partielle conservée : pour une écoute (getevent), le
        # délai écoulé est le cas normal, pas une erreur.
        partielle = exc.stdout if isinstance(exc.stdout, str) else ""
        return False, partielle or "", f"délai dépassé ({delai} secondes)"
    except OSError as exc:
        return False, "", str(exc)
    return termine.returncode == 0, termine.stdout, termine.stderr.strip()


def preparer_acces() -> dict[str, str | None]:
    """Prépare l'accès au téléphone, ou explique ce qui bloque.

    Renvoie toujours les clés adb, serie, erreur et note. Si erreur
    n'est pas None, l'outil appelant la renvoie telle quelle. Si note
    n'est pas None (plusieurs téléphones), l'outil l'ajoute à sa réponse.
    """
    adb = trouver_adb()
    if adb is None:
        return {"adb": None, "serie": None, "erreur": MESSAGE_ADB_MANQUANT, "note": None}
    telephones = lister_telephones(adb)
    if telephones["prets"]:
        serie = telephones["prets"][0]
        note = None
        if len(telephones["prets"]) > 1:
            note = (
                f"Plusieurs téléphones détectés, j'utilise le premier ({serie})."
            )
        return {"adb": adb, "serie": serie, "erreur": None, "note": note}
    if telephones["non_autorises"]:
        return {"adb": adb, "serie": None, "erreur": MESSAGE_NON_AUTORISE, "note": None}
    return {"adb": adb, "serie": None, "erreur": MESSAGE_TELEPHONE_MANQUANT, "note": None}


__all__ = [
    "DELAI_ADB_LENT_SECONDES",
    "DELAI_ADB_SECONDES",
    "MESSAGE_ADB_MANQUANT",
    "MESSAGE_NON_AUTORISE",
    "MESSAGE_TELEPHONE_MANQUANT",
    "NOM_EXECUTABLE_ADB",
    "URL_PLATFORM_TOOLS",
    "analyser_sortie_devices",
    "appareils_connectes",
    "choisir_appareil",
    "executer_adb",
    "erreur_courte",
    "executer_adb_serie",
    "executer_shell",
    "lister_telephones",
    "message_adb_absent",
    "message_aucun_telephone",
    "parametre_shell_valide",
    "parse_sortie_devices",
    "preparer_acces",
    "preparer_appel",
    "resumer_liaison",
    "trouver_adb",
]
