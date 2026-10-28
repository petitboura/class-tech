"""Objet FastMCP partagé par tous les outils de diagnostic (chantier B).

Adapté de core/outils_generation_commun.py de classinus-backend (lu en
lecture seule) : l'objet mcp_diagnostic défini ici est LE même objet
partagé par tous les modules core/outils_*.py. Chaque
@mcp_diagnostic.tool() déclaré dans un de ces modules enregistre son
outil sur ce serveur unique, monté dans api/main.py.
"""

from mcp.server.mcpserver import Context, MCPServer as FastMCP

mcp_diagnostic = FastMCP(name="diagnostic")

# Version du serveur, source unique (lue par api/main.py et par la
# sonde ping_serveur, jamais recopiée ailleurs). 0.2.0 : palier 80 %,
# pont ADB et 14 outils téléphone.
VERSION_SERVEUR = "0.2.0"

__all__ = ["Context", "VERSION_SERVEUR", "mcp_diagnostic"]
