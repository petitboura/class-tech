"""Construit l'exe 1 clic du relais (outil pour Bourama, pas pour l'utilisateur).

Usage depuis la racine du depot : python relais/construire_exe.py
Demande PyInstaller installe (pip install pyinstaller). Le resultat
est un seul fichier exe dans dist-1clic, a telecharger et double
cliquer sur le PC de l'utilisateur.
"""

from __future__ import annotations

import os
import subprocess
import sys

NOM_EXE = "Relais-Class-Tech"
DOSSIER_DIST = "dist-1clic"
DOSSIER_TRAVAIL = "build-1clic"


def racine_depot():
    """Racine du depot, parent du dossier relais."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    """Lance PyInstaller avec les bons chemins, affiche le resultat."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller manque : lance pip install pyinstaller puis recommence.")
        return 1
    racine = racine_depot()
    entree = os.path.join(racine, "relais", "demarrage_1clic.py")
    donnees = os.path.join(racine, "relais", "reglages.json")
    commande = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        "--name",
        NOM_EXE,
        "--paths",
        os.path.join(racine, "relais"),
        "--paths",
        os.path.join(racine, "backend"),
        "--add-data",
        donnees + os.pathsep + ".",
        "--distpath",
        os.path.join(racine, DOSSIER_DIST),
        "--workpath",
        os.path.join(racine, DOSSIER_TRAVAIL),
        "--specpath",
        os.path.join(racine, DOSSIER_TRAVAIL),
        entree,
    ]
    termine = subprocess.run(commande, cwd=racine)
    if termine.returncode != 0:
        print("La construction a echoue, relis les messages ci dessus.")
        return 1
    exe = os.path.join(racine, DOSSIER_DIST, NOM_EXE + ".exe")
    if os.path.isfile(exe):
        taille_mo = os.path.getsize(exe) / (1024 * 1024)
        print("Exe pret : " + exe + " (" + str(round(taille_mo, 1)) + " Mo).")
        return 0
    print("Exe introuvable apres construction, dossier : " + DOSSIER_DIST + ".")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
