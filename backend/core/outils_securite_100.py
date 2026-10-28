"""Permissions, sécurité et mises à jour (palier 100 %, sans root).

Lecture seule, sauf revoquer_permission qui retire vraiment une
permission (outil sensible : Classinus demande confirmation avant).
Texte en français simple, aucun verdict inventé : ce qui est illisible
sur un modèle est dit tel quel.
"""

from __future__ import annotations

import re

from core.analyse_systeme import (
   analyser_mises_a_jour,
    analyser_permissions,
    analyser_securite,
    normaliser_permission,
)
from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import DELAI_ADB_SECONDES, erreur_courte, executer_adb_serie, preparer_acces

# La liste complète des permissions est une grosse lecture.
DELAI_PERMISSIONS_SECONDES = 90


def _avec_note(acces: dict, texte: str) -> str:
    """Ajoute la note (plusieurs téléphones) devant la réponse."""
    if acces.get("note"):
        return f"{acces['note']} {texte}"
    return texte


def _lire(adb: str, serie: str, morceaux: list[str]) -> str | None:
    """Une valeur adb, ou None si la lecture échoue."""
    ok, sortie, _ = executer_adb_serie(adb, serie, morceaux)
    if not ok:
        return None
    texte = sortie.strip()
    return texte if texte and texte != "null" else None


def parse_verification_revoke(sortie_dumpsys: str, permissions: list[str]) -> dict[str, bool | None]:
    """Vérifie chaque permission dans `dumpsys package`. Fonction pure.

    Renvoie {permission: True} si granted=false (retrait confirmé),
    False si granted=true (toujours accordée), None si la permission
    n'apparaît pas dans la section runtime (jamais demandée ou
    format inconnu). Seule la section runtime compte : les
    permissions d'installation ont le même format mais ne se
    révoquent pas (audit final : ne pas confondre).
    """
    etats: dict[str, bool | None] = {perm: None for perm in permissions}
    accordees = parse_permissions_accordees(sortie_dumpsys or "")
    for perm in permissions:
        if perm in accordees:
            etats[perm] = not accordees[perm]
    return etats


def parse_permissions_accordees(texte: str) -> dict:
    """Permissions runtime accordees d'apres `dumpsys package`. Pure.

    Renvoie {permission: True/False}. Seule la section "runtime
    permissions" compte : les permissions d'installation ont le meme
    format mais ne se revoquent pas (audit risques : ne pas confondre).
    """
    accordees = {}
    if not texte:
        return accordees
    indent_section = None
    for ligne in texte.splitlines():
        if not ligne.strip():
            continue
        bas = ligne.strip().lower()
        if bas == "runtime permissions:":
            indent_section = len(ligne) - len(ligne.lstrip())
            continue
        if indent_section is None:
            continue
        indent = len(ligne) - len(ligne.lstrip())
        if indent <= indent_section:
            indent_section = None
            continue
        trouve = re.match(
            r"\s*(android\.permission\.[A-Z_]+):\s*granted=(true|false)",
            ligne,
        )
        if trouve:
            accordees[trouve.group(1)] = trouve.group(2) == "true"
    return accordees


