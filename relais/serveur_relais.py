"""Serveur du relais PC Class-Tech.

Ce module réutilise tel quel le code du dépôt : l'application de
api.main (qui porte le serveur MCP sur /mcp/diagnostic) reçoit ici
deux routes simples en plus, sous /relais. Les outils appelés sont
les vraies fonctions du dépôt, sans copie ni réécriture.
Seules des lectures sont exposées. Les outils sensibles et root
sont refusés par construction.
"""

from __future__ import annotations

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relais_config import preparer_imports  # noqa: E402

preparer_imports()

from api.main import app  # noqa: E402
from core.outils_diagnostic_commun import VERSION_SERVEUR  # noqa: E402
from core.outils_materiel_100 import (  # noqa: E402
    tester_boutons,
    tester_ecran_tactile,
    tester_gps,
    tester_micro,
)
from core.outils_performance_100 import (  # noqa: E402
    analyser_applications_gourmandes,
    analyser_cpu,
    analyser_memoire_vive,
)
from core.outils_securite_100 import (  # noqa: E402
    lister_permissions_risquees,
    verifier_mises_a_jour,
    verifier_securite,
)
from core.outils_sonde import ping_serveur  # noqa: E402
from core.outils_telephone_applis import (  # noqa: E402
    lire_crashs_recents,
    lister_applis,
    lister_applis_inutilisees,
)
from core.outils_telephone_base import detecter_telephone  # noqa: E402
from core.outils_telephone_batterie import (  # noqa: E402
    lire_batterie,
    lire_conso_batterie,
)
from core.outils_telephone_capteurs import tester_capteurs  # noqa: E402
from core.outils_telephone_reseau import (  # noqa: E402
    lire_etat_reseau,
    lire_infos_wifi,
)
from core.outils_telephone_stockage import (  # noqa: E402
    lire_stockage,
    lister_gros_fichiers,
)
from core.outils_telephone_systeme import (  # noqa: E402
    lire_erreurs_recentes,
    lire_version_systeme,
)
from core.pont_adb import resumer_liaison  # noqa: E402
from pydantic import BaseModel  # noqa: E402

OUTILS_LECTURE = {
    "ping_serveur": ping_serveur,
    "detecter_telephone": detecter_telephone,
    "lire_batterie": lire_batterie,
    "lire_conso_batterie": lire_conso_batterie,
    "lire_stockage": lire_stockage,
    "lister_gros_fichiers": lister_gros_fichiers,
    "lister_applis": lister_applis,
    "lire_crashs_recents": lire_crashs_recents,
    "lister_applis_inutilisees": lister_applis_inutilisees,
    "lire_version_systeme": lire_version_systeme,
    "lire_erreurs_recentes": lire_erreurs_recentes,
    "lire_etat_reseau": lire_etat_reseau,
    "lire_infos_wifi": lire_infos_wifi,
    "tester_capteurs": tester_capteurs,
    "tester_ecran_tactile": tester_ecran_tactile,
    "tester_gps": tester_gps,
    "tester_micro": tester_micro,
    "tester_boutons": tester_boutons,
    "analyser_memoire_vive": analyser_memoire_vive,
    "analyser_cpu": analyser_cpu,
    "analyser_applications_gourmandes": analyser_applications_gourmandes,
    "lister_permissions_risquees": lister_permissions_risquees,
    "verifier_securite": verifier_securite,
    "verifier_mises_a_jour": verifier_mises_a_jour,
}

OUTILS_SENSIBLES_REFUSES = frozenset({
    "vider_cache_applis",
    "tester_haut_parleur",
    "tester_vibreur",
    "tester_camera",
    "revoquer_permission",
})


class AppelOutil(BaseModel):
    """Arguments d'un outil, vide par défaut."""

    args: dict = {}


@app.get("/relais/sante")
def sante_relais():
    """État du relais et du téléphone vu, en JSON."""
    return {
        "ok": True,
        "service": "Relais PC Class-Tech",
        "version": VERSION_SERVEUR,
        "outils": sorted(OUTILS_LECTURE),
        "liaison": resumer_liaison(),
    }


def _args_acceptes(fonction, args):
    """Ne garde que les arguments acceptés par la fonction."""
    try:
        params = inspect.signature(fonction).parameters
    except (TypeError, ValueError):
        return {}
    acceptes = {}
    for nom, valeur in args.items():
        param = params.get(nom)
        if param is None:
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        acceptes[nom] = valeur
    return acceptes


@app.post("/relais/outil/{nom}")
def appeler_outil(nom: str, appel: AppelOutil | None = None):
    """Exécute un outil de lecture et renvoie son texte."""
    if nom in OUTILS_SENSIBLES_REFUSES or nom.startswith("root"):
        return {
            "ok": False,
            "outil": nom,
            "erreur": "Outil refusé par le relais : lecture seule ici.",
        }
    fonction = OUTILS_LECTURE.get(nom)
    if fonction is None:
        return {
            "ok": False,
            "outil": nom,
            "erreur": "Outil inconnu du relais. Vois la liste sur /relais/sante.",
        }
    args = appel.args if appel and isinstance(appel.args, dict) else {}
    try:
        texte = fonction(**_args_acceptes(fonction, args))
    except TypeError:
        return {
            "ok": False,
            "outil": nom,
            "erreur": "Arguments refusés par l'outil. Réessaie sans arguments.",
        }
    except Exception:
        return {
            "ok": False,
            "outil": nom,
            "erreur": "L'outil a échoué sans explication. Réessaie dans un moment.",
        }
    if not isinstance(texte, str):
        texte = str(texte)
    return {"ok": True, "outil": nom, "resultat": texte}
