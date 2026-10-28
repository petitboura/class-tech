"""Serveur d'outils MCP de diagnostic Class-Tech (étape 2).

Plus de chaîne LLM ici : le cerveau (modèle, boucle d'outils,
confirmations, affichage) vit dans Classinus, qui appelle ce serveur
en HTTP MCP. Cette app FastAPI ne fait que monter le serveur MCP
sur /mcp/diagnostic.

Lancement local (depuis le dossier backend/) :
    uvicorn api.main:app --port 8000
"""

import logging

from fastapi import FastAPI

from core.outils_diagnostic_commun import VERSION_SERVEUR
from core.serveur_mcp_diagnostic import mcp_diagnostic

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Class-Tech API", version=VERSION_SERVEUR)

app.mount(
    "/mcp/diagnostic",
    mcp_diagnostic.streamable_http_app(stateless_http=True, streamable_http_path="/"),
)
