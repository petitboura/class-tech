"""Serveur MCP interne de diagnostic (chantier B, paliers 80 %, 100 % et root).

Garde-fou (audit A) : les 7 modules root du bas ne sont importes que
si OUTILS_ROOT_ACTIFS vaut True dans core/registre_outils.py. Par
defaut ils restent hors du serveur : ni visibles, ni appelables.

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
  - outils_materiel_100.py : tests matériel unitaires (palier 100 %).
  - outils_performance_100.py : mémoire, CPU, applis gourmandes.
  - outils_securite_100.py : permissions, sécurité, mises à jour.
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
import core.outils_telephone_applis  # noqa: F401
import core.outils_telephone_base  # noqa: F401
import core.outils_telephone_batterie  # noqa: F401
import core.outils_telephone_capteurs  # noqa: F401
import core.outils_telephone_reseau  # noqa: F401
import core.outils_telephone_stockage  # noqa: F401
import core.outils_telephone_systeme  # noqa: F401
import core.outils_materiel_100  # noqa: F401
import core.outils_performance_100  # noqa: F401
import core.outils_securite_100  # noqa: F401

from core.outils_diagnostic_commun import mcp_diagnostic
from core.registre_outils import OUTILS_ROOT_ACTIFS

# Palier root DESACTIVE par defaut (audit A, garde-fou) : les modules
# root ne sont importes, donc les outils ni exposes ni appelables,
# que si OUTILS_ROOT_ACTIFS passe a True (ordre de Bourama seul).
if OUTILS_ROOT_ACTIFS:
    import core.outils_root_acces  # noqa: F401
    import core.outils_root_batterie  # noqa: F401
    import core.outils_root_corrections  # noqa: F401
    import core.outils_root_firmware  # noqa: F401
    import core.outils_root_partitions  # noqa: F401
    import core.outils_root_processus  # noqa: F401
    import core.outils_root_systeme  # noqa: F401

__all__ = ["mcp_diagnostic"]
