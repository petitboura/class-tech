"""Mémoire, processeur et applis gourmandes (palier 100 %, sans root).

Lecture seule : ces outils ne changent rien sur le téléphone. Ils
lisent /proc et les services système via adb, analysent avec
analyse_systeme, et renvoient un texte en français.
"""

from __future__ import annotations

from core.analyse_systeme import (
    analyser_cpu as analyser_cpu_systeme,
    analyser_memoire,
    analyser_top,
)
from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_adb_serie, preparer_acces


def _avec_note(acces: dict, texte: str) -> str:
    """Ajoute la note (plusieurs téléphones) devant la réponse."""
    if acces.get("note"):
        return f"{acces['note']} {texte}"
    return texte


@mcp_diagnostic.tool()
def analyser_memoire_vive() -> str:
    """Détaille la mémoire vive : total, libre, verdict.

    Lit /proc/meminfo du téléphone et dit si la mémoire est correcte,
    juste ou critique, avec le geste conseillé.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(adb, serie, ["shell", "cat", "/proc/meminfo"])
    if not ok:
        return _avec_note(acces, "Mémoire vive illisible sur ce téléphone.")
    return _avec_note(acces, analyser_memoire(sortie)["resume"])


@mcp_diagnostic.tool()
def analyser_cpu() -> str:
    """Détaille le processeur : cœurs, modèle, charge actuelle.

    Lit /proc/cpuinfo et /proc/loadavg du téléphone et dit si le
    téléphone est calme, occupé ou très sollicité.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok_cpu, cpuinfo, _ = executer_adb_serie(adb, serie, ["shell", "cat", "/proc/cpuinfo"])
    ok_charge, loadavg, _ = executer_adb_serie(adb, serie, ["shell", "cat", "/proc/loadavg"])
    if not ok_cpu and not ok_charge:
        return _avec_note(acces, "Processeur illisible sur ce téléphone.")
    analyse = analyser_cpu_systeme(cpuinfo if ok_cpu else "", loadavg if ok_charge else "")
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def analyser_applications_gourmandes() -> str:
    """Liste les applis les plus gourmandes en CPU et en RAM.

    Lit le classement instantané du téléphone (top) et la mémoire par
    appli (meminfo), puis nomme les plus gros consommateurs.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    ok_top, top, _ = executer_adb_serie(adb, serie, ["shell", "top", "-n", "1"])
    ok_mem, meminfo, _ = executer_adb_serie(adb, serie, ["shell", "dumpsys", "meminfo"])
    if not ok_top and not ok_mem:
        return _avec_note(acces, "Consommation par appli illisible sur ce téléphone.")
    analyse = analyser_top(top if ok_top else "", meminfo if ok_mem else "")
    return _avec_note(acces, analyse["resume"])
