"""Outils root : batterie brute et temperatures (palier root).

Deux lectures reelles via `su -c`, une correction :
- root_lire_batterie_brute : tensions, courant, compteur, cycles.
- root_lire_temperatures : capteurs thermiques du telephone.
- root_reinitialiser_stats_batterie : remet les compteurs a zero.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import erreur_courte
from core.pont_root import executer_root, marquer_non_teste, preparer_root

# Fichiers lus dans /sys/class/power_supply/battery en un seul appel.
# status dit le sens reel (charge, decharge) : le signe de current_now
# est inverse sur certains modeles, on ne s'y fie jamais seul.
FICHIERS_BATTERIE = (
    "voltage_now",
    "current_now",
    "temp",
    "capacity",
    "charge_counter",
    "charge_full",
    "charge_full_design",
    "cycle_count",
    "health",
    "technology",
    "present",
    "status",
)

# Plages brutes plausibles (unites standard du noyau). Hors plage :
# valeur affichee brute avec mention, jamais convertie a l'aveugle
# (audit risques : unites parfois differentes selon le modele).
PLAGE_TEMP_DIXIEMES = (-300, 1200)
PLAGE_TENSION_MICROVOLTS = (2000000, 15000000)
PLAGE_COURANT_MICROAMPERES = (-30000000, 30000000)
PLAGE_CHARGE_MICROAMPERES_HEURE = (0, 100000000)

# Plage brute plausible des zones thermiques (milliemes de degre).
PLAGE_THERM_MILLIEMES = (-50000, 150000)

# Ligne `grep -H '' f1 f2` : nom:contenu.
MOTIF_SYSFS = re.compile(r"^([^:]+):(.*)$")

# Sens de charge d'apres le fichier status (minuscules).
SENS_PAR_STATUS = {
    "charging": "charge",
    "discharging": "decharge",
    "full": "pleine",
    "not charging": "pas en charge",
}


def parse_sysfs_dict(texte):
    """Parse des lignes nom:valeur en dictionnaire. Fonction pure."""
    valeurs = {}
    if not texte:
        return valeurs
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        trouve = MOTIF_SYSFS.match(ligne)
        if trouve:
            valeurs[trouve.group(1).strip()] = trouve.group(2).strip()
    return valeurs


def _entier(valeurs, cle):
    try:
        return int(valeurs.get(cle, ""))
    except (TypeError, ValueError):
        return None


def _plausible(valeur, mini, maxi):
    """Vrai si la valeur brute est dans la plage standard. Pure."""
    return valeur is not None and mini <= valeur <= maxi


def formater_batterie_brute(valeurs):
    """Texte de reponse pour root_lire_batterie_brute. Fonction pure."""
    if not valeurs:
        return "Batterie brute illisible pour le moment."
    morceaux = []
    tension = _entier(valeurs, "voltage_now")
    if tension is not None:
        if _plausible(tension, *PLAGE_TENSION_MICROVOLTS):
            morceaux.append(f"tension {tension / 1000000:.2f} V")
        else:
            morceaux.append(f"tension brute {tension} (unite inhabituelle)")
    courant = _entier(valeurs, "current_now")
    status = (valeurs.get("status", "") or "").strip().lower()
    if courant is not None:
        if _plausible(courant, *PLAGE_COURANT_MICROAMPERES):
            sens = SENS_PAR_STATUS.get(status)
            if sens is None:
                sens = "charge" if courant > 0 else "decharge"
                sens += " probable"
            morceaux.append(f"courant {abs(courant) // 1000} mA ({sens})")
        else:
            morceaux.append(f"courant brut {courant} (unite inhabituelle)")
    elif status in SENS_PAR_STATUS:
        morceaux.append(f"etat {SENS_PAR_STATUS[status]}")
    temp = _entier(valeurs, "temp")
    if temp is not None:
        if _plausible(temp, *PLAGE_TEMP_DIXIEMES):
            morceaux.append(f"temperature {temp / 10:.1f} C")
        else:
            morceaux.append(f"temperature brute {temp} (unite inhabituelle)")
    compteur = _entier(valeurs, "charge_counter")
    pleine = _entier(valeurs, "charge_full")
    origine = _entier(valeurs, "charge_full_design")
    if compteur is not None:
        if _plausible(compteur, *PLAGE_CHARGE_MICROAMPERES_HEURE):
            morceaux.append(f"contenu {compteur // 1000} mAh")
        else:
            morceaux.append(f"contenu brut {compteur} (unite inhabituelle)")
    if pleine and origine:
        usure = 100 * pleine / origine
        morceaux.append(f"sante {usure:.0f} % de la capacite d'origine")
    elif pleine:
        morceaux.append(f"pleine a {pleine // 1000} mAh")
    cycles = _entier(valeurs, "cycle_count")
    if cycles is not None:
        morceaux.append(f"{cycles} cycles")
    capacite = valeurs.get("capacity", "")
    if capacite:
        morceaux.append(f"niveau {capacite} %")
    sante = valeurs.get("health", "")
    if sante:
        morceaux.append(f"etat {sante}")
    techno = valeurs.get("technology", "")
    if techno:
        morceaux.append(f"technologie {techno}")
    if not morceaux:
        return "Batterie brute illisible pour le moment."
    return "Batterie brute : " + ", ".join(morceaux) + "."


def parse_thermal(types_texte, temps_texte):
    """Joint types et temperatures par zone. Fonction pure.

    Renvoie [(zone, type, degres)] trie par temperature decroissante.
    Les valeurs hors plage plausible sont ignorees ici et comptees
    par compter_zones_sans_mesure (jamais silencieuses).
    """
    types = parse_sysfs_dict(types_texte)
    temps = parse_sysfs_dict(temps_texte)
    zones = []
    for chemin, nom in types.items():
        zone = chemin.rsplit("/", 1)[0] if "/" in chemin else chemin
        cle_temp = None
        for candidat in temps:
            if candidat.rsplit("/", 1)[0] == zone or candidat == zone:
                cle_temp = candidat
                break
        if cle_temp is None:
            continue
        try:
            brut = int(temps[cle_temp])
        except (TypeError, ValueError):
            continue
        if not _plausible(brut, *PLAGE_THERM_MILLIEMES):
            continue
        zones.append((zone.rsplit("/", 1)[-1], nom.strip(), brut / 1000))
    zones.sort(key=lambda z: z[2], reverse=True)
    return zones


def compter_zones_sans_mesure(types_texte, zones):
    """Zones declarees moins zones mesurees. Fonction pure.

    Compte les zones sans temperature jointe ou a valeur ecartee
    (unite inhabituelle), pour le dire dans la reponse.
    """
    if not types_texte:
        return 0
    declares = sum(
        1 for ligne in types_texte.splitlines()
        if ligne.strip() and ":" in ligne
    )
    return max(0, declares - len(zones))


def formater_temperatures(zones, limite=10, sans_mesure=0):
    """Texte de reponse pour root_lire_temperatures. Fonction pure."""
    if not zones:
        if sans_mesure:
            return (
                f"Temperatures illisibles pour le moment "
                f"({sans_mesure} capteur(s) sans mesure)."
            )
        return "Temperatures illisibles pour le moment."
    details = ", ".join(
        f"{nom} {degres:.1f} C" for _z, nom, degres in zones[:limite]
    )
    texte = f"Temperatures ({len(zones)} capteurs) : {details}."
    if sans_mesure:
        texte += f" {sans_mesure} capteur(s) sans mesure."
    return texte


@mcp_diagnostic.tool()
def root_lire_batterie_brute() -> str:
    """Lit les mesures brutes de la batterie (tension, courant, cycles).

    Lecture seule via su, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    fichiers = " ".join(FICHIERS_BATTERIE)
    resultat = executer_root(
        "cd /sys/class/power_supply/battery && "
        f"grep -H '' {fichiers} 2>/dev/null",
        appareil_id,
    )
    if not resultat["ok"]:
        return marquer_non_teste(
            f"Batterie brute illisible : {erreur_courte(resultat['erreur'])}"
        )
    return marquer_non_teste(
        formater_batterie_brute(parse_sysfs_dict(resultat["sortie"]))
    )


