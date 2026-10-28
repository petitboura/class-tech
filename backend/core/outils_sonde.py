"""Sonde de test du serveur d'outils (readiness phase 2).

Outil MCP minimal et réel : ping_serveur répond ok, avec la version
du serveur et l'heure actuelle. Sert aux builders et au déploiement
pour vérifier que le chemin complet répond, sans rien toucher.
"""

from datetime import datetime, timezone

from core.outils_diagnostic_commun import VERSION_SERVEUR, mcp_diagnostic


def reponse_ping() -> str:
    """Texte de réponse, fonction pure testable sans le serveur."""
    heure = datetime.now(timezone.utc).strftime("%H:%M")
    return f"ok, serveur version {VERSION_SERVEUR}, heure {heure} UTC."


@mcp_diagnostic.tool()
def ping_serveur() -> str:
    """Sonde de test : répond ok avec la version du serveur et l'heure.

    Aucune donnée utilisateur. Sert uniquement à valider que le
    serveur d'outils répond (lancement local, déploiement, branchement
    Classinus).
    """
    return reponse_ping()
