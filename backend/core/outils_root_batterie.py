"""Outils root : batterie brute et temperatures (palier root).

Deux lectures reelles via `su -c`, une correction :
- root_lire_batterie_brute : tensions, courant, compteur, cycles.
- root_lire_temperatures : capteurs thermiques du telephone.
- root_reinitialiser_stats_batterie : remet les compteurs a zero.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_root import executer_root, marquer_non_teste, preparer_root

# Dossiers batterie essayes dans l'ordre (audit A) : certains
# telephones exposent "bms" au lieu de "battery".
DOSSIERS_BATTERIE = ("battery", "bms")

# Fichiers lus dans le dossier batterie en un seul appel.
FICHIERS_BATTERIE = (
    "voltage_now",
    "current_now",
    "status",
    "temp",
    "capacity",
    "charge_counter",
    "charge_full",
    "charge_full_design",
    "cycle_count",
    "health",
    "technology",
    "present",
)

# Etats de charge bruts traduits en francais.
ETATS_CHARGE = {
    "charging": "en charge",
    "discharging": "en decharge",
    "full": "pleine",
    "not charging": "pas en charge",
}

# Plage plausible des capteurs thermiques, en degres. Hors de cette
# plage, la valeur est une erreur du capteur, pas une temperature.
TEMP_MINI_PLAUSIBLE = -50.0
TEMP_MAXI_PLAUSIBLE = 150.0

# Ligne `grep -H '' f1 f2` : nom:contenu.
MOTIF_SYSFS = re.compile(r"^([^:]+):(.*)$")


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


def formater_batterie_brute(valeurs):
    """Texte de reponse pour root_lire_batterie_brute. Fonction pure."""
    if not valeurs:
        return "Batterie brute illisible pour le moment."
    morceaux = []
    tension = _entier(valeurs, "voltage_now")
    if tension is not None:
        morceaux.append(f"tension {tension / 1000000:.2f} V")
    # Sens du courant (audit A) : le signe seul ment sur certains
    # modeles (toujours positif, ou inverse). On croise avec status
    # quand il est lisible, sinon on marque le sens "probable".
    etat = (valeurs.get("status") or "").strip().lower()
    courant = _entier(valeurs, "current_now")
    if courant is not None:
        if etat in ("charging", "discharging", "full", "not charging"):
            sens = ETATS_CHARGE[etat]
            morceaux.append(f"courant {abs(courant) // 1000} mA ({sens})")
        else:
            sens = "charge probable" if courant > 0 else "decharge probable"
            morceaux.append(f"courant {abs(courant) // 1000} mA ({sens})")
    elif etat in ETATS_CHARGE:
        morceaux.append(f"batterie {ETATS_CHARGE[etat]}")
    temp = _entier(valeurs, "temp")
    if temp is not None:
        morceaux.append(f"temperature {temp / 10:.1f} C")
    compteur = _entier(valeurs, "charge_counter")
    pleine = _entier(valeurs, "charge_full")
    origine = _entier(valeurs, "charge_full_design")
    if compteur is not None:
        morceaux.append(f"contenu {compteur // 1000} mAh")
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
            degres = int(temps[cle_temp]) / 1000
        except (TypeError, ValueError):
            continue
        if not TEMP_MINI_PLAUSIBLE <= degres <= TEMP_MAXI_PLAUSIBLE:
            continue
        zones.append((zone.rsplit("/", 1)[-1], nom.strip(), degres))
    zones.sort(key=lambda z: z[2], reverse=True)
    return zones


def formater_temperatures(zones, limite=10):
    """Texte de reponse pour root_lire_temperatures. Fonction pure."""
    if not zones:
        return "Temperatures illisibles pour le moment."
    details = ", ".join(
        f"{nom} {degres:.1f} C" for _z, nom, degres in zones[:limite]
    )
    return f"Temperatures ({len(zones)} capteurs) : {details}."


@mcp_diagnostic.tool()
def root_lire_batterie_brute() -> str:
    """Lit les mesures brutes de la batterie (tension, courant, cycles).

    Lecture seule via su, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    fichiers = " ".join(FICHIERS_BATTERIE)
    valeurs = {}
    derniere_erreur = ""
    for dossier in DOSSIERS_BATTERIE:
        resultat = executer_root(
            f"cd /sys/class/power_supply/{dossier} && "
            f"grep -H '' {fichiers} 2>/dev/null",
            appareil_id,
        )
        if resultat["ok"]:
            valeurs = parse_sysfs_dict(resultat["sortie"])
            if valeurs:
                break
        elif resultat["erreur"]:
            derniere_erreur = resultat["erreur"]
    if not valeurs:
        if derniere_erreur:
            return marquer_non_teste(
                f"Batterie brute illisible : {derniere_erreur}"
            )
        return marquer_non_teste("Batterie brute illisible pour le moment.")
    return marquer_non_teste(formater_batterie_brute(valeurs))


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
    zones = parse_thermal(
        types["sortie"] if types["ok"] else "",
        temps["sortie"] if temps["ok"] else "",
    )
    return marquer_non_teste(formater_temperatures(zones, limite))


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
            f"Compteurs non remis a zero : {resultat['erreur']}"
        )
    return marquer_non_teste(
        "Statistiques de batterie remises a zero. Laisse passer "
        "quelques heures d'usage avant de juger la conso."
    )
