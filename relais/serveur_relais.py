"""Serveur du relais PC Class-Tech.

Ce module réutilise tel quel le code du dépôt : l'application de
api.main (qui porte le serveur MCP sur /mcp/diagnostic) reçoit ici
deux routes simples en plus, sous /relais. Les outils appelés sont
les vraies fonctions du dépôt, sans copie ni réécriture.
Les outils root sont refusés par construction. Les 5 outils sensibles
(vider les caches, haut-parleur, vibreur, caméra, retirer une
permission) sont exécutés ici, mais seulement après la confirmation de
l'utilisateur dans Classinus, qui reste le garde-fou.
"""

from __future__ import annotations

import copy
import inspect
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relais_config import preparer_imports  # noqa: E402

preparer_imports()

from api.main import app  # noqa: E402
from core.outils_diagnostic_commun import VERSION_SERVEUR  # noqa: E402
from core.outils_materiel_100 import (  # noqa: E402
    tester_boutons,
    tester_camera,
    tester_ecran_tactile,
    tester_gps,
    tester_haut_parleur,
    tester_micro,
    tester_vibreur,
)
from core.outils_performance_100 import (  # noqa: E402
    analyser_applications_gourmandes,
    analyser_cpu,
    analyser_memoire_vive,
)
from core.outils_profondeur_100 import (  # noqa: E402
    lire_carte_systeme,
    lire_fluidite_ecran,
    lire_historique_batterie,
    lire_journaux_systeme,
    lire_memoire_dans_le_temps,
    lire_reveils_planifies,
    lire_saturation_systeme,
    lire_temperatures_internes,
    lire_trafic_par_appli,
    lire_verrous_veille,
)
from core.outils_securite_100 import (  # noqa: E402
    lister_permissions_risquees,
    revoquer_permission,
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
    vider_cache_applis,
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
    # Outils profonds, sans root (décision D34) : lectures seules, ils
    # n'écrivent rien sur le téléphone.
    "lire_temperatures_internes": lire_temperatures_internes,
    "lire_historique_batterie": lire_historique_batterie,
    "lire_trafic_par_appli": lire_trafic_par_appli,
    "lire_fluidite_ecran": lire_fluidite_ecran,
    "lire_saturation_systeme": lire_saturation_systeme,
    "lire_reveils_planifies": lire_reveils_planifies,
    "lire_journaux_systeme": lire_journaux_systeme,
    "lire_carte_systeme": lire_carte_systeme,
    "lire_memoire_dans_le_temps": lire_memoire_dans_le_temps,
    "lire_verrous_veille": lire_verrous_veille,
    # Outils sensibles : effet réel sur le téléphone. Classinus exige la
    # confirmation de l'utilisateur AVANT de les envoyer ici (voir
    # OUTILS_SENSIBLES dans classinus-backend, core/registre_outils.py).
    "vider_cache_applis": vider_cache_applis,
    "tester_haut_parleur": tester_haut_parleur,
    "tester_vibreur": tester_vibreur,
    "tester_camera": tester_camera,
    "revoquer_permission": revoquer_permission,
}

# Refus par construction : tout nom qui commence par « root ».
PREFIXE_OUTILS_REFUSES = "root"


class AppelOutil(BaseModel):
    """Arguments d'un outil, vide par défaut."""

    args: dict = {}


# --- Liaison ADB en cache -------------------------------------------------
# resumer_liaison() lance `adb devices` (timeout jusqu'a 90 s) : l'appeler
# dans /relais/sante bloquait la reponse bien au-dela du delai HTTP de
# l'appli PC (3 s), qui concluait a tort que le relais etait mort.
# Une tache de fond rafraichit donc la liaison, et la sante ne lit que le
# cache : elle repond immediatement, toujours.
INTERVALLE_LIAISON_S = 5

_cache_liaison: dict | None = None
_verrou_liaison = threading.Lock()


def _liaison_en_attente():
    return {
        "adb_trouve": False,
        "adb_chemin": None,
        "appareils": [],
        "appareil_choisi": None,
        "pret": False,
        "message": "Liaison telephone en cours de verification, reessaie dans un moment.",
    }


def _rafraichir_liaison():
    global _cache_liaison
    while True:
        try:
            liaison = resumer_liaison()
        except Exception:
            liaison = None
        if isinstance(liaison, dict):
            with _verrou_liaison:
                _cache_liaison = liaison
        time.sleep(INTERVALLE_LIAISON_S)


def _demarrer_surveillance_liaison():
    fil = threading.Thread(target=_rafraichir_liaison, daemon=True, name="liaison-adb")
    fil.start()
    return fil


_surveillance_liaison = _demarrer_surveillance_liaison()


def liaison_en_cache():
    """Derniere liaison connue, sans jamais attendre ADB."""
    with _verrou_liaison:
        if _cache_liaison is None:
            return _liaison_en_attente()
        return copy.deepcopy(_cache_liaison)


@app.get("/relais/sante")
def sante_relais():
    """État du relais et du téléphone vu, en JSON. Réponse immédiate."""
    return {
        "ok": True,
        "service": "Relais PC Class-Tech",
        "version": VERSION_SERVEUR,
        "outils": sorted(OUTILS_LECTURE),
        "liaison": liaison_en_cache(),
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
    """Exécute un outil du relais et renvoie son texte."""
    if nom.startswith(PREFIXE_OUTILS_REFUSES):
        return {
            "ok": False,
            "outil": nom,
            "erreur": "Outil refusé par le relais : les outils root ne passent pas ici.",
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
            "erreur": "Arguments manquants ou refusés par l'outil. Vérifie les arguments demandés par l'outil, puis réessaie.",
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
