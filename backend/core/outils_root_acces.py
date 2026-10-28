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
    """Devine Magisk, KernelSU ou autre depuis `ls /data/adb`. Pure.

    Compare des noms entiers (audit A) : le test "su" en simple
    sous-chaine repondait present pour presque tout ("super",
    "result"...), d'ou des faux positifs.
    """
    noms = set((sortie_ls_adb or "").lower().split())
    if any(n == "magisk" or n.startswith("magisk.") for n in noms):
        return "Magisk probable"
    if any(n == "ksu" or n.startswith("ksu.") for n in noms):
        return "KernelSU probable"
    if "su" in noms:
        return "binaire su present, gestionnaire inconnu"
    return "gestionnaire inconnu"


def parse_modules_magisk(sortie_ls, sortie_props):
    """Parse modules : (noms_dossiers, {id: nom}). Fonction pure.

    Chaque name= se rattache au dernier id= vu (audit A) : l'ancien
    appariement par rang melangeait les noms des qu'un module.prop
    oubliait son name=.
    """
    dossiers = []
    if sortie_ls:
        for ligne in sortie_ls.splitlines():
            nom = ligne.strip()
            if nom and not nom.startswith("."):
                dossiers.append(nom)
    modules = {}
    courant = None
    if sortie_props:
        for ligne in sortie_props.splitlines():
            ligne = ligne.strip()
            trouve_id = MOTIF_MODULE_ID.match(ligne)
            if trouve_id:
                courant = trouve_id.group(1).strip()
                modules.setdefault(courant, courant)
                continue
            trouve_nom = MOTIF_MODULE_NOM.match(ligne)
            if trouve_nom and courant:
                nom = trouve_nom.group(1).strip()
                if nom:
                    modules[courant] = nom
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
