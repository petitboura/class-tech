"""Outils root : corrections profondes (palier root).

Quatre actions reelles via `su -c`, chacune avec confirmation exigee
cote Classinus (OUTILS_SENSIBLES) :
- root_nettoyer_fichiers_crash : supprime les rapports de plantage.
- root_vider_cache_dalvik : vide le cache des applis (reboot conseille).
- root_forcer_trim : optimise le stockage (fstrim).
- root_redemarrer : redemarre (normal, recovery ou bootloader).

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
Jamais de remise a zero d'usine ici : trop destructeur.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import DELAI_ADB_LENT_SECONDES
from core.pont_root import executer_root, marquer_non_teste, preparer_root

# Dossiers de rapports de plantage nettoyes (contenu seul, pas le dossier).
DOSSIERS_CRASH = (
    "/data/tombstones",
    "/data/system/dropbox",
    "/data/anr",
)

# Ligne `du -sh dossier` : taille dossier.
MOTIF_DU = re.compile(r"^(\S+)\s+(\S+)\s*$")

# Sortie `fstrim -v` : /data: X bytes trimmed.
MOTIF_TRIM = re.compile(r"(\S+):\s*([\d,]+)\s*bytes trimmed")

# Modes de redemarrage acceptes. Source unique.
MODES_REDEMARRAGE = ("normal", "recovery", "bootloader")


def parse_du(texte):
    """Parse `du -sh` en {dossier: taille}. Fonction pure."""
    tailles = {}
    if not texte:
        return tailles
    for ligne in texte.splitlines():
        trouve = MOTIF_DU.match(ligne.strip())
        if trouve:
            tailles[trouve.group(2)] = trouve.group(1)
    return tailles


def parse_ls_restes(texte):
    """Contenu restant d'apres `ls -A`, en liste de noms. Pure."""
    if not texte:
        return []
    return [l.strip() for l in texte.splitlines() if l.strip()]


def formater_nettoyage(tailles, restes):
    """Texte de reponse pour root_nettoyer_fichiers_crash. Pure.

    restes : {dossier: [noms restants]} releve apres suppression.
    """
    sales = {d: fichiers for d, fichiers in restes.items() if fichiers}
    if sales:
        details = ", ".join(
            f"{d} ({len(fichiers)} fichier(s) restant(s))"
            for d, fichiers in sales.items()
        )
        return (
            "Nettoyage partiel, certains fichiers resistent : "
            f"{details}. Le reste est supprime."
        )
    details = ", ".join(
        f"{d} ({tailles.get(d, '?')})" for d in DOSSIERS_CRASH
    )
    return f"Rapports de plantage supprimes : {details}."


def formater_dalvik(taille_avant, restes):
    """Texte de reponse pour root_vider_cache_dalvik. Pure.

    restes : [noms restants] releves apres suppression.
    """
    if restes:
        return (
            f"Cache Dalvik partiellement vide, {len(restes)} "
            "element(s) resiste(nt). Redemarre le telephone quand meme, "
            "le prochain demarrage sera plus long."
        )
    texte = "Cache Dalvik vide"
    if taille_avant:
        texte += f" ({taille_avant} liberes)"
    return texte + ". Redemarre le telephone, le prochain demarrage sera plus long."


def parse_trim(texte):
    """Parse la sortie de fstrim en [(point, octets)]. Fonction pure."""
    resultats = []
    if not texte:
        return resultats
    for trouve in MOTIF_TRIM.finditer(texte):
        try:
            octets = int(trouve.group(2).replace(",", ""))
        except ValueError:
            continue
        resultats.append((trouve.group(1), octets))
    return resultats


def formater_trim(resultats, ok, erreur=""):
    """Texte de reponse pour root_forcer_trim. Fonction pure."""
    if not ok:
        return f"Optimisation refusee : {erreur or 'commande refusee'}."
    if not resultats:
        return "Optimisation terminee, gain illisible."
    details = ", ".join(
        f"{point} ({octets // 1024 // 1024} Mo)" for point, octets in resultats
    )
    return f"Stockage optimise : {details}."


def commande_redemarrage(mode):
    """Commande reboot pour un mode. Fonction pure, None si inconnu."""
    if mode == "normal":
        return "reboot"
    if mode == "recovery":
        return "reboot recovery"
    if mode == "bootloader":
        return "reboot bootloader"
    return None