@mcp_diagnostic.tool()
def lister_permissions_risquees(perimetre: str = "tierces") -> str:
    """Liste les applis détenant des permissions à risque.

    perimetre vaut tierces (applis installées, défaut), systeme ou
    toutes. Lit l'état réel des permissions sur le téléphone et signale
    les applis qui cumulent les accès sensibles.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    choix = (perimetre or "").strip().lower()
    if choix not in ("tierces", "systeme", "toutes"):
        return "Erreur : périmètre inconnu. Valeurs acceptées : tierces, systeme, toutes."
    adb, serie = acces["adb"], acces["serie"]
    ok, sortie, _ = executer_adb_serie(
        adb, serie, ["shell", "dumpsys", "package"], delai=DELAI_PERMISSIONS_SECONDES
    )
    if not ok:
        return _avec_note(acces, "Permissions illisibles sur ce téléphone.")
    analyse = analyser_permissions(sortie, choix)
    return _avec_note(acces, analyse["resume"])


@mcp_diagnostic.tool()
def revoquer_permission(paquet: str, permission: str) -> str:
    """Retire une permission à une appli (action réelle, sensible).

    paquet est le nom technique de l'appli (ex : com.exemple.appli).
    permission accepte un nom court (localisation, camera, micro,
    contacts, sms, telephone, calendrier, fichiers) ou un nom complet
    android.permission. Vérifie le retrait après coup et le confirme.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    nom_paquet = (paquet or "").strip()
    if not re.fullmatch(r"[A-Za-z][\w.]*", nom_paquet):
        return "Erreur : nom d'appli invalide (attendu : com.exemple.appli)."
    permissions = normaliser_permission(permission or "")
    if not permissions:
        return (
            "Erreur : permission inconnue. Noms courts acceptés : localisation, "
            "camera, micro, contacts, sms, telephone, calendrier, fichiers."
        )
    adb, serie = acces["adb"], acces["serie"]
    retires, echecs = [], []
    for perm in permissions:
        ok, _, erreur = executer_adb_serie(adb, serie, ["shell", "pm", "revoke", nom_paquet, perm])
        if ok:
            retires.append(perm)
        else:
            echecs.append((perm, erreur))
    if echecs and not retires:
        detail = (echecs[0][1] or "").lower()
        if "unknown package" in detail or "unknown_package" in detail:
            return _avec_note(acces, f"Appli {nom_paquet} introuvable sur ce téléphone.")
        if "does not support runtime permissions" in detail:
            return _avec_note(
                acces, f"L'appli {nom_paquet} ne gère pas les permissions à la volée."
            )
        if "not a changeable permission" in detail or "not changeable" in detail:
            return _avec_note(acces, f"Permission non modifiable pour {nom_paquet}.")
        return _avec_note(acces, f"Retrait impossible pour {nom_paquet} ({erreur_courte(echecs[0][1])}).")
    # Vérification après coup (audits A et B) : pm revoke répond OK
    # même quand il n'a rien changé. On relit l'état réel (section
    # runtime seule) avant d'affirmer.
    courts_retires = [p.rsplit(".", 1)[-1] for p in retires]
    texte = f"Permission retirée à {nom_paquet} : {', '.join(courts_retires)}."
    ok_controle, sortie_controle, _ = executer_adb_serie(
        adb, serie, ["shell", "dumpsys", "package", nom_paquet]
    )
    if ok_controle:
        accordees = parse_permissions_accordees(sortie_controle)
        non_confirmes = [p for p in retires if accordees.get(p, False)]
        if non_confirmes:
            courts_nc = [p.rsplit(".", 1)[-1] for p in non_confirmes]
            texte += (
                f" Non confirmé (toujours accordées) : {', '.join(courts_nc)}"
                " (retrait non confirmé,"
                " vérifiez dans les paramètres de l'appli)."
            )
        else:
            texte += " Retrait vérifié."
    else:
        texte += " Retrait non vérifié (lecture de contrôle impossible)."
    if echecs:
        texte += f" Reste non retiré : {', '.join(p.rsplit('.', 1)[-1] for p, _ in echecs)}."
    return _avec_note(acces, texte)


@mcp_diagnostic.tool()
def verifier_securite() -> str:
    """Bilan sécurité de base : correctif, démarrage, chiffrement.

    Lit le niveau du correctif de sécurité, l'état du démarrage vérifié,
    le chiffrement, les sources inconnues et le débogage USB. Chaque
    point est noté bon, à revoir ou non vérifié.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    donnees = {
        "patch": _lire(adb, serie, ["shell", "getprop", "ro.build.version.security_patch"]),
        "bootloader": _lire(adb, serie, ["shell", "getprop", "ro.boot.verifiedbootstate"])
        or _lire(adb, serie, ["shell", "getprop", "ro.boot.flash.locked"]),
        "crypto": _lire(adb, serie, ["shell", "getprop", "ro.crypto.state"]),
        "sources_inconnues": _lire(
            adb, serie, ["shell", "settings", "get", "global", "install_non_market_apps"]
        ),
        "adb_active": _lire(adb, serie, ["shell", "settings", "get", "global", "adb_enabled"]),
    }
    if all(v is None for v in donnees.values()):
        return _avec_note(acces, "Sécurité illisible sur ce téléphone.")
    return _avec_note(acces, analyser_securite(donnees)["resume"])


@mcp_diagnostic.tool()
def verifier_mises_a_jour() -> str:
    """État des mises à jour : version Android et âge du correctif.

    Dit si le téléphone est à jour, en retard ou très en retard, et
    indique où lancer la mise à jour dans les paramètres.
    """
    acces = preparer_acces()
    if acces["erreur"]:
        return acces["erreur"]
    adb, serie = acces["adb"], acces["serie"]
    version = _lire(adb, serie, ["shell", "getprop", "ro.build.version.release"]) or ""
    patch = _lire(adb, serie, ["shell", "getprop", "ro.build.version.security_patch"]) or ""
    if not version and not patch:
        return _avec_note(acces, "Version illisible sur ce téléphone.")
    return _avec_note(acces, analyser_mises_a_jour(version, patch)["resume"])