@mcp_diagnostic.tool()
def root_lire_temperatures(limite: int = 10) -> str:
    """Lit les capteurs de temperature du telephone, plus chauds d'abord.

    limite : capteurs affiches (1 a 30, 10 par defaut). Lecture seule
    via su, ne modifie rien. Non teste sur appareil roote.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 30."
        )
    if not 1 <= limite <= 30:
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 30."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    types = executer_root(
        "grep -H '' /sys/class/thermal/thermal_zone*/type 2>/dev/null",
        appareil_id,
    )
    temps = executer_root(
        "grep -H '' /sys/class/thermal/thermal_zone*/temp 2>/dev/null",
        appareil_id,
    )
    types_texte = types["sortie"] if types["ok"] else ""
    zones = parse_thermal(
        types_texte,
        temps["sortie"] if temps["ok"] else "",
    )
    return marquer_non_teste(formater_temperatures(
        zones, limite, compter_zones_sans_mesure(types_texte, zones)))


@mcp_diagnostic.tool()
def root_reinitialiser_stats_batterie() -> str:
    """Remet a zero les statistiques de batterie d'Android.

    Correction douce : efface les compteurs pour repartir sur des
    mesures propres. Ne touche ni aux applis ni aux donnees.
    Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root("dumpsys batterystats --reset", appareil_id)
    if not resultat["ok"]:
        return marquer_non_teste(
            f"Compteurs non remis a zero : {erreur_courte(resultat['erreur'])}"
        )
    return marquer_non_teste(
        "Statistiques de batterie remises a zero. Laisse passer "
        "quelques heures d'usage avant de juger la conso."
    )
