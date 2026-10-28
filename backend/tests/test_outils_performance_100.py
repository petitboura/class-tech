"""Tests des outils performance du palier 100 % (telephone simule).

Le test de l'outil analyser_cpu protege la correction B16 : l'outil
appelait sa fonction de calcul du meme nom au lieu de l'utiliser, ce
qui plantait des qu'un telephone etait branche. Jamais d'ADB reel.
Depuis backend/ : `pytest tests/test_outils_performance_100.py`
(ou `python tests/test_outils_performance_100.py`).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ACCES_OK = {"adb": "adb", "serie": "T", "erreur": None, "note": None}

CPUINFO_EXEMPLE = (
    "processor\t: 0\n"
    "processor\t: 1\n"
    "processor\t: 2\n"
    "processor\t: 3\n"
    "Hardware\t: Qualcomm Technologies, Inc SM-A055F\n"
)

LOADAVG_EXEMPLE = "0.50 0.40 0.30 1/200 12345\n"


def _interdire_adb_reel(monkeypatch):
    """Rend tout appel ADB reel impossible en test."""
    def interdit(*args, **kwargs):
        raise AssertionError("appel adb reel interdit en test")

    monkeypatch.setattr("core.pont_adb.executer_adb", interdit)
    monkeypatch.setattr("core.pont_adb.executer_adb_serie", interdit)
    monkeypatch.setattr("core.pont_adb.executer_shell", interdit)


def _simuler_adb(monkeypatch, nom_module, reponses):
    """Doublure de executer_adb_serie avec sorties figees.

    reponses : [(fragment, (ok, sortie, erreur))], le premier
    fragment contenu dans la commande gagne.
    """
    def faux_executer(adb, serie, morceaux, delai=None):
        commande = " ".join(morceaux)
        for fragment, reponse in reponses:
            if fragment in commande:
                return reponse
        return (False, "", "commande non simulee")

    _interdire_adb_reel(monkeypatch)
    monkeypatch.setattr(nom_module + ".preparer_acces", lambda: dict(ACCES_OK))
    monkeypatch.setattr(nom_module + ".executer_adb_serie", faux_executer)


def test_analyser_cpu_telephone_simule(monkeypatch):
    import core.outils_performance_100 as performance
    _simuler_adb(monkeypatch, "core.outils_performance_100", [
        ("cpuinfo", (True, CPUINFO_EXEMPLE, "")),
        ("loadavg", (True, LOADAVG_EXEMPLE, "")),
    ])
    texte = performance.analyser_cpu()
    assert "4 cœurs" in texte
    assert "calme" in texte


if __name__ == "__main__":
    import importlib

    class Rustine:
        def setattr(self, cible, valeur):
            module, _, attr = cible.rpartition(".")
            setattr(importlib.import_module(module), attr, valeur)

    rustine = Rustine()
    test_analyser_cpu_telephone_simule(rustine)
    print("OK : outils performance 100.")
