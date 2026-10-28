"""Tests du registre d'outils (étape 2).

Sans dépendance externe : tourne avec pytest comme avec un simple
`python tests/test_registre_outils.py` depuis le dossier backend/.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.registre_outils import (  # noqa: E402
    CATEGORIES_OUTILS,
    OUTILS_PALIER_ROOT,
    OUTILS_SENSIBLES,
    REGISTRE_AFFICHAGE_OUTILS,
    TYPES_APPAREILS,
    VERBES_ACTIONS,
    outils_de_la_categorie,
)


def test_categories_connues_du_registre():
    for categorie, noms in CATEGORIES_OUTILS.items():
        for nom in noms:
            assert nom in REGISTRE_AFFICHAGE_OUTILS, f"{nom} ({categorie}) absent du registre"


def test_entrees_registre_completes():
    for nom, entree in REGISTRE_AFFICHAGE_OUTILS.items():
        assert entree.get("label"), f"{nom} sans label"
        assert entree.get("icone"), f"{nom} sans icone"
        assert "onglet" in entree, f"{nom} sans clé onglet (None accepté, absence refusée)"


def test_aucun_tiret_double_affiche():
    # Règle MUSE.md : jamais de "--" dans un texte affiché.
    for nom, entree in REGISTRE_AFFICHAGE_OUTILS.items():
        assert "--" not in entree["label"], f"{nom} : tiret double dans le label"
    for verbe, (libelle, _icone) in VERBES_ACTIONS.items():
        assert "--" not in libelle, f"{verbe} : tiret double dans le libellé"


def test_outils_sensibles_connus():
    for nom in OUTILS_SENSIBLES:
        base = nom.split(":")[0]
        assert base in REGISTRE_AFFICHAGE_OUTILS, f"{nom} sensible mais inconnu du registre"


def test_outils_de_la_categorie():
    candidats = [
        {"type": "function", "function": {"name": "resumer_symptome"}},
        {"type": "function", "function": {"name": "verifier_chaine"}},
    ]
    trouves = {o["function"]["name"] for o in outils_de_la_categorie("telephone", candidats)}
    assert trouves == {"resumer_symptome"}
    assert outils_de_la_categorie("categorie_inconnue", candidats) == []


def test_types_appareils():
    assert TYPES_APPAREILS == ("telephone", "ordinateur")


def test_garde_fou_root_declare_mais_sensible():
    # Audit final : le registre DECLARE les 19 outils root (dans la
    # categorie telephone et dans OUTILS_SENSIBLES, donc confirmation
    # exigee le jour de l'activation). C'est le serveur qui les cache
    # tant que CLASSTECH_OUTILS_ROOT ne vaut pas "1" (voir les tests
    # en sous-processus de test_outils_root.py et test_audit_risques_b.py).
    assert len(OUTILS_PALIER_ROOT) == 19
    telephone = CATEGORIES_OUTILS["telephone"]
    for nom in OUTILS_PALIER_ROOT:
        assert nom in telephone
        assert nom in OUTILS_SENSIBLES


if __name__ == "__main__":
    test_categories_connues_du_registre()
    test_entrees_registre_completes()
    test_aucun_tiret_double_affiche()
    test_outils_sensibles_connus()
    test_outils_de_la_categorie()
    test_types_appareils()
    test_garde_fou_root_declare_mais_sensible()
    print("OK : registre d'outils cohérent.")
