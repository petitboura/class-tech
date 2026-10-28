"""Pont root : commandes avec droits super-utilisateur via ADB (palier root).

Ce module ne declare aucun outil MCP : il fournit le transport partage
par tous les outils root (commandes `su -c`, verification que le
telephone est roote, messages standards quand root manque ou refuse).

Chaque outil root commence par preparer_root() : si ADB manque, si
aucun telephone n'est pret, ou si root est absent ou refuse, l'outil
renvoie un message clair au lieu d'echouer.

Marquage : chaque outil root ajoute AVERTISSEMENT_NON_TESTE a sa
reponse (aucun appareil roote disponible pour tester ici).
"""

import os
import re
import shlex

from core.pont_adb import (
    DELAI_ADB_LENT_SECONDES,
    DELAI_ADB_SECONDES,
    erreur_courte,
    executer_shell,
    parametre_shell_valide,
    preparer_appel,
)

# Marque ajoutee a la reponse de chaque outil root. Source unique.
AVERTISSEMENT_NON_TESTE = (
    "Note : outil root non teste sur appareil roote, resultat a confirmer."
)

# Dossiers racines autorises pour la lecture de fichiers systeme.
# Tout chemin hors de ces prefixes est refuse, jamais elargi.
PREFIXES_LECTURE_ROOT = (
    "/system",
    "/vendor",
    "/product",
    "/odm",
    "/oem",
    "/data",
    "/proc",
    "/sys",
    "/dev",
    "/apex",
    "/sbin",
    "/cache",
)

# Sous-chemins interdits meme sous un prefixe autorise (audit A).
# Vie privee : donnees des applis (/data/data, /data/user), fichiers
# perso (/data/media), secrets systeme (/data/misc : cles wifi...),
# frappes clavier (/dev/input). Pieges : peripheriques blocs
# (/dev/block : lectures enormes), memoire noyau brute (/proc/kcore,
# /proc/kallsyms : contourne la protection des adresses), debugfs
# (/sys/kernel/debug : lectures instables ou bloquantes).
SOUS_CHEMINS_INTERDITS = (
    "/data/media",
    "/data/data",
    "/data/user",
    "/data/misc",
    "/dev/block",
    "/dev/input",
    "/proc/kcore",
    "/proc/kallsyms",
    "/sys/kernel/debug",
)

# Sortie de `id` : uid=0(root) gid=0(root) ...
MOTIF_UID = re.compile(r"uid=(\d+)")


# Interrupteur des outils root (audit risques, 28/10/2026). Les
# outils root ne sont exposes par le serveur ET n'acceptent de
# tourner que si CLASSTECH_OUTILS_ROOT vaut "1". Eteint par defaut :
# tant que Bourama n'a pas donne l'ordre, Classinus ne peut ni les
# proposer (absents de list_tools) ni les executer (refus ici).
VARIABLE_OUTILS_ROOT = "CLASSTECH_OUTILS_ROOT"


def outils_root_actifs():
    """Vrai si les outils root sont autorises sur ce serveur."""
    return os.environ.get(VARIABLE_OUTILS_ROOT) == "1"


def message_root_desactive():
    """Message standard quand les outils root sont eteints. Fonction pure."""
    return (
        "Outils root desactives sur ce serveur. Le diagnostic root "
        "n'est pas encore ouvert."
    )


def commande_root(commande_interne):
    """Enrobe une commande pour `su -c`. Fonction pure.

    La commande interne est protegee (guillemets) pour traverser
    intacte les deux couches de shell (adb puis su).
    """
    return "su -c " + shlex.quote(commande_interne)


def executer_root(commande_interne, appareil_id, delai=DELAI_ADB_SECONDES):
    """Execute une commande en root sur le telephone designe.

    Meme contrat que executer_shell : {"ok", "sortie", "erreur"},
    ne leve jamais.
    """
    return executer_shell(commande_root(commande_interne), appareil_id, delai=delai)


def parse_uid_root(sortie):
    """Extrait l'uid de la sortie de `id`. Fonction pure, None si absent."""
    if not sortie:
        return None
    trouve = MOTIF_UID.search(sortie)
    if not trouve:
        return None
    try:
        return int(trouve.group(1))
    except ValueError:
        return None


