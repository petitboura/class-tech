"""Outils root : acces super-utilisateur (palier root).

Deux lectures reelles via `su -c`, sans rien modifier :
- root_verifier_acces : root actif ou non, uid, gestionnaire probable,
  etat SELinux.
- root_lire_infos_root : version de su, modules systeme installes.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_shell, preparer_appel
from core.pont_root import (
    executer_root,
    marquer_non_teste,
    message_root_absent,
    message_root_desactive,
    outils_root_actifs,
    preparer_root,
    verifier_root,
)


def deviner_gestionnaire_root(sortie_ls_adb):
    """Devine Magisk, KernelSU ou autre depuis `ls /data/adb`. Pure.

    Compare des noms entiers (audits A et B) : le test "su" en
    simple sous-chaine repondait present pour presque tout ("super",
    "result", "asus_config"...), d'ou des faux positifs.
    """
    mots = set()
    for ligne in (sortie_ls_adb or "").splitlines():
        for mot in ligne.replace("/", " ").split():
            mots.add(mot.strip().lower())
    if any(
        m == "magisk" or m.startswith("magisk.") or m.startswith("magisk_")
        for m in mots
    ):
        return "Magisk probable"
    if any(
        m in ("ksu", "kernelsu")
        or m.startswith("ksu.")
        or m.startswith("ksu_")
        for m in mots
    ):
        return "KernelSU probable"
    if "su" in mots:
        return "binaire su present, gestionnaire inconnu"
    return "gestionnaire inconnu"


def parse_modules_magisk(sortie_ls, sortie_props):
    """Parse modules : (noms_dossiers, {id: nom}). Fonction pure.

    Les module.prop sont lus en un seul `cat` : chaque ligne id=
    ouvre un nouveau module, la ligne name= suivante s'y rattache.
    Un module sans name= garde son id, sans decaler les suivants
    (audits A et B, decalage par rang corrige).
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
            if ligne.startswith("id=") and len(ligne) > 3:
                courant = ligne[3:].strip()
                if courant:
                    modules.setdefault(courant, courant)
                else:
                    courant = None
            elif ligne.startswith("name=") and courant:
                nom = ligne[5:].strip()
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
    if not outils_root_actifs():
        return marquer_non_teste(message_root_desactive())
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
