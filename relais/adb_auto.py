"""ADB automatique pour le relais PC Class-Tech.

Sur un PC neuf, ADB est absent et l'utilisateur ne doit rien
installer a la main. Ce module cherche ADB, et s'il manque, le
telecharge et le range seul dans un dossier local, sans aucun clic.
Reutilise trouver_adb du pont existant, sans le modifier.
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relais_config import lire_fichier_reglages  # noqa: E402

ENV_URL_ADB = "RELAIS_PC_URL_ADB"
ENV_DOSSIER_ADB = "RELAIS_PC_DOSSIER_ADB"

CLE_URL_ADB = "url_outils_adb"
CLE_DOSSIER_ADB = "dossier_outils_adb"

NOM_MARQUE_DOSSIER = "Class-Tech"
NOM_OUTILS_DOSSIER = "outils-adb"
NOM_ZIP_ADB = "outils-adb.zip"

DELAI_TELECHARGEMENT_S = 300
TAILLE_BLOC_OCTETS = 1024 * 256


def dossier_adb_par_defaut():
    """Dossier local range pour nos outils ADB, sous le profil Windows."""
    base = os.environ.get("LOCALAPPDATA", "").strip()
    if not base:
        base = os.path.expanduser("~")
    return os.path.join(base, NOM_MARQUE_DOSSIER, NOM_OUTILS_DOSSIER)


def dossier_adb_voulu():
    """Dossier voulu : reglages ou variable, sinon dossier par defaut."""
    fichier = lire_fichier_reglages()
    voulu = os.environ.get(ENV_DOSSIER_ADB, "").strip()
    if not voulu:
        voulu = str(fichier.get(CLE_DOSSIER_ADB, "") or "").strip()
    if voulu:
        return os.path.abspath(voulu)
    return dossier_adb_par_defaut()


def url_adb_voulue():
    """Adresse du zip ADB : reglages ou variable, vide si inconnue."""
    voulue = os.environ.get(ENV_URL_ADB, "").strip()
    if not voulue:
        fichier = lire_fichier_reglages()
        voulue = str(fichier.get(CLE_URL_ADB, "") or "").strip()
    return voulue


def _pont_adb():
    """Acces paresseux au pont ADB du depot, sans import circulaire."""
    from relais_config import preparer_imports

    preparer_imports()
    import core.pont_adb as pont

    return pont


def adb_deja_la():
    """Chemin ADB deja utilisable, ou None. Ne telecharge rien."""
    pont = _pont_adb()
    trouve = pont.trouver_adb()
    if trouve:
        return trouve
    candidat = os.path.join(
        dossier_adb_voulu(), "platform-tools", pont.NOM_EXECUTABLE_ADB
    )
    if os.path.isfile(candidat):
        return candidat
    return None


def _telecharger(url, destination):
    """Telecharge url vers destination. Renvoie une erreur ou None."""
    try:
        with urllib.request.urlopen(url, timeout=DELAI_TELECHARGEMENT_S) as reponse:
            with open(destination, "wb") as fichier:
                while True:
                    bloc = reponse.read(TAILLE_BLOC_OCTETS)
                    if not bloc:
                        return None
                    fichier.write(bloc)
    except Exception:
        return (
            "Telechargement impossible. Verifie la connexion internet "
            "puis relance le relais."
        )
    return None


def _verifier_adb(chemin_adb):
    """Vrai si le fichier ADB lance et repond. Ne touche pas au telephone."""
    try:
        termine = subprocess.run(
            [chemin_adb, "version"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return termine.returncode == 0


def installer_adb_auto():
    """Apporte ADB sur ce PC si besoin. Renvoie (chemin, erreur).

    Chemin renseigne quand ADB est utilisable. Erreur en francais
    simple quand rien n'a marche. Affiche la progression en console.
    """
    deja = adb_deja_la()
    if deja:
        return deja, None
    url = url_adb_voulue()
    if not url:
        return None, (
            "ADB est introuvable et aucune adresse de telechargement "
            "n'est reglee. Demande de l'aide pour ce PC."
        )
    dossier = dossier_adb_voulu()
    try:
        os.makedirs(dossier, exist_ok=True)
    except OSError:
        return None, (
            "Impossible de preparer le dossier des outils. "
            "Demande de l'aide pour ce PC."
        )
    print("Je prepare le lien vers le telephone, un petit moment...")
    zip_local = os.path.join(dossier, NOM_ZIP_ADB)
    erreur = _telecharger(url, zip_local)
    if erreur:
        return None, erreur
    try:
        with zipfile.ZipFile(zip_local) as archive:
            archive.extractall(dossier)
    except (OSError, zipfile.BadZipFile):
        return None, (
            "Telechargement abime. Relance le relais pour recommencer."
        )
    finally:
        try:
            os.remove(zip_local)
        except OSError:
            pass
    pont = _pont_adb()
    chemin_adb = os.path.join(
        dossier, "platform-tools", pont.NOM_EXECUTABLE_ADB
    )
    if not os.path.isfile(chemin_adb) or not _verifier_adb(chemin_adb):
        return None, (
            "Les outils recus ne marchent pas sur ce PC. "
            "Demande de l'aide pour ce PC."
        )
    print("Lien vers le telephone pret.")
    return chemin_adb, None


def rendre_adb_visible(chemin_adb):
    """Met le dossier ADB devant dans le PATH du programme."""
    if not chemin_adb:
        return
    dossier = os.path.dirname(os.path.abspath(chemin_adb))
    courant = os.environ.get("PATH", "")
    if dossier.lower() not in courant.lower().split(os.pathsep):
        os.environ["PATH"] = dossier + os.pathsep + courant


def preparer_adb():
    """Cherche ou installe ADB puis le rend visible. Renvoie (chemin, erreur)."""
    chemin, erreur = installer_adb_auto()
    if chemin:
        rendre_adb_visible(chemin)
    return chemin, erreur


def main():
    """Petit test manuel : prepare ADB et affiche le resultat."""
    chemin, erreur = preparer_adb()
    if chemin:
        print("ADB pret : " + chemin)
        return 0
    print(erreur or "ADB indisponible.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
