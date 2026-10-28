"""Outils reseau du telephone : etat reseau et details wifi (palier 80 %).

Deux lectures reelles via ADB, sans danger :
- lire_etat_reseau : wifi ou donnees mobiles, mode avion.
- lire_infos_wifi : reseau wifi actuel, force du signal, debit.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_shell, preparer_appel

MOTIF_AGENT_RESEAU = re.compile(r"NetworkAgentInfo\s*\[\s*(\w+)", re.IGNORECASE)
MOTIF_SSID = re.compile(r'SSID:\s*"([^"]+)"')
MOTIF_RSSI = re.compile(r"RSSI:\s*(-?\d+)")
MOTIF_DEBIT = re.compile(r"Link speed:\s*([^\s,]+)")
MOTIF_FREQUENCE = re.compile(r"Frequency:\s*([^\s,]+)")
TRANSPORTS_CONNUS = {"WIFI": "wifi", "MOBILE": "donnees mobiles"}


def parse_connectivite(texte):
    """Parse `dumpsys connectivity` en {connectes, defaut}. Fonction pure.

    connectes : transports vus connectes (wifi, donnees mobiles...).
    defaut : transport par defaut ou "" si introuvable.
    """
    resultat = {"connectes": [], "defaut": ""}
    if not texte:
        return resultat
    blocs = re.split(r"NetworkAgentInfo", texte)
    for bloc in blocs[1:]:
        entete = bloc[:80]
        trouve = re.match(r"\s*\[\s*(\w+)", entete)
        if not trouve:
            continue
        transport = TRANSPORTS_CONNUS.get(trouve.group(1).upper(), trouve.group(1))
        corps = bloc[:2000]
        if not re.search(r"state\s*:\s*connected\b", corps, re.IGNORECASE):
            continue
        if transport not in resultat["connectes"]:
            resultat["connectes"].append(transport)
        if re.search(r"isDefaultNetwork\s*:\s*true", corps, re.IGNORECASE):
            resultat["defaut"] = transport
    if not resultat["defaut"] and len(resultat["connectes"]) == 1:
        resultat["defaut"] = resultat["connectes"][0]
    return resultat


def formater_reseau(connectivite, mode_avion):
    """Texte de reponse pour l'etat reseau. Fonction pure."""
    if mode_avion.strip() == "1":
        return "Mode avion active, aucun reseau."
    connectes = connectivite.get("connectes", [])
    if not connectes:
        return "Aucun reseau connecte (ni wifi ni donnees mobiles)."
    texte = "Reseau connecte : " + ", ".join(connectes) + "."
    if connectivite.get("defaut"):
        texte += f" Reseau utilise : {connectivite['defaut']}."
    return texte


def parse_wifi(texte):
    """Parse `dumpsys wifi` en {active, ssid, rssi, debit, frequence}.

    Fonction pure. ssid vaut "" si non connecte.
    """
    infos = {"active": False, "ssid": "", "rssi": "", "debit": "", "frequence": ""}
    if not texte:
        return infos
    if re.search(r"Wifi is enabled", texte):
        infos["active"] = True
    trouve = MOTIF_SSID.search(texte)
    if trouve and trouve.group(1) not in ("<unknown ssid>", "unknown"):
        infos["ssid"] = trouve.group(1)
    trouve = MOTIF_RSSI.search(texte)
    if trouve:
        infos["rssi"] = trouve.group(1)
    trouve = MOTIF_DEBIT.search(texte)
    if trouve:
        infos["debit"] = trouve.group(1)
    trouve = MOTIF_FREQUENCE.search(texte)
    if trouve:
        infos["frequence"] = trouve.group(1)
    return infos


def formater_wifi(infos):
    """Texte de reponse pour les details wifi. Fonction pure."""
    if not infos.get("active"):
        return "Wifi coupe sur le telephone."
    if not infos.get("ssid"):
        return "Wifi active mais non connecte a un reseau."
    morceaux = [f"reseau {infos['ssid']}"]
    if infos.get("rssi"):
        morceaux.append(f"signal {infos['rssi']} dBm")
    if infos.get("debit"):
        morceaux.append(f"debit {infos['debit']}")
    if infos.get("frequence"):
        morceaux.append(f"frequence {infos['frequence']}")
    return "Wifi : " + ", ".join(morceaux) + "."


@mcp_diagnostic.tool()
def lire_etat_reseau() -> str:
    """Lit l'etat reseau reel : wifi, donnees mobiles ou mode avion.

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("dumpsys connectivity", appareil_id)
    if not resultat["ok"]:
        return f"Etat reseau illisible : {resultat['erreur']}"
    avion = executer_shell("settings get global airplane_mode_on", appareil_id)
    mode_avion = avion["sortie"] if avion["ok"] else ""
    return formater_reseau(parse_connectivite(resultat["sortie"]), mode_avion)


@mcp_diagnostic.tool()
def lire_infos_wifi() -> str:
    """Lit le wifi actuel : reseau, force du signal, debit.

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("dumpsys wifi", appareil_id)
    if not resultat["ok"]:
        return f"Infos wifi illisibles : {resultat['erreur']}"
    return formater_wifi(parse_wifi(resultat["sortie"]))
