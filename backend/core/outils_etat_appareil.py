"""Outil exemple du squelette : état de l'appareil (chantier B).

Adapté du motif de core/outils_minuteurs.py de classinus-backend (lu en
lecture seule) : un outil MCP déclaré avec @mcp_diagnostic.tool(), qui
renvoie un texte en français destiné au modèle.

Volontairement sans mémoire ni base de données : le squelette reste
sans état. Quand un outil stockera des données liées à un compte, il
faudra appliquer la règle de purge du MUSE.md (purge + export +
cascade) dans la même livraison.
"""

from core.outils_diagnostic_commun import mcp_diagnostic
from core.registre_outils import TYPES_APPAREILS


@mcp_diagnostic.tool()
def verifier_chaine() -> str:
    """Sonde de santé : confirme que la chaîne d'outils répond.

    Aucune donnée utilisateur. Sert uniquement à valider que le chemin
    complet (modèle, appel d'outil, serveur MCP interne) fonctionne.
    """
    return "Chaîne d'outils opérationnelle, je suis prêt à diagnostiquer."


@mcp_diagnostic.tool()
def resumer_symptome(appareil: str, symptome: str, depuis: str = "") -> str:
    """Reformule le symptôme déclaré en fiche structurée pour le modèle.

    appareil vaut telephone ou ordinateur (voir TYPES_APPAREILS).
    symptome est la description en langage libre. depuis est optionnel
    (moment d'apparition, par exemple hier soir ou depuis une mise à
    jour). Ne pose aucun diagnostic, met seulement les faits en ordre.
    """
    if appareil not in TYPES_APPAREILS:
        attendus = ", ".join(TYPES_APPAREILS)
        return f"Erreur : appareil inconnu. Valeurs acceptées : {attendus}."
    if not symptome or not symptome.strip():
        return "Erreur : décris le symptôme en quelques mots."
    lignes = [f"Appareil : {appareil}", f"Symptôme : {symptome.strip()}"]
    if depuis and depuis.strip():
        lignes.append(f"Depuis : {depuis.strip()}")
    lignes.append("Prochaine étape : poser une question de précision.")
    return "\n".join(lignes)
