"""Outils batterie du telephone : etat et conso par appli (palier 80 %).

Deux lectures reelles via ADB, sans danger :
- lire_batterie : niveau, temperature, etat de charge, sante.
- lire_conso_batterie : estimation de la conso par UID/appli depuis
  les statistiques Android (batterystats).
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import DELAI_ADB_LENT_SECONDES, executer_shell, preparer_appel

# Codes Android de dumpsys battery, traduits en francais. Source unique.
ETATS_CHARGE_BATTERIE = {
    "1": "inconnu",
    "2": "en charge",
    "3": "en decharge",
    "4": "pas en charge",
    "5": "pleine",
}
SANTE_BATTERIE = {
    "1": "inconnue",
    "2": "bonne",
    "3": "surchauffe",
    "4": "morte",
    "5": "surtension",
    "6": "defaillance",
    "7": "froide",
}

# Ligne "Estimated power use" de batterystats, avec ou sans nom de paquet.
MOTIF_CONSO_UID = re.compile(
    r"^\s*Uid\s+(\S+?)(?:\s*\(([^)]+)\))?\s*:\s*([\d.]+)", re.MULTILINE
)
MOTIF_DRAIN_CALCULE = re.compile(
    r"Computed drain:\s*([\d.]+),\s*actual drain:\s*([\d.]+)"
)

# Ligne de `pm list packages -U` : package:nom uid:numero.
MOTIF_PAQUET_UID = re.compile(r"^package:(\S+)\s+uid:(\d+)", re.MULTILINE)


def parse_dumpsys_battery(texte):
    """Parse `dumpsys battery` en dictionnaire. Fonction pure."""
    infos = {}
    if not texte:
        return infos
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if ":" not in ligne:
            continue
        cle, _, valeur = ligne.partition(":")
        infos[cle.strip()] = valeur.strip()
    return infos


def formater_batterie(infos):
    """Texte de reponse pour l'etat batterie. Fonction pure."""
    if not infos:
        return "Etat batterie illisible pour le moment."
    morceaux = []
    niveau = infos.get("level", "")
    if niveau:
        morceaux.append(f"niveau {niveau} %")
    morceaux.append(f"etat {ETATS_CHARGE_BATTERIE.get(infos.get('status', ''), 'inconnu')}")
    morceaux.append(f"sante {SANTE_BATTERIE.get(infos.get('health', ''), 'inconnue')}")
    brut_temperature = infos.get("temperature", "")
    try:
        morceaux.append(f"temperature {int(brut_temperature) / 10:.1f} C")
    except (TypeError, ValueError):
        pass
    tension = infos.get("voltage", "")
    if tension:
        morceaux.append(f"tension {tension} mV")
    sources = [nom for cle, nom in
               (("AC powered", "secteur"), ("USB powered", "USB"), ("Wireless powered", "sans fil"))
               if infos.get(cle, "").lower() == "true"]
    if sources:
        morceaux.append("alimente par " + ", ".join(sources))
    technologie = infos.get("technology", "")
    if technologie:
        morceaux.append(f"technologie {technologie}")
    return "Batterie : " + ", ".join(morceaux) + "."


def parse_conso_batterystats(texte):
    """Parse la section conso estimee de batterystats. Fonction pure.

    Renvoie (lignes, drain) avec lignes = [(uid, paquet_ou_vide, mah)]
    triees par conso decroissante, et drain = (calcule, reel) ou None.
    """
    if not texte:
        return [], None
    debut = texte.find("Estimated power use")
    zone = texte[debut:] if debut >= 0 else texte
    lignes = []
    for correspondance in MOTIF_CONSO_UID.finditer(zone):
        uid, paquet, mah = correspondance.groups()
        try:
            lignes.append((uid, paquet or "", float(mah)))
        except ValueError:
            continue
    lignes.sort(key=lambda item: item[2], reverse=True)
    drain = None
    trouve = MOTIF_DRAIN_CALCULE.search(zone)
    if trouve:
        try:
            drain = (float(trouve.group(1)), float(trouve.group(2)))
        except ValueError:
            drain = None
    return lignes, drain


def parse_paquets_uid(texte):
    """Parse `pm list packages -U` en {uid: [paquets]}. Fonction pure."""
    table = {}
    if not texte:
        return table
    for correspondance in MOTIF_PAQUET_UID.finditer(texte):
        paquet, uid = correspondance.group(1), correspondance.group(2)
        table.setdefault(uid, [])
        if paquet not in table[uid]:
            table[uid].append(paquet)
    return table


def uid_android_vers_nombre(uid):
    """Convertit u0a123 en numero systeme 10123. Fonction pure, None sinon."""
    if not uid:
        return None
    trouve = re.match(r"^u(\d+)a(\d+)$", uid)
    if not trouve:
        return None
    try:
        return str(int(trouve.group(1)) * 100000 + 10000 + int(trouve.group(2)))
    except ValueError:
        return None


def formater_conso(lignes, table_uid, drain, limite=10):
    """Texte de reponse pour la conso par appli. Fonction pure."""
    if not lignes:
        return (
            "Statistiques de conso indisponibles (compteurs remis a zero "
            "ou version Android qui ne les expose pas)."
        )
    morceaux = []
    for uid, paquet, mah in lignes[:limite]:
        noms = [paquet] if paquet else []
        if not noms:
            numero = uid_android_vers_nombre(uid)
            noms = table_uid.get(numero, []) if numero else []
        if not noms:
            noms = table_uid.get(uid, [])
        etiquette = ", ".join(noms) if noms else f"UID {uid}"
        morceaux.append(f"{etiquette} ({mah:.1f} mAh)")
    texte = "Conso estimee par appli : " + ", ".join(morceaux) + "."
    if drain:
        texte += f" Total calcule {drain[0]:.0f} mAh, reel {drain[1]:.0f} mAh."
    return texte


@mcp_diagnostic.tool()
def lire_batterie() -> str:
    """Lit l'etat reel de la batterie : niveau, temperature, charge, sante.

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("dumpsys battery", appareil_id)
    if not resultat["ok"]:
        return f"Batterie illisible : {resultat['erreur']}"
    return formater_batterie(parse_dumpsys_battery(resultat["sortie"]))


@mcp_diagnostic.tool()
def lire_conso_batterie(limite: int = 10) -> str:
    """Estime quelles applis consomment le plus de batterie.

    Lit les statistiques Android (batterystats) et rend les plus
    gourmandes en premier. Lecture seule, ne modifie rien.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return "Erreur : limite invalide, donne un nombre entre 1 et 30."
    if not 1 <= limite <= 30:
        return "Erreur : limite invalide, donne un nombre entre 1 et 30."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("dumpsys batterystats", appareil_id, delai=DELAI_ADB_LENT_SECONDES)
    if not resultat["ok"]:
        return f"Conso batterie illisible : {resultat['erreur']}"
    lignes, drain = parse_conso_batterystats(resultat["sortie"])
    table_uid = {}
    if lignes and not lignes[0][1]:
        mapping = executer_shell("pm list packages -U", appareil_id)
        if mapping["ok"]:
            table_uid = parse_paquets_uid(mapping["sortie"])
    return formater_conso(lignes, table_uid, drain, limite)
