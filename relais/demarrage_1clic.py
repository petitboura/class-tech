"""Demarrage en 1 clic du relais PC Class-Tech.

Point d'entree de l'exe : double clic, tout est automatique.
Reutilise le relais existant tel quel (reglages, serveur, outils).
Etapes : reglages, ADB auto, serveur local, page de sante ouverte.
"""

from __future__ import annotations

import os
import sys
import json
import socket
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
PORT_SECOURS_FIN = 10  # 8765 -> 8775 max


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


def port_libre(hote, port):
    """Vrai si on peut écouter sur hote:port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((hote, port))
        s.close()
        return True
    except OSError:
        try:
            s.close()
        except Exception:
            pass
        return False


def choisir_port(hote, port_prefere):
    """Port préféré s'il est libre, sinon le suivant jusqu'à +10."""
    for decalage in range(PORT_SECOURS_FIN + 1):
        port = port_prefere + decalage
        if 1 <= port <= 65535 and port_libre(hote, port):
            return port
    return port_prefere


def memoriser_port(port_effectif):
    """Écrit le port effectif pour que l'appli le retrouve."""
    try:
        from relais_config import chemin_fichier_reglages as _chemin
        fichier = _chemin()
        try:
            with open(fichier, encoding="utf-8") as f:
                donnees = json.load(f)
        except Exception:
            donnees = {}
        if not isinstance(donnees, dict):
            donnees = {}
        donnees["port"] = port_effectif
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


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

    port_effectif = choisir_port(reglages["hote"], reglages["port"])
    if port_effectif != reglages["port"]:
        print(f"Port {reglages['port']} pris, bascule sur {port_effectif}.")
        memoriser_port(port_effectif)
    base = adresse_base({**reglages, "port": port_effectif})
    page_sante = base + "/relais/sante"
    print("Relais PC Class-Tech en route sur " + base)
    print("Page de sante : " + page_sante)
    print("Branche le telephone en USB puis lance un diagnostic.")
    print("Pour arreter, ferme cette fenetre.")
    ouvrir_page_plus_tard(page_sante, delai_ouverture_page())
    try:
        uvicorn.run(app, host=reglages["hote"], port=port_effectif)
    except KeyboardInterrupt:
        print("Relais arrete, a bientot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
