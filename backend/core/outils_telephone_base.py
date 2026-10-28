"""Outil de base du pont PC vers telephone : detection et infos (palier 80 %).

Premier outil a appeler avant tout diagnostic : il dit si un telephone
est branché et pret, et donne son modele et sa version d'Android.
Lecture seule, sans danger.
"""

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_shell, resumer_liaison

# Proprietes Android lues pour presenter le telephone. Source unique.
CLES_INFOS_APPAREIL = {
    "ro.product.manufacturer": "fabricant",
    "ro.product.brand": "marque",
    "ro.product.model": "modele",
    "ro.build.version.release": "android",
    "ro.build.version.sdk": "sdk",
    "ro.build.version.security_patch": "patch_securite",
    "ro.build.id": "compilation",
}


def parse_getprop(texte):
    """Parse la sortie de `getprop` en dictionnaire. Fonction pure."""
    infos = {}
    if not texte:
        return infos
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne.startswith("[") or "]:" not in ligne:
            continue
        cle, _, valeur = ligne[1:].partition("]: [")
        valeur = valeur[:-1] if valeur.endswith("]") else valeur
        if cle:
            infos[cle] = valeur
    return infos


def formater_detection(liaison, infos):
    """Texte de reponse a partir de la liaison et des infos. Fonction pure."""
    if not liaison.get("pret"):
        return liaison.get("message") or "Telephone indisponible."
    lignes = []
    choisi = liaison.get("appareil_choisi") or {}
    if choisi.get("id"):
        lignes.append(f"Telephone detecte ({choisi['id']}).")
    fabricant = infos.get("ro.product.manufacturer", "")
    marque = infos.get("ro.product.brand", "")
    modele = infos.get("ro.product.model", "")
    nom = " ".join(p for p in (fabricant, modele or marque) if p).strip()
    if nom:
        lignes.append(f"Modele : {nom}.")
    android = infos.get("ro.build.version.release", "")
    sdk = infos.get("ro.build.version.sdk", "")
    if android:
        detail = f"Android {android}"
        if sdk:
            detail += f" (SDK {sdk})"
        lignes.append(detail + ".")
    patch = infos.get("ro.build.version.security_patch", "")
    if patch:
        lignes.append(f"Correctif de securite : {patch}.")
    autres = [a for a in liaison.get("appareils", []) if a.get("id") != choisi.get("id")]
    if autres:
        lignes.append(f"{len(autres)} autre appareil vu, diagnostic sur le premier pret.")
    if not lignes:
        return "Telephone detecte et pret."
    return " ".join(lignes)


def texte_detection(liaison, sortie_getprop):
    """Assemble la reponse complete. Fonction pure, testee sans telephone."""
    return formater_detection(liaison, parse_getprop(sortie_getprop or ""))


@mcp_diagnostic.tool()
def detecter_telephone() -> str:
    """Detecte le telephone branché en USB et donne son modele et sa version.

    A appeler en premier avant tout diagnostic. Lecture seule : ne
    modifie rien sur le telephone ni sur le PC.
    """
    liaison = resumer_liaison()
    if not liaison["pret"]:
        return liaison["message"]
    resultat = executer_shell("getprop", liaison["appareil_choisi"]["id"])
    if not resultat["ok"]:
        base = formater_detection(liaison, {})
        return base + " Details du modele illisibles pour le moment."
    return texte_detection(liaison, resultat["sortie"])
