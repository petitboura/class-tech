"""Serveur d'outils MCP de diagnostic Class-Tech (étape 2, palier 80 %).

Plus de chaîne LLM ici : le cerveau (modèle, boucle d'outils,
confirmations, affichage) vit dans Classinus, qui appelle ce serveur
en HTTP MCP. Cette app FastAPI ne fait que monter le serveur MCP
sur /mcp/diagnostic.

Lancement local (depuis le dossier backend/) :
    uvicorn api.main:app --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.outils_diagnostic_commun import VERSION_SERVEUR
from core.serveur_mcp_diagnostic import mcp_diagnostic

logging.basicConfig(level=logging.INFO)

# Sous-application MCP, construite une seule fois (elle porte les routes
# ET le cycle de vie du gestionnaire de sessions).
app_mcp = mcp_diagnostic.streamable_http_app(stateless_http=True, streamable_http_path="/")


@asynccontextmanager
async def duree_vie(_app):
    """Demarre le gestionnaire de sessions MCP avec le serveur.

    Correctif palier 80 % : streamable_http_app() branche son gestionnaire
    sur le cycle de vie du sous-serveur, mais les versions recentes de
    Starlette n'executent plus ce cycle pour une app montee (erreur
    "Task group is not initialized" a chaque appel, constatee en local).
    On execute donc ce cycle explicitement. Sur une ancienne version qui
    le demarrerait deja toute seule, on laisse filer sans double demarrage.
    """
    contexte = app_mcp.router.lifespan_context(app_mcp)
    try:
        await contexte.__aenter__()
    except RuntimeError as erreur:
        if "only be called once" not in str(erreur):
            raise
        yield
        return
    try:
        yield
    finally:
        await contexte.__aexit__(None, None, None)


app = FastAPI(title="Class-Tech API", version=VERSION_SERVEUR, lifespan=duree_vie)

app.mount("/mcp/diagnostic", app_mcp)
