"""Réglages du relais PC Class-Tech.

L'adresse, le port, le délai et le chemin ADB viennent du fichier
reglages.json placé à côté de ce script. Chaque valeur peut aussi
être forcée par une variable d'environnement. Rien de tout cela
n'est écrit en dur dans le code.
"""

from __future__ import annotations

import json
import os
import sys

NOM_FICHIER_REGLAGES = "reglages.json"

ENV_HOTE = "RELAIS_PC_HOTE"
ENV_PORT = "RELAIS_PC_PORT"
ENV_DELAI = "RELAIS_PC_DELAI"
ENV_ADB = "RELAIS_PC_ADB"


def dossier_relais():
    """Dossier qui contient ce script, donc le dossier relais."""
    return os.path.dirname(os.path.abspath(__file__))


def racine_depot():
    """Racine du dépôt cloné, parent du dossier relais."""
    return os.path.dirname(dossier_relais())


def dossier_backend():
    """Dossier backend du dépôt cloné."""
    return os.path.join(racine_depot(), "backend")


def chemin_fichier_reglages():
    """Chemin complet du fichier reglages.json livré avec le relais."""
    return os.path.join(dossier_relais(), NOM_FICHIER_REGLAGES)


def lire_fichier_reglages():
    """Contenu du fichier de réglages, dictionnaire vide si illisible."""
    try:
        with open(chemin_fichier_reglages(), encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except (OSError, ValueError):
        return {}
    return donnees if isinstance(donnees, dict) else {}


def _entier(valeur):
    """Entier tiré d'une valeur, ou 0 si impossible. Fonction utilitaire."""
    try:
        return int(str(valeur).strip())
    except (TypeError, ValueError):
        return 0


def charger_reglages():
    """Réglages effectifs : fichier puis variables d'environnement.

    Renvoie un dictionnaire avec hote, port, delai_lancement_s et
    chemin_adb. Les variables d'environnement gagnent sur le fichier.
    chemin_adb vide veut dire recherche auto par le pont ADB.
    """
    fichier = lire_fichier_reglages()
    hote = os.environ.get(ENV_HOTE, "").strip()
    if not hote:
        hote = str(fichier.get("hote", "")).strip()
    port = _entier(os.environ.get(ENV_PORT, ""))
    if not port:
        port = _entier(fichier.get("port"))
    delai = _entier(os.environ.get(ENV_DELAI, ""))
    if not delai:
        delai = _entier(fichier.get("delai_lancement_s"))
    adb = os.environ.get(ENV_ADB, "").strip()
    if not adb:
        adb = str(fichier.get("chemin_adb", "")).strip()
    return {
        "hote": hote,
        "port": port,
        "delai_lancement_s": delai,
        "chemin_adb": adb,
    }


def valider_reglages(reglages):
    """Message d'erreur en français, ou None si tout est bon."""
    if not reglages.get("hote"):
        return "Réglage manquant : renseigne hote dans relais/reglages.json."
    port = reglages.get("port", 0)
    if not isinstance(port, int) or not 1 <= port <= 65535:
        return (
            "Réglage invalide : port doit être un nombre entre 1 et 65535 "
            "dans relais/reglages.json."
        )
    delai = reglages.get("delai_lancement_s", 0)
    if not isinstance(delai, int) or delai < 1:
        return (
            "Réglage invalide : delai_lancement_s doit valoir au moins 1 "
            "dans relais/reglages.json."
        )
    return None


def appliquer_chemin_adb(reglages):
    """Rend le chemin ADB des réglages visible du pont, si renseigné.

    Vide : rien à faire, le pont cherche seul. Renseigné : le dossier
    passe devant dans le PATH du programme. Renvoie un message
    d'erreur en français, ou None si tout est bon.
    """
    chemin = (reglages.get("chemin_adb") or "").strip()
    if not chemin:
        return None
    if not os.path.isfile(chemin):
        return (
            "Chemin ADB invalide dans les réglages : fichier introuvable. "
            "Vide chemin_adb pour la recherche auto."
        )
    dossier = os.path.dirname(os.path.abspath(chemin))
    os.environ["PATH"] = dossier + os.pathsep + os.environ.get("PATH", "")
    return None


def preparer_imports():
    """Ajoute le dossier backend aux imports, pour réutiliser le dépôt."""
    dossier = dossier_backend()
    if dossier not in sys.path:
        sys.path.insert(0, dossier)


def adresse_base(reglages):
    """Adresse locale du relais, pour l'affichage et la vérification."""
    return "http://" + reglages["hote"] + ":" + str(reglages["port"])
