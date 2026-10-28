"""Serveur MCP interne de diagnostic (chantier B, palier 80 %).

Adapté de core/serveur_mcp_generation.py de classinus-backend (lu en
lecture seule). Ce fichier ne fait que rassembler les modules d'outils
ci-dessous, qui déclarent chacun leurs outils sur le même objet partagé
mcp_diagnostic (core/outils_diagnostic_commun.py) :
  - outils_etat_appareil.py : sonde de santé, résumé du symptôme.
  - outils_sonde.py : sonde de test ping_serveur (ok, version, heure).
  - outils_telephone_base.py : détection du téléphone branché (pont ADB).
  - outils_telephone_batterie.py : état batterie, conso par appli.
  - outils_telephone_stockage.py : espace, gros fichiers, vide des caches.
  - outils_telephone_applis.py : liste, plantages, inutilisées.
  - outils_telephone_systeme.py : version Android, erreurs récentes.
  - outils_telephone_reseau.py : état réseau, détails wifi.
  - outils_telephone_capteurs.py : test groupé des capteurs.

Monté dans api/main.py sur le chemin /mcp/diagnostic (même processus,
pas de service séparé).
"""

# Chaque import enregistre les outils du module sur mcp_diagnostic.
import core.outils_etat_appareil  # noqa: F401
import core.outils_sonde  # noqa: F401
import core.outils_telephone_applis  # noqa: F401
import core.outils_telephone_base  # noqa: F401
import core.outils_telephone_batterie  # noqa: F401
import core.outils_telephone_capteurs  # noqa: F401
import core.outils_telephone_reseau  # noqa: F401
import core.outils_telephone_stockage  # noqa: F401
import core.outils_telephone_systeme  # noqa: F401

from core.outils_diagnostic_commun import mcp_diagnostic

__all__ = ["mcp_diagnostic"]
