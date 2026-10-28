"""Outils iPhone portes : detection, batterie, stockage, version systeme.

Premiers outils iOS en lecture seule via le pont libimobiledevice
(voir core/pont_ios.py). Chaque outil commence par preparer_appel_ios()
et renvoie un texte en francais simple. Aucune ecriture, aucun reglage
change, jamais de jailbreak.
"""

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_ios import (
    DOMAINE_BATTERIE,
    DOMAINE_STOCKAGE,
    erreur_courte_ios,
    executer_ios,
    lire_domaine,
    parse_ideviceinfo,
    resumer_liaison_ios,
)

# Seuil d'alerte stockage presque plein, en pour cent. Source unique.
SEUIL_STOCKAGE_PLEIN_PCT = 90


def formater_detection_ios(liaison, infos):
    """Texte de reponse a partir de la liaison et des infos. Fonction pure."""
    if not liaison.get("pret"):
        return liaison.get("message") or "iPhone indisponible."
    lignes = []
    if liaison.get("udid_choisi"):
        lignes.append("iPhone detecte et pret.")
    nom = infos.get("DeviceName", "")
    if nom:
        lignes.append(f"Nom : {nom}.")
    produit = infos.get("ProductName", "")
    modele = infos.get("ModelNumber", "")
    etiquette = " ".join(p for p in (produit, modele) if p).strip()
    if etiquette:
        lignes.append(f"Modele : {etiquette}.")
    ios = infos.get("ProductVersion", "")
    compilation = infos.get("BuildVersion", "")
    if ios:
        detail = f"iOS {ios}"
        if compilation:
            detail += f" (compilation {compilation})"
        lignes.append(detail + ".")
    autres = [u for u in liaison.get("udids", []) if u != liaison.get("udid_choisi")]
    if autres:
        lignes.append(f"{len(autres)} autre iPhone vu, diagnostic sur le premier pret.")
    if not lignes:
        return "iPhone detecte et pret."
    return " ".join(lignes)


def texte_detection_ios(liaison, sortie_ideviceinfo):
    """Assemble la reponse complete. Fonction pure, testee sans telephone."""
    return formater_detection_ios(liaison, parse_ideviceinfo(sortie_ideviceinfo or ""))


def formater_batterie_ios(infos):
    """Texte de reponse pour l'etat batterie iPhone. Fonction pure."""
    niveau = (infos.get("BatteryCurrentCapacity", "") or "").strip()
    if not niveau:
        return "Etat batterie illisible pour le moment."
    morceaux = [f"niveau {niveau} %"]
    charge = (infos.get("BatteryIsCharging", "") or "").strip().lower()
    if charge == "true":
        morceaux.append("en charge")
    elif charge == "false":
        morceaux.append("pas en charge")
    return "Batterie iPhone : " + ", ".join(morceaux) + "."


def octets_vers_go(texte):
    """Convertit un nombre d'octets en Go. Fonction pure, None si illisible."""
    try:
        return int(str(texte or "").strip()) / (1024 ** 3)
    except (TypeError, ValueError):
        return None


def formater_stockage_ios(infos):
    """Texte de reponse pour le stockage iPhone. Fonction pure."""
    total = octets_vers_go(infos.get("TotalDiskCapacity", ""))
    disponible = octets_vers_go(infos.get("AmountDataAvailable", ""))
    if total is None or disponible is None or total <= 0:
        return "Espace disque illisible pour le moment."
    utilise_pct = round((total - disponible) / total * 100)
    texte = (
        f"Stockage iPhone : {disponible:.1f} Go libres sur {total:.1f} Go "
        f"({utilise_pct} % utilises)."
    )
    if utilise_pct >= SEUIL_STOCKAGE_PLEIN_PCT:
        texte += " Stockage presque plein."
    return texte


def formater_version_ios(infos):
    """Texte de reponse pour la version iOS. Fonction pure."""
    ios = infos.get("ProductVersion", "")
    compilation = infos.get("BuildVersion", "")
    if not ios and not compilation:
        return "Version systeme illisible pour le moment."
    morceaux = []
    if ios:
        morceaux.append(f"iOS {ios}")
    if compilation:
        morceaux.append(f"compilation {compilation}")
    return "Systeme : " + ", ".join(morceaux) + "."


@mcp_diagnostic.tool()
def detecter_iphone() -> str:
    """Detecte l'iPhone branché en USB et donne son nom, modele et version iOS.

    A appeler en premier avant tout diagnostic iPhone. Lecture seule :
    ne modifie rien sur l'iPhone ni sur le PC.
    """
    liaison = resumer_liaison_ios()
    if not liaison["pret"]:
        return liaison["message"]
    resultat = executer_ios("infos", [], udid=liaison["udid_choisi"])
    if not resultat["ok"]:
        base = formater_detection_ios(liaison, {})
        return base + " Details du modele illisibles pour le moment."
    return texte_detection_ios(liaison, resultat["sortie"])


@mcp_diagnostic.tool()
def lire_batterie_iphone() -> str:
    """Lit le niveau reel de la batterie de l'iPhone et l'etat de charge.

    Lecture seule via libimobiledevice, ne modifie rien sur l'iPhone.
    """
    liaison = resumer_liaison_ios()
    if not liaison["pret"]:
        return liaison["message"]
    resultat = lire_domaine(liaison["udid_choisi"], DOMAINE_BATTERIE)
    if not resultat["ok"]:
        return f"Batterie illisible : {erreur_courte_ios(resultat['erreur'])}"
    return formater_batterie_ios(parse_ideviceinfo(resultat["sortie"]))


@mcp_diagnostic.tool()
def lire_stockage_iphone() -> str:
    """Lit l'espace disque reel de l'iPhone : total, libre, utilise.

    Lecture seule via libimobiledevice, ne modifie rien sur l'iPhone.
    """
    liaison = resumer_liaison_ios()
    if not liaison["pret"]:
        return liaison["message"]
    resultat = lire_domaine(liaison["udid_choisi"], DOMAINE_STOCKAGE)
    if not resultat["ok"]:
        return f"Stockage illisible : {erreur_courte_ios(resultat['erreur'])}"
    return formater_stockage_ios(parse_ideviceinfo(resultat["sortie"]))


@mcp_diagnostic.tool()
def lire_version_iphone() -> str:
    """Lit la version iOS et la compilation de l'iPhone branché.

    Lecture seule via libimobiledevice, ne modifie rien sur l'iPhone.
    """
    liaison = resumer_liaison_ios()
    if not liaison["pret"]:
        return liaison["message"]
    resultat = executer_ios("infos", [], udid=liaison["udid_choisi"])
    if not resultat["ok"]:
        return f"Version systeme illisible : {erreur_courte_ios(resultat['erreur'])}"
    return formater_version_ios(parse_ideviceinfo(resultat["sortie"]))