def verifier_root(appareil_id):
    """Dit si root repond sur le telephone. Dictionnaire, ne leve jamais.

    Cles : root (bool), uid (entier ou None), detail (texte brut utile
    au diagnostic, vide si root actif).
    Delai long : le premier appel affiche une demande super-utilisateur
    sur le telephone, que l'utilisateur doit valider a la main.
    """
    resultat = executer_root("id", appareil_id, delai=DELAI_ADB_LENT_SECONDES)
    if not resultat["ok"]:
        return {"root": False, "uid": None, "detail": resultat["erreur"]}
    uid = parse_uid_root(resultat["sortie"])
    if uid == 0:
        return {"root": True, "uid": 0, "detail": ""}
    return {"root": False, "uid": uid, "detail": (resultat["sortie"] or "").strip()}


def message_root_absent(detail=""):
    """Message standard quand root manque ou refuse. Fonction pure."""
    texte = (
        "Acces root indisponible sur ce telephone. "
        "Cet outil exige un telephone roote avec une demande "
        "super-utilisateur validee sur l'ecran du telephone."
    )
    if detail:
        court = erreur_courte(detail)
        texte += f" Detail : {court}"
    return texte


def preparer_root():
    """Porte d'entree standard de chaque outil root.

    Refuse d'abord si les outils root sont eteints (voir
    outils_root_actifs), sans toucher a ADB.
    Renvoie (id_appareil, None) si ADB, telephone et root sont prets,
    sinon (None, message en francais).
    """
    if not outils_root_actifs():
        return None, message_root_desactive()
    appareil_id, erreur = preparer_appel()
    if erreur:
        return None, erreur
    verif = verifier_root(appareil_id)
    if not verif["root"]:
        return None, message_root_absent(verif["detail"])
    return appareil_id, None


def marquer_non_teste(texte):
    """Ajoute la marque non teste a une reponse d'outil. Fonction pure."""
    if not texte:
        return AVERTISSEMENT_NON_TESTE
    return texte.rstrip() + " " + AVERTISSEMENT_NON_TESTE


def chemin_lecture_valide(chemin):
    """Vrai si chemin peut etre lu en root. Fonction pure.

    Exige un chemin absolu, sans "..", sans caracteres dangereux,
    sous un des PREFIXES_LECTURE_ROOT et hors SOUS_CHEMINS_INTERDITS
    (donnees perso, secrets, pieges de lecture).
    """
    if not chemin or not isinstance(chemin, str):
        return False
    chemin = chemin.strip()
    if not chemin.startswith("/"):
        return False
    if not parametre_shell_valide(chemin):
        return False
    if chemin_interdit(chemin):
        return False
    return chemin_sous_prefixe(chemin)


def chemin_sous_prefixe(chemin):
    """Vrai si chemin est sous un prefixe autorise. Fonction pure."""
    if not chemin or not chemin.startswith("/"):
        return False
    return any(
        chemin == prefixe or chemin.startswith(prefixe + "/")
        for prefixe in PREFIXES_LECTURE_ROOT
    )


def chemin_interdit(chemin):
    """Vrai si chemin touche un sous-chemin interdit. Fonction pure."""
    if not chemin or not isinstance(chemin, str):
        return False
    chemin = chemin.strip()
    return any(
        chemin == interdit or chemin.startswith(interdit + "/")
        for interdit in SOUS_CHEMINS_INTERDITS
    )


def citer_chemin(chemin):
    """Protege un chemin valide pour le shell. Fonction pure."""
    return shlex.quote(chemin.strip())


__all__ = [
    "AVERTISSEMENT_NON_TESTE",
    "PREFIXES_LECTURE_ROOT",
    "SOUS_CHEMINS_INTERDITS",
    "chemin_interdit",
    "chemin_lecture_valide",
    "chemin_sous_prefixe",
    "citer_chemin",
    "commande_root",
    "executer_root",
    "marquer_non_teste",
    "message_root_absent",
    "message_root_desactive",
    "outils_root_actifs",
    "parse_uid_root",
    "preparer_root",
    "verifier_root",
    "VARIABLE_OUTILS_ROOT",
]
