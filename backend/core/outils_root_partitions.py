"""Outils root : partitions et integrite systeme (palier root).

Deux lectures reelles via `su -c`, sans rien modifier :
- root_lire_partitions : espace, points de montage, table by-name.
- root_verifier_integrite : demarrage verifie, verrouillage, montage
  lecture seule de la partition systeme.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import executer_shell
from core.pont_root import executer_root, marquer_non_teste, preparer_root

# Ligne `df -h` : systeme taille utilise dispo pct monte_sur.
MOTIF_DF = re.compile(r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$")

# Ligne /proc/mounts : periph point type options ...
MOTIF_MOUNT = re.compile(r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+")

# Points de montage qui comptent pour le diagnostic.
POINTS_MONTAGE_UTILES = ("/", "/system", "/data", "/cache", "/vendor", "/product")

# Ligne `ls -l /dev/block/by-name` : droits ... date heure lien -> periph.
MOTIF_BYNAME = re.compile(r"^l\S*\s+\d+\s+\S+\s+\S+\s+\d+\s+\S+\s+\S+\s+(\S+)\s+->\s+(\S+)")


def parse_df(texte):
    """Parse `df -h` en [(systeme, taille, utilise, dispo, pct, point)].

    Fonction pure. Ignore l'en tete et les lignes bizarres.
    """
    lignes = []
    if not texte:
        return lignes
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        trouve = MOTIF_DF.match(ligne)
        if not trouve:
            continue
        systeme = trouve.group(1)
        if systeme in ("Filesystem", "systeme"):
            continue
        lignes.append(trouve.groups())
    return lignes


def parse_mounts(texte):
    """Parse /proc/mounts en {point: (type, options)}. Fonction pure."""
    montages = {}
    if not texte:
        return montages
    for ligne in texte.splitlines():
        trouve = MOTIF_MOUNT.match(ligne.strip())
        if trouve:
            _periph, point, fstype, options = trouve.groups()
            montages.setdefault(point, (fstype, options))
    return montages


def parse_byname(texte, limite=40):
    """Parse `ls -l /dev/block/by-name` en [(nom, periph)]. Pure."""
    entrees = []
    if not texte:
        return entrees
    for ligne in texte.splitlines():
        trouve = MOTIF_BYNAME.match(ligne.strip())
        if trouve and len(entrees) < limite:
            entrees.append((trouve.group(1), trouve.group(2)))
    return entrees


def formater_partitions(df, montages, byname):
    """Texte de reponse pour root_lire_partitions. Fonction pure."""
    if not df and not montages:
        return "Partitions illisibles pour le moment."
    morceaux = []
    for systeme, taille, _u, dispo, pct, point in df:
        if point in POINTS_MONTAGE_UTILES:
            morceaux.append(f"{point} : {dispo} libres sur {taille} ({pct})")
    texte = ""
    if morceaux:
        texte = "Partitions : " + ", ".join(morceaux) + "."
    for point in ("/", "/system"):
        if point in montages:
            fstype, options = montages[point]
            mode = "lecture seule" if options.split(",")[0] == "ro" else "lecture et ecriture"
            texte += f" {point} monte en {mode} ({fstype})."
            break
    if byname:
        noms = ", ".join(nom for nom, _p in byname[:25])
        texte += f" {len(byname)} partition(s) nommee(s) : {noms}."
    return texte.strip()


def formater_integrite(props, cmdline, montages):
    """Texte de reponse pour root_verifier_integrite. Fonction pure."""
    verifie = props.get("ro.boot.verifiedbootstate", "")
    verrouille = props.get("ro.boot.flash.locked", "")
    vbmeta = props.get("ro.boot.vbmeta.device_state", "")
    securise = props.get("ro.secure", "")
    debogable = props.get("ro.debuggable", "")
    if "androidboot.verifiedbootstate=" in cmdline:
        extrait = cmdline.split("androidboot.verifiedbootstate=")[1].split()[0]
        verifie = verifie or extrait.strip(",")
    morceaux = []
    if verifie.lower() == "green":
        morceaux.append("demarrage verifie : oui")
    elif verifie:
        morceaux.append(f"demarrage verifie : {verifie}")
    if verrouille == "1":
        morceaux.append("chargeur verrouille")
    elif verrouille == "0":
        morceaux.append("chargeur DEVERROUILLE")
    if vbmeta:
        morceaux.append(f"etat vbmeta : {vbmeta}")
    if securise == "0" or debogable == "1":
        morceaux.append("systeme en mode mise au point")
    for point in ("/", "/system"):
        if point in montages:
            options = montages[point][1]
            if options.split(",")[0] == "rw":
                morceaux.append(f"{point} monte en ecriture (inhabituel)")
            else:
                morceaux.append(f"{point} en lecture seule (normal)")
            break
    if not morceaux:
        return "Integrite illisible pour le moment."
    return "Integrite : " + ", ".join(morceaux) + "."


def parse_getprop_simple(texte):
    """Parse `getprop` en dictionnaire. Fonction pure."""
    infos = {}
    if not texte:
        return infos
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne.startswith("[") or "]:" not in ligne:
            continue
        cle, _, valeur = ligne[1:].partition("]: [")
        valeur = valeur[:-1] if valeur.endswith("]") else valeur
        if cle:
            infos[cle] = valeur
    return infos


@mcp_diagnostic.tool()
def root_lire_partitions() -> str:
    """Lit les partitions : espace libre, montages, table des noms.

    Lecture seule via su, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    df = executer_root("df -h", appareil_id)
    mounts = executer_root("cat /proc/mounts", appareil_id)
    byname = executer_root("ls -l /dev/block/by-name", appareil_id)
    return marquer_non_teste(
        formater_partitions(
            parse_df(df["sortie"] if df["ok"] else ""),
            parse_mounts(mounts["sortie"] if mounts["ok"] else ""),
            parse_byname(byname["sortie"] if byname["ok"] else ""),
        )
    )


@mcp_diagnostic.tool()
def root_verifier_integrite() -> str:
    """Verifie l'integrite : demarrage verifie, verrouillage, montage.

    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    props = executer_shell("getprop", appareil_id)
    cmdline = executer_root("cat /proc/cmdline", appareil_id)
    mounts = executer_root("cat /proc/mounts", appareil_id)
    return marquer_non_teste(
        formater_integrite(
            parse_getprop_simple(props["sortie"] if props["ok"] else ""),
            cmdline["sortie"] if cmdline["ok"] else "",
            parse_mounts(mounts["sortie"] if mounts["ok"] else ""),
        )
    )
