"""Outils applis du telephone : liste, plantages, inutilisees (palier 80 %).

Trois lectures reelles via ADB, sans danger :
- lister_applis : paquets installes (choix : installees, systeme, toutes).
- lire_crashs_recents : plantages recents (tampon crash, repli dropbox).
- lister_applis_inutilisees : applis tierces pas ouvertes depuis X jours.
"""

import re
import time

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import DELAI_ADB_LENT_SECONDES, executer_shell, preparer_appel

# Choix valides pour lister_applis : choix -> option de list packages.
OPTIONS_LISTE_APPLIS = {"installees": "-3", "systeme": "-s", "toutes": ""}

MOTIF_PAQUET = re.compile(r"^package:([A-Za-z0-9_.:]+)")
MOTIF_CRASH_ENTETE = re.compile(
    r"^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+E/AndroidRuntime\(\s*\d+\):\s*FATAL EXCEPTION.*$"
)
MOTIF_CRASH_PROCESSUS = re.compile(r"Process:\s*([A-Za-z0-9_.:]+)")
MOTIF_CRASH_ERREUR = re.compile(r"([\w$.]*?(?:Exception|Error)[\w.]*\s*:\s*.{1,160})")
MOTIF_DROPBOX_ENTREE = re.compile(r"^(data_app_(?:crash|anr))\s+@\s*(.+?)\s*$")
MOTIF_USAGE_PAQUET = re.compile(r"package=([A-Za-z0-9_.:]+)")
MOTIF_USAGE_MOMENT = re.compile(r"lastTimeUsed=(\d+)")

MILLISECONDES_PAR_JOUR = 24 * 3600 * 1000


def parse_liste_packages(texte):
    """Parse `cmd package list packages` en noms de paquets. Fonction pure."""
    paquets = []
    if not texte:
        return paquets
    for ligne in texte.splitlines():
        trouve = MOTIF_PAQUET.match(ligne.strip())
        if trouve and trouve.group(1) not in paquets:
            paquets.append(trouve.group(1))
    return paquets


def formater_applis(paquets, quelles, limite):
    """Texte de reponse pour la liste d'applis. Fonction pure."""
    if not paquets:
        return f"Aucune appli trouvee ({quelles})."
    affichees = paquets[:limite]
    texte = f"{len(paquets)} applis ({quelles}) : " + ", ".join(affichees) + "."
    if len(paquets) > limite:
        texte += f" Et {len(paquets) - limite} autres."
    return texte


def parse_logcat_crash(texte):
    """Parse le tampon crash en [{moment, paquet, erreur}]. Fonction pure."""
    crashs = []
    if not texte:
        return crashs
    courant = None
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        entete = MOTIF_CRASH_ENTETE.match(ligne)
        if entete:
            if courant:
                crashs.append(courant)
            courant = {"moment": entete.group(1), "paquet": "", "erreur": ""}
            continue
        if courant is None:
            continue
        if not courant["paquet"]:
            processus = MOTIF_CRASH_PROCESSUS.search(ligne)
            if processus:
                courant["paquet"] = processus.group(1)
        if not courant["erreur"]:
            erreur = MOTIF_CRASH_ERREUR.search(ligne)
            if erreur and "FATAL EXCEPTION" not in ligne:
                courant["erreur"] = erreur.group(1).strip()
    if courant:
        crashs.append(courant)
    return [c for c in crashs if c["paquet"] or c["erreur"]]


def parse_dropbox_crashs(texte, limite=10):
    """Parse `dumpsys dropbox --print` en [{moment, paquet, erreur}].

    Fonction pure, repli quand le tampon crash est vide.
    """
    crashs = []
    if not texte:
        return crashs
    courant = None
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        entree = MOTIF_DROPBOX_ENTREE.match(ligne)
        if entree:
            if courant and (courant["paquet"] or courant["erreur"]):
                crashs.append(courant)
            courant = {"moment": entree.group(2), "paquet": "", "erreur": entree.group(1)}
            if len(crashs) >= limite:
                break
            continue
        if courant is None:
            continue
        if not courant["paquet"]:
            processus = MOTIF_CRASH_PROCESSUS.search(ligne)
            if processus:
                courant["paquet"] = processus.group(1)
                continue
            sujet = re.search(r"Subject:\s*([A-Za-z0-9_.:]+)", ligne)
            if sujet:
                courant["paquet"] = sujet.group(1)
    if courant and (courant["paquet"] or courant["erreur"]):
        crashs.append(courant)
    return crashs[:limite]


def formater_crashs(crashs):
    """Texte de reponse pour les plantages. Fonction pure."""
    if not crashs:
        return "Aucun plantage recent trouve."
    morceaux = []
    for crash in crashs:
        bout = crash["paquet"] or "appli inconnue"
        if crash["erreur"]:
            bout += f" ({crash['erreur']})"
        if crash["moment"]:
            bout += f" vers {crash['moment']}"
        morceaux.append(bout)
    return f"{len(crashs)} plantage(s) recent(s) : " + " ; ".join(morceaux) + "."


