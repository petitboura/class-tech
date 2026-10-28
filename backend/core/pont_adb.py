"""Pont ADB vers le téléphone branché (palier 100 %, sans root).

Tous les outils de diagnostic du palier 100 % passent par ici pour
parler au téléphone : détection du programme adb, liste des téléphones
branchés, exécution des commandes. Aucune donnée utilisateur n'est
stockée, tout est lu en direct sur le téléphone.

Sans dépendance externe (stdlib uniquement), pour que les tests
tournent sans rien installer.
"""

from __future__ import annotations

import shutil
import subprocess

# Délai normal d'une commande adb. Les grosses lectures (liste complète
# des permissions) demandent un délai plus long, passé en paramètre.
DELAI_ADB_SECONDES = 25

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


def trouver_adb() -> str | None:
    """Chemin du programme adb, ou None s'il n'est pas installé."""
    return shutil.which("adb")


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


def executer_adb(
    adb: str,
    serie: str,
    morceaux: list[str],
    delai: int = DELAI_ADB_SECONDES,
) -> tuple[bool, str, str]:
    """Exécute `adb -s serie ...morceaux`, renvoie (réussi, sortie, erreur).

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
