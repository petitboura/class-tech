"""Pont PC vers iPhone via libimobiledevice (Windows, lecture seule).

Ce module ne declare aucun outil MCP : il fournit le transport partage
par tous les outils iPhone (recherche des binaires, liste des appareils,
execution de commandes, messages standards quand rien n'est branche).

Sur PC Windows, sans jailbreak (interdit), la seule voie saine pour
parler a un iPhone branche en USB est libimobiledevice : idevice_id
liste les appareils, ideviceinfo lit les infos, idevicepair verifie
la confiance ("faire confiance a cet ordinateur" valide sur l'iPhone).
Chaque outil iPhone commence par preparer_appel_ios() : si les outils
manquent ou si aucun iPhone n'est pret, l'outil renvoie un message
clair au lieu d'echouer.

Prerequis PC : Apple Mobile Device Support (fourni avec iTunes telecharge
depuis le site Apple, pas la version Microsoft Store, ou avec l'appli
Apple Devices) pour le pilote USB, plus une version Windows de
libimobiledevice. Prerequis iPhone : cable USB, iPhone deverrouille,
"faire confiance" valide.

Lecture seule : ce pont ne lance jamais d'action (redemarrage, montage,
installation, sauvegarde). Tout echec donne ok False avec une
explication en francais, jamais une exception.
"""

from __future__ import annotations

import os
import shutil
import subprocess

# Noms des executables selon le systeme. Source unique, jamais recopiee.
SUFFIXE_EXE = ".exe" if os.name == "nt" else ""
OUTIL_LISTE = "idevice_id" + SUFFIXE_EXE
OUTIL_INFOS = "ideviceinfo" + SUFFIXE_EXE
OUTIL_APPARIAGE = "idevicepair" + SUFFIXE_EXE
OUTIL_DIAGNOSTICS = "idevicediagnostics" + SUFFIXE_EXE
OUTIL_APPLIS = "ideviceinstaller" + SUFFIXE_EXE

# Delai normal d'une commande, en secondes. L'appairage et les gros
# diagnostics demandent plus.
DELAI_IOS_SECONDES = 20
DELAI_IOS_LENT_SECONDES = 60

# Pages officielles. Source unique, jamais recopiee ailleurs.
URL_LIBIMOBILEDEVICE = "https://libimobiledevice.org/"
URL_LIBIMOBILEDEVICE_WINDOWS = "https://github.com/jrjr/libimobiledevice-windows/releases"
URL_ITUNES_APPLE = "https://www.apple.com/fr/itunes/"

# Domaines lockdown lus par ideviceinfo -q. Source unique.
DOMAINE_BASE = ""
DOMAINE_BATTERIE = "com.apple.mobile.battery"
DOMAINE_STOCKAGE = "com.apple.disk_usage"

# Cles lues dans le domaine de base (ideviceinfo sans -q).
CLES_INFOS_APPAREIL_IOS = {
    "DeviceName": "nom",
    "ProductName": "produit",
    "ProductType": "type_produit",
    "ProductVersion": "ios",
    "BuildVersion": "compilation",
    "ModelNumber": "modele",
    "SerialNumber": "serie",
    "UniqueDeviceID": "udid",
}

# Cles lues dans le domaine batterie. A valider en live sur iPhone.
CLES_BATTERIE_IOS = {
    "BatteryCurrentCapacity": "niveau",
    "BatteryIsCharging": "en_charge",
}

# Cles lues dans le domaine stockage. A valider en live sur iPhone.
CLES_STOCKAGE_IOS = {
    "TotalDiskCapacity": "total",
    "AmountDataAvailable": "disponible",
    "TotalSystemCapacity": "total_systeme",
    "AmountSystemAvailable": "disponible_systeme",
}


def _chemins_ios_candidats(nom_outil):
    """Dossiers ou chercher un outil iOS quand il n'est pas dans le PATH."""
    candidats = []
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            candidats.append(os.path.join(
                local, "Programs", "libimobiledevice", nom_outil))
        program_files = os.environ.get("ProgramFiles", "").strip()
        if program_files:
            candidats.append(os.path.join(
                program_files, "libimobiledevice", nom_outil))
        candidats.append(os.path.join("C:\\", "libimobiledevice", nom_outil))
        candidats.append(os.path.join("C:\\", "Program Files",
                                       "libimobiledevice", nom_outil))
        maison = os.path.expanduser("~")
        candidats.append(os.path.join(
            maison, "scoop", "shims", nom_outil))
        for dossier_msys in ("mingw64", "ucrt64", "clang64"):
            candidats.append(os.path.join(
                "C:\\", "msys64", dossier_msys, "bin", nom_outil))
    else:
        candidats.append(os.path.join("/usr/local/bin", nom_outil))
    return candidats


def trouver_outil_ios(nom_outil):
    """Chemin complet vers un outil iOS, ou None si introuvable.

    Fonction pure cote lecture seule : ne modifie rien, ne lance rien.
    """
    dans_path = shutil.which(nom_outil)
    if dans_path:
        return dans_path
    for candidat in _chemins_ios_candidats(nom_outil):
        if candidat and os.path.isfile(candidat):
            return candidat
    return None


