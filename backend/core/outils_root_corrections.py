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
from core.pont_adb import DELAI_ADB_LENT_SECONDES, erreur_courte
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

# Points trimmes separement (un seul appel echoue ne doit pas cacher
# le succes de l'autre, voir root_forcer_trim).
POINTS_TRIM = ("/data", "/cache")

# Modes de redemarrage acceptes. Source unique.
MODES_REDEMARRAGE = ("normal", "recovery", "bootloader")

# Fragments d'erreur ADB qui signalent une liaison coupee (le
# telephone a bien recu l'ordre et redemarre) plutot qu'un refus.
FRAGMENTS_COUPURE_LIAISON = (
    "closed",
    "lost",
    "reset by peer",
    "broken pipe",
    "eof",
    "timeout",
    "timed out",
    "delai depasse",
    "no device",
    "device not found",
    "device offline",
)


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


def commande_nettoyage_crash():
    """Commande de nettoyage des rapports de plantage. Pure.

    UNE seule commande rm avec les trois dossiers en arguments
    (audit final : l'ancien collage "rm -rf a/* rm -rf b/* ..."
    faisait des 2e et 3e "rm -rf" des noms de fichiers a supprimer,
    et un seul code retour ne prouve rien). Le verdict se verifie
    apres coup par `ls -A`, voir root_nettoyer_fichiers_crash.
    Dossiers constants, jamais de parametre.
    """
    return "rm -rf " + " ".join(f"{d}/*" for d in DOSSIERS_CRASH) + " 2>/dev/null"


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


def formater_trim(resultats, ok, erreur="", echecs=()):
    """Texte de reponse pour root_forcer_trim. Fonction pure.

    echecs : [(point, raison)] des points non trimmes, affiches a
    cote des succes (jamais caches, audit risques).
    """
    if not ok:
        return f"Optimisation refusee : {erreur or 'commande refusee'}."
    if not resultats:
        texte = "Optimisation terminee, gain illisible."
    else:
        details = ", ".join(
            f"{point} ({octets // 1024 // 1024} Mo)" for point, octets in resultats
        )
        texte = f"Stockage optimise : {details}."
    if echecs:
        rates = ", ".join(f"{point} ({raison})" for point, raison in echecs)
        texte += f" Non trimme : {rates}."
    return texte


def commande_redemarrage(mode):
    """Commande reboot pour un mode. Fonction pure, None si inconnu."""
    if mode == "normal":
        return "reboot"
    if mode == "recovery":
        return "reboot recovery"
    if mode == "bootloader":
        return "reboot bootloader"
    return None


def coupure_liaison_probable(erreur):
    """Vrai si l'erreur evoque une coupure, pas un refus. Pure.

    Apres un ordre de reboot, ADB perd presque toujours la liaison
    (le telephone s'eteint) : un echec "closed" ou "timeout" veut
    dire "ordre probablement parti", pas "ordre refuse".
    """
    if not erreur:
        return False
    texte = str(erreur).lower()
    return any(fragment in texte for fragment in FRAGMENTS_COUPURE_LIAISON)


# Fragments d'erreur ADB qui signalent un refus net du telephone
# (l'ordre n'est pas parti), pas une coupure apres envoi. Liste
# volontairement courte (audit final) : toute autre erreur reste
# "incertaine", jamais affirmee comme un refus.
FRAGMENTS_REFUS_NET = (
    "permission denied",
    "operation not permitted",
    "not allowed",
    "unauthorized",
    "refused",
)


def refus_redemarrage_net(erreur):
    """Vrai si l'erreur est un refus net, pas une coupure. Pure."""
    if not erreur:
        return False
    texte = str(erreur).lower()
    return any(fragment in texte for fragment in FRAGMENTS_REFUS_NET)


def formater_redemarrage(mode, ok, erreur=""):
    """Texte de reponse pour root_redemarrer. Fonction pure.

    Un echec ADB apres l'ordre se lit en 3 cas (audit final) :
    coupure probable (l'ordre est parti, la liaison tombe parce que
    le telephone redemarre), refus net (l'ordre n'est pas parti),
    ou doute (toute autre erreur : "incertain", jamais affirmee).
    """
    if not ok:
        if coupure_liaison_probable(erreur):
            precision = {
                "normal": "",
                "recovery": " en mode recovery",
                "bootloader": " en mode bootloader",
            }.get(mode, "")
            return (
                f"Ordre de redemarrage envoye{precision}, reponse non "
                "recue (normal : le telephone coupe la liaison en "
                "redemarrant). Verifie l'ecran du telephone."
            )
        if refus_redemarrage_net(erreur):
            return f"Redemarrage refuse : {erreur_courte(erreur)}."
        return (
            "Redemarrage incertain : la liaison est tombee "
            f"({erreur_courte(erreur) if erreur else 'sans detail'}). "
            "C'est normal si le telephone redemarre : "
            "regarde son ecran pour confirmer."
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
    tailles = parse_du(avant["sortie"] or "")
    executer_root(commande_nettoyage_crash(), appareil_id)
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
    # Dossier absent (audit B) : on n'efface rien dans le vide et on
    # le dit ; sinon on verifie apres coup par `ls -A` (audit A).
    if not avant["ok"] and not (avant["sortie"] or "").strip():
        return marquer_non_teste(
            "Cache Dalvik absent ou illisible sur ce telephone, "
            "rien supprime."
        )
    tailles = parse_du(avant["sortie"] or "")
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
    resultats, echecs = [], []
    for point in POINTS_TRIM:
        appel = executer_root(
            f"fstrim -v {point}", appareil_id,
            delai=DELAI_ADB_LENT_SECONDES,
        )
        if appel["ok"]:
            resultats.extend(parse_trim(appel["sortie"] or ""))
        else:
            echecs.append((point, erreur_courte(appel["erreur"], maxi=100)))
    if not resultats and len(echecs) == len(POINTS_TRIM):
        return marquer_non_teste(
            formater_trim(
                [], False,
                ", ".join(f"{p} ({r})" for p, r in echecs),
            )
        )
    return marquer_non_teste(
        formater_trim(resultats, True, echecs=tuple(echecs))
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