def parse_usagestats(texte):
    """Parse `dumpsys usagestats` en {paquet: dernier usage en ms}.

    Fonction pure : garde le moment le plus recent vu par paquet.
    """
    usages = {}
    if not texte:
        return usages
    for ligne in texte.splitlines():
        paquet = MOTIF_USAGE_PAQUET.search(ligne)
        moment = MOTIF_USAGE_MOMENT.search(ligne)
        if not paquet or not moment:
            continue
        try:
            instant = int(moment.group(1))
        except ValueError:
            continue
        nom = paquet.group(1)
        if instant > usages.get(nom, -1):
            usages[nom] = instant
    return usages


def selectionner_inutilisees(usages, paquets_tierces, jours, maintenant_ms=None):
    """Paquets tierces inutilisees depuis jours : [(paquet, jours_ou_None)].

    Fonction pure. jours_ou_None vaut None si jamais ouvertes (ou hors
    suivi), sinon le nombre de jours arrondi. Triees : jamais ouvertes
    d'abord, puis les plus anciennes.
    """
    if maintenant_ms is None:
        maintenant_ms = int(time.time() * 1000)
    limite_ms = maintenant_ms - jours * MILLISECONDES_PAR_JOUR
    inutilisees = []
    for paquet in paquets_tierces:
        dernier = usages.get(paquet, 0)
        if dernier <= 0 or dernier < limite_ms:
            age = None if dernier <= 0 else round((maintenant_ms - dernier) / MILLISECONDES_PAR_JOUR)
            inutilisees.append((paquet, age))
    inutilisees.sort(key=lambda item: (item[1] is not None, -(item[1] or 0)))
    return inutilisees


def formater_inutilisees(inutilisees, jours, limite):
    """Texte de reponse pour les applis inutilisees. Fonction pure."""
    if not inutilisees:
        return f"Aucune appli tierce inutilisee depuis {jours} jours."
    morceaux = []
    for paquet, age in inutilisees[:limite]:
        morceaux.append(paquet if age is None else f"{paquet} (il y a {age} jours)")
    texte = f"Applis pas ouvertes depuis {jours} jours : " + ", ".join(morceaux) + "."
    if len(inutilisees) > limite:
        texte += f" Et {len(inutilisees) - limite} autres."
    return texte


@mcp_diagnostic.tool()
def lister_applis(quelles: str = "installees", limite: int = 50) -> str:
    """Liste les applis du telephone : installees, systeme ou toutes.

    quelles : installees (par defaut), systeme ou toutes.
    limite : combien en montrer (1 a 500, 50 par defaut). Lecture seule.
    """
    quelles = (quelles or "").strip().lower() or "installees"
    if quelles not in OPTIONS_LISTE_APPLIS:
        return "Erreur : choix invalide, donne installees, systeme ou toutes."
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return "Erreur : limite invalide, donne un nombre entre 1 et 500."
    if not 1 <= limite <= 500:
        return "Erreur : limite invalide, donne un nombre entre 1 et 500."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    option = OPTIONS_LISTE_APPLIS[quelles]
    commande = f"cmd package list packages --user 0 {option}".strip()
    resultat = executer_shell(commande, appareil_id)
    if not resultat["ok"]:
        return f"Liste des applis illisible : {resultat['erreur']}"
    return formater_applis(parse_liste_packages(resultat["sortie"]), quelles, limite)


@mcp_diagnostic.tool()
def lire_crashs_recents(limite: int = 10) -> str:
    """Lit les plantages recents des applis (qui a planté, quelle erreur).

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return "Erreur : limite invalide, donne un nombre entre 1 et 50."
    if not 1 <= limite <= 50:
        return "Erreur : limite invalide, donne un nombre entre 1 et 50."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("logcat -d -b crash -v brief", appareil_id)
    if resultat["ok"]:
        crashs = parse_logcat_crash(resultat["sortie"])[:limite]
        if crashs:
            return formater_crashs(crashs)
    repli = executer_shell("dumpsys dropbox --print", appareil_id, delai=DELAI_ADB_LENT_SECONDES)
    if repli["ok"]:
        return formater_crashs(parse_dropbox_crashs(repli["sortie"], limite))
    return "Plantages illisibles pour le moment."


@mcp_diagnostic.tool()
def lister_applis_inutilisees(jours: int = 90, limite: int = 30) -> str:
    """Liste les applis tierces pas ouvertes depuis X jours (90 par defaut).

    Sert a reperer ce qui encombre le telephone. Lecture seule.
    """
    try:
        jours = int(jours)
    except (TypeError, ValueError):
        return "Erreur : jours invalide, donne un nombre entre 7 et 365."
    if not 7 <= jours <= 365:
        return "Erreur : jours invalide, donne un nombre entre 7 et 365."
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return "Erreur : limite invalide, donne un nombre entre 1 et 200."
    if not 1 <= limite <= 200:
        return "Erreur : limite invalide, donne un nombre entre 1 et 200."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    usages = executer_shell("dumpsys usagestats", appareil_id, delai=DELAI_ADB_LENT_SECONDES)
    if not usages["ok"]:
        return f"Usages illisibles : {usages['erreur']}"
    tierces = executer_shell("cmd package list packages --user 0 -3", appareil_id)
    if not tierces["ok"]:
        return f"Liste des applis illisible : {tierces['erreur']}"
    inutilisees = selectionner_inutilisees(
        parse_usagestats(usages["sortie"]), parse_liste_packages(tierces["sortie"]), jours)
    return formater_inutilisees(inutilisees, jours, limite)