def parse_sortie_idevice_id(texte):
    """Parse la sortie de `idevice_id -l` en liste d'UDID.

    Fonction pure, testee sans telephone. Chaque ligne non vide est
    un UDID ; les lignes d'erreur (ERROR...) sont ignorees.
    """
    udids = []
    if not texte:
        return udids
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("ERROR"):
            continue
        if ligne not in udids:
            udids.append(ligne)
    return udids


def parse_ideviceinfo(texte):
    """Parse la sortie de `ideviceinfo` en dictionnaire cle/valeur.

    Fonction pure, testee sans telephone. Format : "Cle: valeur".
    """
    infos = {}
    if not texte:
        return infos
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if ":" not in ligne:
            continue
        cle, _, valeur = ligne.partition(":")
        cle, valeur = cle.strip(), valeur.strip()
        if cle:
            infos[cle] = valeur
    return infos


def iphones_connectes():
    """UDID des iPhones vus, sous forme (liste, raison).

    raison vaut "ok" en cas de succes, "outils_absents" si
    libimobiledevice est introuvable, "erreur" si la commande a
    echoue. Ne leve jamais.
    """
    chemin = trouver_outil_ios(OUTIL_LISTE)
    if not chemin:
        return [], "outils_absents"
    try:
        termine = subprocess.run(
            [chemin, "-l"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=DELAI_IOS_LENT_SECONDES,
        )
    except (OSError, subprocess.TimeoutExpired):
        return [], "erreur"
    if termine.returncode != 0:
        return [], "erreur"
    return parse_sortie_idevice_id(termine.stdout), "ok"


def choisir_iphone(udids):
    """Premier UDID de la liste, ou None. Fonction pure."""
    for udid in udids:
        if udid:
            return udid
    return None


def executer_ios(outil, arguments, udid=None, delai=DELAI_IOS_SECONDES):
    """Execute un outil libimobiledevice, renvoie {"ok", "sortie", "erreur"}.

    outil est un nom court ("liste", "infos", "appairage") ou un nom
    d'executable. Ne leve jamais : tout echec (outil absent, delai
    depasse, code de retour non nul) donne ok False avec une
    explication en francais.
    """
    nom = NOMS_OUTILS_COURTS.get(outil, outil)
    chemin = trouver_outil_ios(nom)
    if not chemin:
        return {"ok": False, "sortie": "", "erreur": "libimobiledevice introuvable sur ce PC."}
    commande = [chemin]
    if udid:
        commande += ["-u", udid]
    commande += list(arguments)
    try:
        termine = subprocess.run(
            commande,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=delai,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "sortie": "", "erreur": "delai depasse, l'iPhone n'a pas repondu a temps."}
    except OSError:
        return {"ok": False, "sortie": "", "erreur": "impossible de lancer l'outil iOS sur ce PC."}
    if termine.returncode != 0:
        detail = (termine.stderr or termine.stdout or "").strip()
        if len(detail) > 300:
            detail = detail[:300] + "…"
        return {"ok": False, "sortie": termine.stdout or "", "erreur": detail or "commande refusee par l'iPhone."}
    return {"ok": True, "sortie": termine.stdout or "", "erreur": ""}


# Noms courts acceptes par executer_ios(). Source unique.
NOMS_OUTILS_COURTS = {
    "liste": OUTIL_LISTE,
    "infos": OUTIL_INFOS,
    "appairage": OUTIL_APPARIAGE,
    "diagnostics": OUTIL_DIAGNOSTICS,
    "applis": OUTIL_APPLIS,
}


def lire_domaine(udid, domaine, cle=None):
    """Lit un domaine lockdown via ideviceinfo. Ne leve jamais."""
    arguments = ["-q", domaine]
    if cle:
        arguments += ["-k", cle]
    resultat = executer_ios("infos", arguments, udid=udid)
    if not resultat["ok"]:
        return resultat
    if cle:
        return {"ok": True, "sortie": resultat["sortie"].strip(), "erreur": ""}
    return resultat


def parse_validation_appairage(texte, retour_ok):
    """True si `idevicepair validate` a confirme la confiance.

    Fonction pure, testee sans telephone : succes seulement si la
    commande a reussi ET que la sortie contient SUCCESS.
    """
    if not retour_ok:
        return False
    return "success" in (texte or "").lower()


def confiance_iphone(udid):
    """Etat de confiance de l'iPhone, sous forme (confirme, raison).

    raison vaut "ok", "outils_absents", "refuse" (pas encore de
    confiance) ou "erreur". Lecture seule passive : idevicepair
    validate ne declenche aucun nouvel appairage. Ne leve jamais.
    """
    resultat = executer_ios("appairage", ["validate"], udid=udid)
    if resultat["erreur"] == "libimobiledevice introuvable sur ce PC.":
        return False, "outils_absents"
    if parse_validation_appairage(resultat["sortie"], resultat["ok"]):
        return True, "ok"
    if not resultat["ok"] and "No device found" in (resultat["sortie"] + resultat["erreur"]):
        return False, "erreur"
    return False, "refuse"


def erreur_courte_ios(erreur, maxi=200):
    """Erreur iPhone nettoyee pour affichage. Fonction pure.

    Tronque a maxi caracteres et remplace les "--" (regle du depot :
    jamais de tirets doubles dans un texte affiche).
    """
    if not erreur:
        return "commande refusee par l'iPhone."
    texte = " ".join(str(erreur).split())
    if len(texte) > maxi:
        texte = texte[:maxi] + "…"
    return texte.replace("--", ",").strip() or "commande refusee par l'iPhone."


def message_outils_ios_absents():
    """Message standard quand libimobiledevice est introuvable. Fonction pure."""
    return (
        "Les outils iPhone sont introuvables sur ce PC, impossible de parler "
        "a l'iPhone. Installe Apple Mobile Device Support (avec iTunes depuis "
        f"le site Apple : {URL_ITUNES_APPLE}) puis libimobiledevice pour Windows "
        f"(page du projet : {URL_LIBIMOBILEDEVICE}, versions Windows : "
        f"{URL_LIBIMOBILEDEVICE_WINDOWS}), puis reessaie."
    )


def message_aucun_iphone(udids, confiance_refusee=False):
    """Message standard quand aucun iPhone n'est pret. Fonction pure."""
    if not udids:
        return (
            "Aucun iPhone branché detecte. Branche l'iPhone en USB avec un "
            "cable Apple ou certifie, deverrouille l'iPhone, et valide "
            "\"faire confiance\" sur l'ecran de l'iPhone."
        )
    if confiance_refusee:
        return (
            "iPhone vu mais pas encore de confiance. Sur l'iPhone, valide "
            "\"faire confiance a cet ordinateur\" puis reessaie."
        )
    return (
        "iPhone vu mais pas pret pour le moment. Deverrouille l'iPhone, "
        "valide \"faire confiance\" si demande, puis reessaie."
    )


def resumer_liaison_ios():
    """Etat complet de la liaison PC vers iPhone, en un dictionnaire.

    Cles : outils_trouves, udids, udid_choisi, confiance, pret,
    message (None si pret, sinon l'explication en francais).
    """
    udids, raison = iphones_connectes()
    if raison == "outils_absents":
        return {
            "outils_trouves": False,
            "udids": [],
            "udid_choisi": None,
            "confiance": False,
            "pret": False,
            "message": message_outils_ios_absents(),
        }
    if raison != "ok":
        return {
            "outils_trouves": True,
            "udids": [],
            "udid_choisi": None,
            "confiance": False,
            "pret": False,
            "message": "Les outils iPhone ne repondent pas sur ce PC, reessaie dans un moment.",
        }
    choisi = choisir_iphone(udids)
    if choisi is None:
        return {
            "outils_trouves": True,
            "udids": [],
            "udid_choisi": None,
            "confiance": False,
            "pret": False,
            "message": message_aucun_iphone([]),
        }
    confirme, _raison_confiance = confiance_iphone(choisi)
    if not confirme:
        return {
            "outils_trouves": True,
            "udids": udids,
            "udid_choisi": None,
            "confiance": False,
            "pret": False,
            "message": message_aucun_iphone(udids, confiance_refusee=True),
        }
    return {
        "outils_trouves": True,
        "udids": udids,
        "udid_choisi": choisi,
        "confiance": True,
        "pret": True,
        "message": None,
    }


def preparer_appel_ios():
    """Porte d'entree standard de chaque outil iPhone.

    Renvoie (udid, None) si tout est pret, sinon (None, message).
    """
    liaison = resumer_liaison_ios()
    if not liaison["pret"]:
        return None, liaison["message"]
    return liaison["udid_choisi"], None


__all__ = [
    "CLES_BATTERIE_IOS",
    "CLES_INFOS_APPAREIL_IOS",
    "CLES_STOCKAGE_IOS",
    "DELAI_IOS_LENT_SECONDES",
    "DELAI_IOS_SECONDES",
    "DOMAINE_BASE",
    "DOMAINE_BATTERIE",
    "DOMAINE_STOCKAGE",
    "NOMS_OUTILS_COURTS",
    "OUTIL_APPARIAGE",
    "OUTIL_APPLIS",
    "OUTIL_DIAGNOSTICS",
    "OUTIL_INFOS",
    "OUTIL_LISTE",
    "URL_ITUNES_APPLE",
    "URL_LIBIMOBILEDEVICE",
    "URL_LIBIMOBILEDEVICE_WINDOWS",
    "choisir_iphone",
    "confiance_iphone",
    "erreur_courte_ios",
    "executer_ios",
    "iphones_connectes",
    "lire_domaine",
    "message_aucun_iphone",
    "message_outils_ios_absents",
    "parse_ideviceinfo",
    "parse_sortie_idevice_id",
    "parse_validation_appairage",
    "preparer_appel_ios",
    "resumer_liaison_ios",
    "trouver_outil_ios",
]
