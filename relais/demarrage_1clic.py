"""Demarrage en 1 clic du relais PC Class-Tech.

Point d'entree de l'exe : double clic, tout est automatique.
Reutilise le relais existant tel quel (reglages, serveur, outils).
Etapes : reglages, ADB auto, serveur local, page de sante ouverte.
"""

from __future__ import annotations

import os
import sys
import threading
import webbrowser

if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn  # noqa: E402

from adb_auto import preparer_adb  # noqa: E402
from relais_config import (  # noqa: E402
    adresse_base,
    appliquer_chemin_adb,
    charger_reglages,
    lire_fichier_reglages,
    preparer_imports,
    valider_reglages,
)

ENV_DELAI_PAGE = "RELAIS_PC_DELAI_PAGE"
CLE_DELAI_PAGE = "delai_ouverture_page_s"
DELAI_PAGE_SECOURS_S = 3


def delai_ouverture_page():
    """Secondes avant d'ouvrir la page de sante, depuis les reglages."""
    brut = os.environ.get(ENV_DELAI_PAGE, "").strip()
    if not brut:
        fichier = lire_fichier_reglages()
        brut = str(fichier.get(CLE_DELAI_PAGE, "") or "").strip()
    try:
        delai = int(brut)
    except (TypeError, ValueError):
        return DELAI_PAGE_SECOURS_S
    if delai < 0:
        return DELAI_PAGE_SECOURS_S
    return delai


def ouvrir_page_plus_tard(url, delai):
    """Ouvre la page de sante dans le navigateur apres le delai."""

    def _ouvrir():
        try:
            webbrowser.open(url)
        except Exception:
            pass

    minuteur = threading.Timer(delai, _ouvrir)
    minuteur.daemon = True
    minuteur.start()


def attendre_avant_fermeture():
    """Laisse la fenetre lisible quand on a double clique."""
    try:
        input("Appuie sur Entree pour fermer cette fenetre.")
    except (EOFError, OSError):
        pass


def main():
    """Demarre tout : ADB, relais, page de sante."""
    reglages = charger_reglages()
    erreur = valider_reglages(reglages)
    if erreur:
        print(erreur)
        attendre_avant_fermeture()
        return 1
    chemin_adb, erreur_adb = preparer_adb()
    if chemin_adb:
        print("Lien telephone : pret.")
    else:
        print(erreur_adb or "Lien telephone : pas pret pour le moment.")
        print("Le relais demarre quand meme, la page dira quoi faire.")
    erreur = appliquer_chemin_adb(reglages)
    if erreur:
        print(erreur)
        attendre_avant_fermeture()
        return 1
    preparer_imports()

    from serveur_relais import app

    base = adresse_base(reglages)
    page_sante = base + "/relais/sante"
    print("Relais PC Class-Tech en route sur " + base)
    print("Page de sante : " + page_sante)
    print("Branche le telephone en USB puis lance un diagnostic.")
    print("Pour arreter, ferme cette fenetre.")
    ouvrir_page_plus_tard(page_sante, delai_ouverture_page())
    try:
        uvicorn.run(app, host=reglages["hote"], port=reglages["port"])
    except KeyboardInterrupt:
        print("Relais arrete, a bientot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
