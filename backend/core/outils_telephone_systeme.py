"""Outils systeme du telephone : version Android, erreurs recentes.

Deux lectures reelles via ADB, sans danger :
- lire_version_systeme : version Android, correctif, compilation.
- lire_erreurs_recentes : erreurs du journal systeme, groupees par cause.
"""

import re
from collections import Counter

from core.outils_diagnostic_commun import mcp_diagnostic
from core.outils_telephone_base import parse_getprop
from core.pont_adb import executer_shell, preparer_appel

MOTIF_LOGCAT_ERREUR = re.compile(
    r"^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+E/(\S+)\(\s*\d+\):\s*(.{1,200}).*$"
)


def formater_version(infos):
    """Texte de reponse pour la version systeme. Fonction pure."""
    android = infos.get("ro.build.version.release", "")
    sdk = infos.get("ro.build.version.sdk", "")
    patch = infos.get("ro.build.version.security_patch", "")
    compilation = infos.get("ro.build.id", "")
    if not android and not sdk:
        return "Version systeme illisible pour le moment."
    morceaux = []
    if android:
        morceaux.append(f"Android {android}")
    if sdk:
        morceaux.append(f"SDK {sdk}")
    if patch:
        morceaux.append(f"correctif du {patch}")
    if compilation:
        morceaux.append(f"compilation {compilation}")
    return "Systeme : " + ", ".join(morceaux) + "."


def parse_logcat_erreurs(texte):
    """Parse des lignes logcat erreur en (total, compteur_tags, exemples).

    Fonction pure. exemples = [(moment, tag, message)] les plus recents.
    """
    compteur = Counter()
    exemples = []
    total = 0
    if not texte:
        return total, compteur, exemples
    for ligne in texte.splitlines():
        trouve = MOTIF_LOGCAT_ERREUR.match(ligne.strip())
        if not trouve:
            continue
        total += 1
        moment, tag, message = trouve.groups()
        compteur[tag] += 1
        exemples.append((moment, tag, message.strip()))
    return total, compteur, exemples


def formater_erreurs(total, compteur, exemples, limite_exemples=10):
    """Texte de reponse pour les erreurs recentes. Fonction pure."""
    if total == 0:
        return "Aucune erreur recente dans le journal systeme."
    morceaux = []
    for tag, nombre in compteur.most_common(8):
        morceaux.append(f"{tag} ({nombre})")
    texte = f"{total} erreur(s) recente(s), par cause : " + ", ".join(morceaux) + "."
    recents = exemples[-limite_exemples:]
    if recents:
        details = " ; ".join(f"{tag} : {message}" for _m, tag, message in recents)
        texte += " Dernieres : " + details + "."
    return texte


@mcp_diagnostic.tool()
def lire_version_systeme() -> str:
    """Lit la version Android, le correctif de securite et la compilation.

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("getprop", appareil_id)
    if not resultat["ok"]:
        return f"Version systeme illisible : {resultat['erreur']}"
    return formater_version(parse_getprop(resultat["sortie"]))


@mcp_diagnostic.tool()
def lire_erreurs_recentes(limite: int = 100) -> str:
    """Lit les erreurs recentes du journal systeme, groupees par cause.

    limite : lignes analysees (10 a 1000, 100 par defaut). Lecture seule.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return "Erreur : limite invalide, donne un nombre entre 10 et 1000."
    if not 10 <= limite <= 1000:
        return "Erreur : limite invalide, donne un nombre entre 10 et 1000."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell(f"logcat -d -v brief *:E -t {limite}", appareil_id)
    if not resultat["ok"]:
        return f"Journal illisible : {resultat['erreur']}"
    total, compteur, exemples = parse_logcat_erreurs(resultat["sortie"])
    return formater_erreurs(total, compteur, exemples)
