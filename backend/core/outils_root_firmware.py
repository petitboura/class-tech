"""Outils root : firmware et slot de demarrage (palier root).

Une lecture reelle et une correction douce :
- root_lire_firmware : noyau, bootloader, bande de base, compilation,
  slot A/B actif.
- root_valider_slot_demarre : marque le slot actuel comme bon (utile
  apres une mise a jour qui refuse de se valider).

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import erreur_courte, executer_shell
from core.pont_root import executer_root, marquer_non_teste, preparer_root

# Proprietes lues pour decrire le firmware. Source unique.
CLES_FIRMWARE = {
    "ro.build.fingerprint": "emprunte",
    "ro.build.version.release": "android",
    "ro.build.version.sdk": "sdk",
    "ro.build.version.security_patch": "patch_securite",
    "ro.build.date": "date_compilation",
    "ro.build.id": "compilation",
    "ro.boot.bootloader": "bootloader",
    "ro.boot.slot_suffix": "slot",
    "gsm.version.baseband": "bande_base",
    "ro.product.manufacturer": "fabricant",
    "ro.product.model": "modele",
}


def parse_getprop_firmware(texte):
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


def parse_version_noyau(sortie_proc_version):
    """Tire la version du noyau de /proc/version. Fonction pure."""
    if not sortie_proc_version:
        return ""
    premiere = sortie_proc_version.strip().splitlines()[0]
    morceaux = premiere.split()
    if len(morceaux) >= 3 and morceaux[0] == "Linux":
        return f"{morceaux[0]} {morceaux[1]} {morceaux[2]}"
    return premiere[:120]


def normaliser_slot(brut):
    """Normalise le suffixe de slot : "_a", "_b" ou "". Pure.

    `getprop ro.boot.slot_suffix` renvoie "_a" (ou "[_a]"). Tout
    autre texte donne "" : on ne valide jamais un slot douteux
    (audit risques).
    """
    if not brut or not isinstance(brut, str):
        return ""
    lignes = brut.strip().splitlines()
    if not lignes:
        return ""
    texte = lignes[0].strip().strip("[]").strip().lower()
    if texte in ("_a", "a"):
        return "_a"
    if texte in ("_b", "b"):
        return "_b"
    return ""


def parse_slot_bootctl(texte):
    """Numero de slot depuis `bootctl get-current-slot`. Pure.

    Renvoie "0", "1" ou None (bootctl absent ou reponse illisible).
    """
    if not texte or not isinstance(texte, str):
        return None
    for morceau in texte.strip().split():
        if morceau in ("0", "1"):
            return morceau
    return None


def formater_firmware(infos, noyau):
    """Texte de reponse pour root_lire_firmware. Fonction pure."""
    morceaux = []
    modele = infos.get("ro.product.model", "")
    fabricant = infos.get("ro.product.manufacturer", "")
    nom = " ".join(p for p in (fabricant, modele) if p).strip()
    if nom:
        morceaux.append(f"appareil {nom}")
    if noyau:
        morceaux.append(f"noyau {noyau}")
    android = infos.get("ro.build.version.release", "")
    if android:
        morceaux.append(f"Android {android}")
    patch = infos.get("ro.build.version.security_patch", "")
    if patch:
        morceaux.append(f"correctif du {patch}")
    bootloader = infos.get("ro.boot.bootloader", "")
    if bootloader:
        morceaux.append(f"bootloader {bootloader}")
    bande = infos.get("gsm.version.baseband", "")
    if bande:
        morceaux.append(f"bande de base {bande}")
    slot = infos.get("ro.boot.slot_suffix", "")
    if slot:
        morceaux.append(f"slot actif {slot}")
    date = infos.get("ro.build.date", "")
    if date:
        morceaux.append(f"compile le {date}")
    if not morceaux:
        return "Firmware illisible pour le moment."
    if not slot:
        morceaux.append("pas de double slot A/B")
    return "Firmware : " + ", ".join(morceaux) + "."


def formater_validation_slot(slot, ok_bootctl, erreur=""):
    """Texte de reponse pour root_valider_slot_demarre. Pure."""
    if not slot:
        return (
            "Pas de double slot A/B sur ce telephone, "
            "rien a valider."
        )
    if ok_bootctl:
        return (
            f"Slot {slot} marque comme bon. La prochaine mise a jour "
            "pourra basculer sans crainte. Validation definitive : "
            "a ne faire que si le telephone fonctionne bien."
        )
    return f"Slot {slot} non valide : {erreur or 'commande refusee'}."


@mcp_diagnostic.tool()
def root_lire_firmware() -> str:
    """Lit le firmware : noyau, bootloader, bande de base, slot actif.

    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    props = executer_shell("getprop", appareil_id)
    version = executer_root("cat /proc/version", appareil_id)
    return marquer_non_teste(
        formater_firmware(
            parse_getprop_firmware(props["sortie"] if props["ok"] else ""),
            parse_version_noyau(version["sortie"] if version["ok"] else ""),
        )
    )


@mcp_diagnostic.tool()
def root_valider_slot_demarre() -> str:
    """Marque le slot de demarrage actuel comme bon (telephones A/B).

    Correction douce : sert quand une mise a jour refuse de se
    valider alors que le telephone demarre bien. Sans effet sur les
    telephones sans double slot, et ne refait rien si le slot est
    deja valide. Validation definitive. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    props = executer_shell("getprop ro.boot.slot_suffix", appareil_id)
    brut = props["sortie"] if props["ok"] else ""
    slot = normaliser_slot(brut)
    if not slot:
        if brut.strip():
            return marquer_non_teste(
                "Slot de demarrage illisible, rien modifie."
            )
        return marquer_non_teste(formater_validation_slot("", False))
    actuel = executer_root("bootctl get-current-slot", appareil_id)
    numero = parse_slot_bootctl(actuel["sortie"] if actuel["ok"] else "")
    if numero is not None:
        marque = executer_root(
            f"bootctl is-marked-successful {numero}", appareil_id
        )
        if marque["ok"]:
            return marquer_non_teste(
                f"Slot {slot} deja marque comme bon, rien modifie."
            )
    resultat = executer_root("bootctl mark-boot-successful", appareil_id)
    return marquer_non_teste(
        formater_validation_slot(
            slot, resultat["ok"],
            erreur_courte(resultat["erreur"]) if not resultat["ok"] else "",
        )
    )
