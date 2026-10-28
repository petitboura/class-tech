"""Outils root : acces super-utilisateur (palier root).

Deux lectures reelles via `su -c`, sans rien modifier :
- root_verifier_acces : root actif ou non, uid, gestionnaire probable,
  etat SELinux.
- root_lire_infos_root : version de su, modules systeme installes.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_shell, preparer_appel
from core.pont_root import (
    executer_root,
    marquer_non_teste,
    message_root_absent,
    parse_uid_root,
    preparer_root,
    verifier_root,
)

# Ligne module.prop : id=... ou name=...
MOTIF_MODULE_ID = re.compile(r"^id=(.+)$", re.MULTILINE)
MOTIF_MODULE_NOM = re.compile(r"^name=(.+)$", re.MULTILINE)


def deviner_gestionnaire_root(sortie_ls_adb):
    """Devine Magisk, KernelSU ou autre depuis `ls /data/adb`. Pure."""
    texte = sortie_ls_adb or ""
    if "magisk" in texte:
        return "Magisk probable"
    if "ksu" in texte:
        return "KernelSU probable"
    if "su" in texte:
        return "binaire su present, gestionnaire inconnu"
    return "gestionnaire inconnu"


def parse_modules_magisk(sortie_ls, sortie_props):
    """Parse modules : (noms_dossiers, {id: nom}). Fonction pure."""
    dossiers = []
    if sortie_ls:
        for ligne in sortie_ls.splitlines():
            nom = ligne.strip()
            if nom and not nom.startswith("."):
                dossiers.append(nom)
    modules = {}
    if sortie_props:
        ids = MOTIF_MODULE_ID.findall(sortie_props)
        noms = MOTIF_MODULE_NOM.findall(sortie_props)
        for rang, identifiant in enumerate(ids):
            nom = noms[rang].strip() if rang < len(noms) else ""
            modules[identifiant.strip()] = nom or identifiant.strip()
    return dossiers, modules


def formater_verif_acces(uid, gestionnaire, selinux):
    """Texte de reponse pour root_verifier_acces. Fonction pure."""
    if uid != 0:
        return message_root_absent()
    morceaux = ["Root actif (uid 0)"]
    if gestionnaire:
        morceaux.append(f"gestionnaire : {gestionnaire}")
    if selinux:
        morceaux.append(f"SELinux : {selinux}")
    return ". ".join(morceaux) + "."


def formater_infos_root(version_su, dossiers, modules):
    """Texte de reponse pour root_lire_infos_root. Fonction pure."""
    morceaux = []
    if version_su:
        morceaux.append(f"su version {version_su}")
    else:
        morceaux.append("version de su illisible")
    if dossiers:
        morceaux.append(f"{len(dossiers)} module(s) : " + ", ".join(dossiers[:20]))
        if len(dossiers) > 20:
            morceaux[-1] += " et d'autres"
    else:
        morceaux.append("aucun module detecte")
    return "Root : " + ", ".join(morceaux) + "."


@mcp_diagnostic.tool()
def root_verifier_acces() -> str:
    """Verifie que le telephone est roote et que root repond.

    Lit l'uid via su, devine le gestionnaire (Magisk, KernelSU) et
    lit l'etat SELinux. Lecture seule, ne modifie rien.
    Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return marquer_non_teste(erreur)
    verif = verifier_root(appareil_id)
    if not verif["root"]:
        return marquer_non_teste(message_root_absent(verif["detail"]))
    gestionnaire = ""
    contenu = executer_root("ls /data/adb", appareil_id)
    if contenu["ok"]:
        gestionnaire = deviner_gestionnaire_root(contenu["sortie"])
    selinux = ""
    etat = executer_shell("getenforce", appareil_id)
    if etat["ok"] and etat["sortie"].strip():
        selinux = etat["sortie"].strip().splitlines()[0][:40]
    return marquer_non_teste(
        formater_verif_acces(verif["uid"], gestionnaire, selinux)
    )


@mcp_diagnostic.tool()
def root_lire_infos_root() -> str:
    """Lit la version de su et les modules systeme installes.

    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    version_su = ""
    for commande in ("su --version", "su -v"):
        resultat = executer_shell(commande, appareil_id)
        if resultat["ok"] and resultat["sortie"].strip():
            version_su = resultat["sortie"].strip().splitlines()[0][:60]
            break
    dossiers, modules = [], {}
    liste = executer_root("ls /data/adb/modules", appareil_id)
    if liste["ok"]:
        props = executer_root(
            "cat /data/adb/modules/*/module.prop", appareil_id
        )
        dossiers, modules = parse_modules_magisk(
            liste["sortie"], props["sortie"] if props["ok"] else ""
        )
    if modules and not dossiers:
        dossiers = sorted(modules.values())
    return marquer_non_teste(formater_infos_root(version_su, dossiers, modules))
