"""Serveur d'outils MCP de diagnostic Class-Tech (étape 2, palier 80 %).

Plus de chaîne LLM ici : le cerveau (modèle, boucle d'outils,
confirmations, affichage) vit dans Classinus, qui appelle ce serveur
en HTTP MCP. Cette app FastAPI ne fait que monter le serveur MCP
sur /mcp/diagnostic.

Lancement local (depuis le dossier backend/) :
    uvicorn api.main:app --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI

from core.outils_diagnostic_commun import VERSION_SERVEUR
from core.serveur_mcp_diagnostic import mcp_diagnostic

logging.basicConfig(level=logging.INFO)


def _hote_de_valeur(valeur):
    """Nom d'hote tire d'une URL ou d'un nom brut. Fonction pure."""
    valeur = (valeur or "").strip()
    if not valeur:
        return ""
    if "://" not in valeur:
        valeur = "https://" + valeur
    return urlparse(valeur).hostname or ""


def hotes_publics_autorises():
    """Hotes publics acceptes par la protection anti-rebond DNS.

    Lus dans l'environnement, jamais en dur : RENDER_EXTERNAL_URL est
    fourni par Render (adresse https du service), MCP_HOTE_PUBLIC permet
    de forcer une autre adresse. Vide en local, ou les hotes locaux
    suffisent.
    """
    hotes = []
    for variable in ("MCP_HOTE_PUBLIC", "RENDER_EXTERNAL_URL"):
        hote = _hote_de_valeur(os.environ.get(variable, ""))
        if hote and hote not in hotes:
            hotes.append(hote)
    return hotes


def _construire_app_mcp():
    """Sous-application MCP avec hotes autorises dynamiques."""
    from mcp.server.transport_security import TransportSecuritySettings

    hotes = [
        "127.0.0.1", "localhost", "[::1]",
        "127.0.0.1:*", "localhost:*", "[::1]:*",
    ]
    origines = [
        "http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*",
    ]
    for hote in hotes_publics_autorises():
        hotes.extend([hote, hote + ":*"])
        origines.append("https://" + hote)
    securite = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hotes,
        allowed_origins=origines,
    )
    return mcp_diagnostic.streamable_http_app(
        stateless_http=True,
        streamable_http_path="/",
        transport_security=securite,
    )


# Sous-application MCP, construite une seule fois (elle porte les routes
# ET le cycle de vie du gestionnaire de sessions).
app_mcp = _construire_app_mcp()


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
