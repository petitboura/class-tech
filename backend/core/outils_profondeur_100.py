"""10 diagnostics profonds en lecture seule (palier 100 %, sans root).

Ces outils lisent les services internes d'Android via adb (dumpsys,
getprop, /proc, logcat), analysent avec analyse_profonde, et renvoient
un texte en français simple. AUCUNE écriture, aucun changement de
réglage : si une source est fermée sur un modèle, l'outil le dit
honnêtement au lieu d'inventer. Le journal du noyau (dmesg) reste
fermé sans root et n'est lu par aucun outil ici.
"""

from __future__ import annotations

from core.analyse_profonde import (
    analyser_carte_systeme,
    analyser_fluidite,
    analyser_historique_batterie,
    analyser_journaux,
    analyser_memoire_temps,
    analyser_reveils,
    analyser_saturation,
    analyser_temperatures,
    analyser_trafic_applis,
    analyser_verrous_veille,
    associer_uid_paquets,
)
from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import DELAI_ADB_LENT_SECONDES, executer_adb_serie, preparer_acces


def _avec_note(acces: dict, texte: str) -> str:
    """Ajoute la note (plusieurs téléphones) devant la réponse."""
    if acces.get("note"):
        return f"{acces['note']} {texte}"
    return texte


def _lire(adb: str, serie: str, morceaux: list, lent: bool = False) -> str:
    """Une lecture adb, sortie brute ou chaîne vide si illisible."""
    if lent:
        ok, sortie, _ = executer_adb_serie(
            adb, serie, morceaux, delai=DELAI_ADB_LENT_SECONDES
        )
    else:
        ok, sortie, _ = executer_adb_serie(adb, serie, morceaux)
    return sortie if ok else ""


@mcp_diagnostic.tool()
def lire_temperatures_internes() -> str:
    """Lit les températures internes : sondes CPU, batterie, coque.

    Dit si le téléphone chauffe normalement ou trop, et conseille
    le repos à l'ombre en cas de surchauffe.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    sortie = _lire(
        acces["adb"], acces["serie"], ["shell", "dumpsys", "thermalservice"]
    )
    return _avec_note(acces, analyser_temperatures(sortie)["resume"])


@mcp_diagnostic.tool()
def lire_historique_batterie() -> str:
    """Lit l'historique batterie complet : autonomie, conso, réveils.

    Temps passé sur batterie depuis la charge, conso estimée et
    mesurée, plus gros consommateurs et nombre de réveils.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    sortie = _lire(
        acces["adb"], acces["serie"], ["shell", "dumpsys", "batterystats"],
        lent=True,
    )
    return _avec_note(acces, analyser_historique_batterie(sortie)["resume"])


@mcp_diagnostic.tool()
def lire_trafic_par_appli() -> str:
    """Lit le trafic internet par appli : qui envoie et reçoit quoi.

    Octets reçus et envoyés par appli depuis les compteurs du
    téléphone, avec le total général.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    netstats = _lire(adb, serie, ["shell", "dumpsys", "netstats"], lent=True)
    paquets = _lire(adb, serie, ["shell", "pm", "list", "packages", "-U"])
    table = associer_uid_paquets(paquets)
    return _avec_note(acces, analyser_trafic_applis(netstats, table)["resume"])


@mcp_diagnostic.tool()
def lire_fluidite_ecran() -> str:
    """Lit les saccades d'affichage : images saccadées par appli.

    Dit si l'affichage est fluide ou si le téléphone peine, appli
    par appli. Demande d'ouvrir une appli si rien n'est mesurable.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    sortie = _lire(
        acces["adb"], acces["serie"], ["shell", "dumpsys", "gfxinfo"], lent=True
    )
    return _avec_note(acces, analyser_fluidite(sortie)["resume"])


@mcp_diagnostic.tool()
def lire_saturation_systeme() -> str:
    """Lit la saturation interne : attentes processeur et mémoire.

    Dit quel pourcentage du temps récent le téléphone a manqué de
    souffle (processeur, mémoire, stockage).
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    cpu = _lire(adb, serie, ["shell", "cat", "/proc/pressure/cpu"])
    memoire = _lire(adb, serie, ["shell", "cat", "/proc/pressure/memory"])
    stockage = _lire(adb, serie, ["shell", "cat", "/proc/pressure/io"])
    return _avec_note(acces, analyser_saturation(cpu, memoire, stockage)["resume"])


@mcp_diagnostic.tool()
def lire_reveils_planifies() -> str:
    """Lit les alarmes et tâches qui réveillent le téléphone.

    Compte les réveils par appli et les tâches planifiées, pour
    trouver ce qui travaille en arrière plan.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    alarmes = _lire(adb, serie, ["shell", "dumpsys", "alarm"], lent=True)
    taches = _lire(adb, serie, ["shell", "dumpsys", "jobscheduler"])
    return _avec_note(acces, analyser_reveils(alarmes, taches)["resume"])


@mcp_diagnostic.tool()
def lire_journaux_systeme() -> str:
    """Lit les journaux système profonds : plantages et erreurs.

    Plantages récents par appli, erreurs système par sujet et
    rapports conservés par le téléphone.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    crash = _lire(
        adb, serie, ["shell", "logcat", "-d", "-b", "crash", "-t", "80"]
    )
    systeme = _lire(
        adb, serie,
        ["shell", "logcat", "-d", "-b", "system", "-t", "150", "*:E"],
    )
    dropbox = _lire(adb, serie, ["shell", "dumpsys", "dropbox"])
    analyse = analyser_journaux(crash, systeme, dropbox)
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def lire_carte_systeme() -> str:
    """Dresse la carte du système : version, modèle, services.

    Version Android et correctif, marque et modèle, nombre de
    services actifs et de composants matériels déclarés.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    proprietes = _lire(adb, serie, ["shell", "getprop"])
    services = _lire(adb, serie, ["shell", "service", "list"])
    composants = _lire(adb, serie, ["shell", "lshal"])
    analyse = analyser_carte_systeme(proprietes, services, composants)
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def lire_memoire_dans_le_temps() -> str:
    """Lit la mémoire par appli sur les dernières heures.

    Moyennes de mémoire vive gardée par chaque appli : qui garde
    beaucoup et qui reste raisonnable.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    sortie = _lire(
        acces["adb"], acces["serie"],
        ["shell", "dumpsys", "procstats", "--hours", "3"],
        lent=True,
    )
    return _avec_note(acces, analyser_memoire_temps(sortie)["resume"])


@mcp_diagnostic.tool()
def lire_verrous_veille() -> str:
    """Lit les verrous qui empêchent le téléphone de dormir.

    Liste ce qui retient le téléphone éveillé en ce moment, pour
    expliquer une batterie qui fond vite.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    sortie = _lire(
        acces["adb"], acces["serie"], ["shell", "dumpsys", "power"]
    )
    return _avec_note(acces, analyser_verrous_veille(sortie)["resume"])
