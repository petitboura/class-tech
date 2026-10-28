"""Test groupe des capteurs du telephone (palier 80 %, un seul outil).

tester_capteurs lit la liste reelle des capteurs via ADB (sensorservice)
et dit lesquels sont actifs en ce moment. Lecture seule, sans danger.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_shell, preparer_appel

# Ligne de la liste des capteurs : 0x....) Nom | reste.
MOTIF_CAPTEUR = re.compile(r"^0x[0-9a-fA-F]+\)\s*([^|]+?)\s*(?:\||$)")


def _nettoyer_nom_capteur(brut):
    """Nom de capteur sans la parenthese technique. Fonction pure."""
    nom = " ".join(brut.split())
    nom = re.sub(r"\s*\(.*\)$", "", nom).strip()
    return nom


def parse_sensorservice(texte):
    """Parse `dumpsys sensorservice` en {capteurs, actifs}. Fonction pure.

    capteurs : noms detectes. actifs : sous-ensemble actif en ce moment
    (vide si la section des actifs est absente sur cet appareil).
    """
    resultat = {"capteurs": [], "actifs": []}
    if not texte:
        return resultat
    coupure = re.search(r"^Active sensors.*$", texte, re.MULTILINE | re.IGNORECASE)
    if coupure:
        zone_liste, zone_actifs = texte[:coupure.start()], texte[coupure.start():]
    else:
        zone_liste, zone_actifs = texte, ""
    for ligne in zone_liste.splitlines():
        trouve = MOTIF_CAPTEUR.match(ligne.strip())
        if trouve:
            nom = _nettoyer_nom_capteur(trouve.group(1))
            if nom and nom not in resultat["capteurs"]:
                resultat["capteurs"].append(nom)
    for ligne in zone_actifs.splitlines():
        trouve = MOTIF_CAPTEUR.match(ligne.strip())
        if trouve:
            nom = _nettoyer_nom_capteur(trouve.group(1))
            if nom and nom not in resultat["actifs"]:
                resultat["actifs"].append(nom)
        else:
            for capteur in resultat["capteurs"]:
                if capteur and capteur in ligne and capteur not in resultat["actifs"]:
                    resultat["actifs"].append(capteur)
    return resultat


def formater_capteurs(donnees):
    """Texte de reponse pour le test capteurs. Fonction pure."""
    capteurs = donnees.get("capteurs", [])
    if not capteurs:
        return "Aucun capteur detecte (service capteurs illisible)."
    texte = f"{len(capteurs)} capteur(s) detecte(s) : " + ", ".join(capteurs) + "."
    actifs = donnees.get("actifs", [])
    if actifs:
        texte += f" Actifs en ce moment : {', '.join(actifs)}."
    else:
        texte += " Aucun en cours d'utilisation au moment du test."
    return texte


@mcp_diagnostic.tool()
def tester_capteurs() -> str:
    """Teste les capteurs en un passage : liste reelle et actifs du moment.

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("dumpsys sensorservice", appareil_id)
    if not resultat["ok"]:
        return f"Capteurs illisibles : {resultat['erreur']}"
    return formater_capteurs(parse_sensorservice(resultat["sortie"]))
