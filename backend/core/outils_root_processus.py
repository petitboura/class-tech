"""Outils root : processus et verrous de reveil (palier root).

Deux lectures reelles via `su -c`, sans rien modifier :
- root_lister_processus : processus qui utilisent le plus le CPU.
- root_lire_wakelocks : applis qui empechent le telephone de dormir.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_root import executer_root, marquer_non_teste, preparer_root

# Ligne `top -n 1` (toybox) : PID PR CPU% S #THR VSS RSS PCY UID Name.
MOTIF_TOP = re.compile(
    r"^\s*(\d+)\s+\S+\s+(\S+)\s+(\S)\s+\d+\s+\S+\s+(\S+)\s+\S+\s+(\S+)\s+(.+)$"
)

# Section verrous de `dumpsys power` : Wake Locks: size=N puis lignes.
MOTIF_NB_WAKELOCKS = re.compile(r"Wake Locks:\s*size=(\d+)")
MOTIF_WAKELOCK = re.compile(r"^\s*\S*_WAKE_LOCK\s+'([^']+)'")


def parse_top(texte):
    """Parse `top -n 1` en [(pid, cpu, rss, uid, nom)]. Fonction pure.

    Trie par CPU decroissant (les valeurs avec % sont converties).
    """
    processus = []
    if not texte:
        return processus
    for ligne in texte.splitlines():
        trouve = MOTIF_TOP.match(ligne.rstrip())
        if not trouve:
            continue
        pid, cpu, _etat, rss, uid, nom = trouve.groups()
        try:
            cpu_val = float(cpu.rstrip("%"))
        except ValueError:
            cpu_val = 0.0
        processus.append((pid, cpu_val, rss, uid, nom.strip()[:60]))
    processus.sort(key=lambda p: p[1], reverse=True)
    return processus


def formater_processus(processus, limite):
    """Texte de reponse pour root_lister_processus. Fonction pure."""
    if not processus:
        return "Processus illisibles pour le moment."
    details = ", ".join(
        f"{nom} ({cpu:.0f} % CPU)" for _p, cpu, _r, _u, nom in processus[:limite]
    )
    return f"Processus gourmands : {details}."


def parse_wakelocks(texte):
    """Parse les verrous de `dumpsys power`. Fonction pure.

    Renvoie (nombre_annonce, [noms]).
    """
    if not texte:
        return 0, []
    annonce = 0
    trouve = MOTIF_NB_WAKELOCKS.search(texte)
    if trouve:
        try:
            annonce = int(trouve.group(1))
        except ValueError:
            annonce = 0
    noms = []
    for ligne in texte.splitlines():
        verrou = MOTIF_WAKELOCK.match(ligne)
        if verrou:
            noms.append(verrou.group(1).strip()[:80])
    return annonce, noms


def formater_wakelocks(annonce, noms, limite=10):
    """Texte de reponse pour root_lire_wakelocks. Fonction pure."""
    if annonce == 0 and not noms:
        return "Aucun verrou de reveil actif, le telephone dort bien."
    details = ", ".join(noms[:limite]) if noms else "noms illisibles"
    return (
        f"{annonce or len(noms)} verrou(s) de reveil actif(s) : "
        f"{details}."
    )


@mcp_diagnostic.tool()
def root_lister_processus(limite: int = 10) -> str:
    """Liste les processus qui utilisent le plus le CPU.

    limite : lignes affichees (1 a 30, 10 par defaut). Lecture seule
    via su (root voit tous les processus), ne modifie rien.
    Non teste sur appareil roote.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 30."
        )
    if not 1 <= limite <= 30:
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 30."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root("top -n 1", appareil_id)
    if not resultat["ok"]:
        return marquer_non_teste(f"Processus illisibles : {resultat['erreur']}")
    return marquer_non_teste(
        formater_processus(parse_top(resultat["sortie"]), limite)
    )


@mcp_diagnostic.tool()
def root_lire_wakelocks(limite: int = 10) -> str:
    """Lit les applis qui empechent le telephone de dormir.

    limite : verrous affiches (1 a 30, 10 par defaut). Lecture seule
    via su, ne modifie rien. Non teste sur appareil roote.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 30."
        )
    if not 1 <= limite <= 30:
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 30."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root("dumpsys power", appareil_id)
    if not resultat["ok"]:
        return marquer_non_teste(f"Verrous illisibles : {resultat['erreur']}")
    annonce, noms = parse_wakelocks(resultat["sortie"])
    return marquer_non_teste(formater_wakelocks(annonce, noms, limite))