def formater_redemarrage(mode, ok, erreur=""):
    """Texte de reponse pour root_redemarrer. Fonction pure.

    Un echec ADB ne veut pas dire echec du redemarrage (audit A) :
    la connexion tombe justement quand le telephone redemarre. On
    reste honnete : incertain, verifier l'ecran du telephone.
    """
    if not ok:
        return (
            "Redemarrage incertain : la liaison est tombee "
            f"({erreur or 'sans detail'}). C'est normal si le telephone "
            "redemarre : regarde son ecran pour confirmer."
        )
    if mode == "normal":
        return "Telephone en cours de redemarrage. Attends son retour."
    if mode == "recovery":
        return (
            "Telephone en cours de redemarrage en mode recovery. "
            "Pour revenir : choisis redemarrer avec les boutons du "
            "telephone (volume pour naviguer, marche pour valider)."
        )
    return (
        "Telephone en cours de redemarrage en mode bootloader. "
        "Pour revenir : choisis redemarrer avec les boutons du "
        "telephone (volume pour naviguer, marche pour valider)."
    )


@mcp_diagnostic.tool()
def root_nettoyer_fichiers_crash() -> str:
    """Supprime les rapports de plantage (tombstones, dropbox, ANR).

    Correction : libere de la place, ne touche ni aux applis ni aux
    donnees. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    avant = executer_root(f"du -sh {' '.join(DOSSIERS_CRASH)}", appareil_id)
    tailles = parse_du(avant["sortie"] if avant["ok"] else "")
    # UNE seule commande rm (audit A) : l'ancienne version collait
    # "rm -rf a/* rm -rf b/* ...", donc les 2e et 3e "rm -rf"
    # devenaient des noms de fichiers a supprimer dans le dossier
    # courant. Ici les dossiers sont constants, jamais de parametre.
    executer_root(
        "rm -rf " + " ".join(f"{d}/*" for d in DOSSIERS_CRASH)
        + " 2>/dev/null",
        appareil_id,
    )
    restes = {}
    for dossier in DOSSIERS_CRASH:
        releve = executer_root(f"ls -A {dossier} 2>/dev/null", appareil_id)
        restes[dossier] = (
            parse_ls_restes(releve["sortie"]) if releve["ok"] else []
        )
    return marquer_non_teste(formater_nettoyage(tailles, restes))


@mcp_diagnostic.tool()
def root_vider_cache_dalvik() -> str:
    """Vide le cache Dalvik des applis (reconstruction au reboot).

    Correction profonde : ne touche ni aux applis ni aux donnees,
    mais le prochain demarrage sera plus long. Reboot conseille apres.
    Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    avant = executer_root("du -sh /data/dalvik-cache", appareil_id)
    tailles = parse_du(avant["sortie"] if avant["ok"] else "")
    executer_root(
        "rm -rf /data/dalvik-cache/* 2>/dev/null", appareil_id,
        delai=DELAI_ADB_LENT_SECONDES,
    )
    releve = executer_root(
        "ls -A /data/dalvik-cache 2>/dev/null", appareil_id
    )
    restes = parse_ls_restes(releve["sortie"]) if releve["ok"] else []
    return marquer_non_teste(
        formater_dalvik(tailles.get("/data/dalvik-cache", ""), restes)
    )


@mcp_diagnostic.tool()
def root_forcer_trim() -> str:
    """Optimise le stockage (fstrim sur les donnees et le cache).

    Maintenance profonde : dit au stockage quelles zones sont libres.
    Ne touche ni aux applis ni aux donnees. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root(
        "fstrim -v /data; fstrim -v /cache", appareil_id,
        delai=DELAI_ADB_LENT_SECONDES,
    )
    if not resultat["ok"] and not resultat["sortie"]:
        return marquer_non_teste(
            formater_trim([], False, resultat["erreur"])
        )
    return marquer_non_teste(
        formater_trim(parse_trim(resultat["sortie"]), True)
    )


@mcp_diagnostic.tool()
def root_redemarrer(mode: str = "normal") -> str:
    """Redemarre le telephone (normal, recovery ou bootloader).

    mode : normal, recovery ou bootloader. Correction profonde : le
    telephone quitte le diagnostic le temps de redemarrer.
    Non teste sur appareil roote.
    """
    mode = (mode or "").strip().lower()
    if mode not in MODES_REDEMARRAGE:
        return marquer_non_teste(
            "Erreur : mode inconnu. Valeurs acceptees : "
            + ", ".join(MODES_REDEMARRAGE)
            + "."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root(commande_redemarrage(mode), appareil_id)
    return marquer_non_teste(
        formater_redemarrage(
            mode, resultat["ok"],
            resultat["erreur"] if not resultat["ok"] else "",
        )
    )
