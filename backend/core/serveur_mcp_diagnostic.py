"""Serveur MCP interne de diagnostic (chantier B, palier root).

Adapté de core/serveur_mcp_generation.py de classinus-backend (lu en
lecture seule). Ce fichier ne fait que rassembler les modules d'outils
ci-dessous, qui déclarent chacun leurs outils sur le même objet partagé
mcp_diagnostic (core/outils_diagnostic_commun.py) :
  - outils_etat_appareil.py : sonde de santé, résumé du symptôme.
  - outils_sonde.py : sonde de test ping_serveur (ok, version, heure).
  - outils_root_acces.py : vérification root, infos su et modules.
  - outils_root_systeme.py : fichiers système, erreurs et paniques noyau.
  - outils_root_partitions.py : partitions et intégrité du système.
  - outils_root_batterie.py : batterie brute, températures, stats.
  - outils_root_firmware.py : firmware et slot de démarrage.
  - outils_root_processus.py : processus gourmands, wakelocks.
  - outils_root_corrections.py : nettoyage crashs, Dalvik, trim, reboot.

Monté dans api/main.py sur le chemin /mcp/diagnostic (même processus,
pas de service séparé).
"""

# Chaque import enregistre les outils du module sur mcp_diagnostic.
import core.outils_etat_appareil  # noqa: F401
import core.outils_sonde  # noqa: F401
import core.outils_root_acces  # noqa: F401
import core.outils_root_batterie  # noqa: F401
import core.outils_root_corrections  # noqa: F401
import core.outils_root_firmware  # noqa: F401
import core.outils_root_partitions  # noqa: F401
import core.outils_root_processus  # noqa: F401
import core.outils_root_systeme  # noqa: F401

from core.outils_diagnostic_commun import mcp_diagnostic

__all__ = ["mcp_diagnostic"]
