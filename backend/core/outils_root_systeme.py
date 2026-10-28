"""Outils root : fichiers systeme caches et journal noyau (palier root).

Quatre lectures reelles via `su -c`, sans rien modifier :
- root_lister_fichiers_systeme : contenu d'un dossier systeme.
- root_lire_fichier_systeme : contenu texte d'un fichier protege.
- root_lire_erreurs_noyau : erreurs du noyau (dmesg).
- root_lire_paniques_passees : traces de plantages noyau precedents.

Non testes sur appareil roote (aucun ici) : chaque reponse le signale.
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import erreur_courte
from core.pont_root import (
    citer_chemin,
    chemin_lecture_valide,
    executer_root,
    marquer_non_teste,
    preparer_root,
)

# Ligne `ls -la` : droits liens owner groupe taille date nom.
MOTIF_LS_LA = re.compile(
    r"^([bcdlps-][rwxstST-]{9})\s+\d+\s+\S+\s+\S+\s+(\d+)\s+\S+\s+\S+\s+(.+)$"
)

# Taille maxi affichee pour un fichier systeme (octets).
TAILLE_MAXI_FICHIER = 20000

# Longueur maxi d'une ligne affichee d'un fichier (les fichiers
# /proc et /sys tiennent parfois sur une seule ligne tres longue).
LIGNE_MAXI_FICHIER = 500

# Fichiers de trace noyau cherches dans l'ordre.
FICHIERS_PANIQUE = (
    "/sys/fs/pstore/console-ramoops",
    "/sys/fs/pstore/dmesg-ramoops-0",
    "/proc/last_kmsg",
)

# Mots qui designent une erreur dans le journal noyau (filtre fait
# ici en Python, pas par dmesg : les options -T et -l manquent sur
# certaines versions, et leur echec silencieux faisait croire a un
# journal sans erreur). "error" couvre "errors", "failed" "fails".
MOTS_ERREUR_NOYAU = (
    "emerg", "alert", "crit", "err", "error", "fail", "failed",
    "oops", "panic", "die", "warn", "bug", "stuck", "hung",
)

# Adresses MAC dans les journaux (dmesg, last_kmsg) : masquees
# avant affichage, ce sont des identifiants du telephone.
MOTIF_MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")


def masquer_mac(texte):
    """Remplace les adresses MAC par un marqueur. Fonction pure."""
    if not texte:
        return texte
    return MOTIF_MAC.sub("[adresse masquee]", texte)


# Secrets jamais lus ni listes, meme en root (audit B) : mots
# de passe wifi, comptes, cles de verrouillage. Aucune valeur pour
# le diagnostic, et leur contenu ne doit jamais partir vers l'API.
# Complete la liste centrale (pont_root) au niveau du nom de fichier.
NOMS_FICHIERS_SENSIBLES = (
    "wpa_supplicant.conf",
    "wificonfigstore.xml",
    "wificonfigstoresoftap.xml",
    "accounts_ce.db",
    "accounts_de.db",
    "locksettings.db",
    "gatekeeper.password.key",
    "gatekeeper.pattern.key",
    "gatekeeper.gesture.key",
    "password.key",
    "pattern.key",
    "personalkey.key",
)

DOSSIERS_SENSIBLES = (
    "/data/misc/keystore",
    "/data/misc/keychain",
    "/data/misc/wifi",
    "/data/system/users",
)


def chemin_sensible_refuse(chemin):
    """Vrai si chemin touche un secret (wifi, comptes, cles). Pure."""
    if not chemin or not isinstance(chemin, str):
        return False
    normal = chemin.strip().rstrip("/")
    nom = normal.rsplit("/", 1)[-1].lower()
    if nom in NOMS_FICHIERS_SENSIBLES:
        return True
    return any(
        normal == dossier or normal.startswith(dossier + "/")
        for dossier in DOSSIERS_SENSIBLES
    )


def parse_ls_la(texte):
    """Parse `ls -la` en [(nom, taille, droits)]. Fonction pure.

    Les liens symboliques "nom -> cible" sont ramenes a "nom"
    (audit A) : la cible faussait l'affichage, et la taille lue
    est celle du lien, pas du fichier vise.
    """
    entrees = []
    if not texte:
        return entrees
    for ligne in texte.splitlines():
        ligne = ligne.rstrip()
        if not ligne or ligne.startswith("total "):
            continue
        trouve = MOTIF_LS_LA.match(ligne)
        if not trouve:
            continue
        droits, taille, nom = trouve.groups()
        if " -> " in nom:
            nom = nom.split(" -> ", 1)[0]
        if nom in (".", ".."):
            continue
        try:
            entrees.append((nom, int(taille), droits))
        except ValueError:
            continue
    return entrees


def formater_liste_fichiers(dossier, entrees, limite=30):
    """Texte de reponse pour root_lister_fichiers_systeme. Pure."""
    if not entrees:
        return f"Dossier {dossier} vide ou illisible."
    total = sum(taille for _n, taille, _d in entrees)
    lignes = [
        f"Dossier {dossier} : {len(entrees)} entree(s), "
        f"{total // 1024} Ko au total."
    ]
    gros = sorted(entrees, key=lambda e: e[1], reverse=True)[:limite]
    details = "; ".join(
        f"{nom} ({taille // 1024} Ko)" for nom, taille, _d in gros
    )
    lignes.append("Plus gros : " + details + ".")
    return " ".join(lignes)


def est_texte_affichable(contenu):
    """Vrai si le contenu peut s'afficher (pas de binaire). Pure."""
    if contenu is None:
        return False
    return "\x00" not in contenu


def formater_fichier_systeme(chemin, contenu, tronque,
                             lignes_coupees=False, taille_inconnue=False):
    """Texte de reponse pour root_lire_fichier_systeme. Pure.

    tronque : le fichier depasse TAILLE_MAXI_FICHIER, seul le debut
    est montre. lignes_coupees : seules les premieres lignes sont
    montrees. taille_inconnue : la taille n'a pas pu etre lue, on ne
    sait pas si tout est montre (audit risques, extrait honnete).
    """
    if not est_texte_affichable(contenu):
        return f"Fichier {chemin} non texte (binaire), affichage refuse."
    if not contenu.strip():
        return f"Fichier {chemin} vide."
    texte = f"Contenu de {chemin} :\n{contenu.rstrip()}"
    if tronque:
        texte += "\n[debut du fichier, suite non affichee]"
    if lignes_coupees:
        texte += "\n[seules les premieres lignes sont affichees]"
    if taille_inconnue:
        texte += "\n[longueur totale inconnue, fin peut-etre manquante]"
    return texte


# Une ligne est une erreur si un mot d'erreur y commence un mot
# (pas precede d'une lettre : "debug" et "terrible" ne comptent pas).
MOTIF_LIGNE_ERREUR = re.compile(
    r"(?<![a-z])(?:" + "|".join(MOTS_ERREUR_NOYAU) + r")",
    re.IGNORECASE,
)


def ligne_est_erreur(ligne):
    """Vrai si la ligne parle d'une erreur noyau. Fonction pure."""
    if not ligne:
        return False
    return bool(MOTIF_LIGNE_ERREUR.search(ligne))


def parse_dmesg_erreurs(texte):
    """Garde les lignes d'erreur de dmesg, bornees. Fonction pure.

    Renvoie (lignes_erreur, lignes_lues) : le total lu permet de
    dire honnetement "journal vide" au lieu de "aucune erreur".
    """
    if not texte:
        return [], 0
    lignes = []
    lues = 0
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        lues += 1
        if ligne_est_erreur(ligne):
            lignes.append(masquer_mac(ligne[:300]))
    return lignes, lues


def formater_erreurs_noyau(lignes, limite, lignes_lues=0):
    """Texte de reponse pour root_lire_erreurs_noyau. Pure.

    lignes_lues distingue le journal vide ("impossible de conclure",
    audit A) d'un journal sans erreur. Quand les erreurs atteignent
    la limite, le total est un minimum ("Au moins", audit B).
    """
    if not lignes:
        if lignes_lues <= 0:
            return "Journal noyau vide ou illisible, impossible de conclure."
        return (
            f"Aucune erreur noyau sur les {lignes_lues} derniere(s) "
            "ligne(s) du journal."
        )
    if len(lignes) >= limite:
        texte = (
            f"Au moins {len(lignes)} ligne(s) d'erreur noyau "
            f"({limite} dernieres affichees) :\n"
        )
    else:
        texte = (
            f"{len(lignes)} ligne(s) d'erreur noyau "
            f"(dernieres {len(lignes)} affichees) :\n"
        )
    return texte + "\n".join(lignes[-limite:])


def parse_paniques(sorties):
    """Assemble les traces de panique trouvees. Fonction pure.

    sorties : [(chemin, contenu ou "")]. Ne garde que les contenus
    non vides, bornes a 2000 caracteres chacun, MAC masquees.
    """
    traces = []
    for chemin, contenu in sorties:
        if contenu and contenu.strip():
            traces.append((chemin, masquer_mac(contenu.strip()[:2000])))
    return traces


def formater_paniques(traces, lectures_reussies=1, presents=None):
    """Texte de reponse pour root_lire_paniques_passees. Pure.

    lectures_reussies vaut 0 quand aucun fichier de trace n'a pu
    etre lu : on dit "illisible" au lieu de "aucune trace" (audit A).
    presents distingue les fichiers absents (normal sur beaucoup de
    modeles) des fichiers presents mais vides (audit B). None
    (defaut) : existence inconnue, message historique.
    """
    if lectures_reussies is None:
        lectures_reussies = 1
    if not traces:
        if lectures_reussies <= 0:
            return "Traces de plantage illisibles, impossible de conclure."
        if presents == 0:
            return (
                "Aucune trace de plantage noyau precedent "
                "(fichiers de trace absents sur ce modele)."
            )
        if presents:
            return (
                "Aucune trace de plantage noyau precedent "
                "(fichiers presents mais vides)."
            )
        return "Aucune trace de plantage noyau precedent."
    morceaux = [f"{len(traces)} trace(s) de plantage noyau precedent."]
    for chemin, extrait in traces:
        morceaux.append(f"{chemin} :\n{extrait}")
    return "\n".join(morceaux)


@mcp_diagnostic.tool()
def root_lister_fichiers_systeme(dossier: str = "/system") -> str:
    """Liste le contenu d'un dossier systeme protege.

    dossier : chemin absolu sous /system, /vendor, /data, /proc, /sys
    ou assimilé (/dev, /apex, /sbin, /cache, /product, /odm, /oem).
    Les dossiers a secrets (wifi, cles, comptes) sont refuses.
    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    # Secrets d'abord (audit final) : un dossier a secrets sous un
    # chemin par ailleurs interdit recoit le message "secrets".
    if chemin_sensible_refuse(dossier or ""):
        return marquer_non_teste(
            "Erreur : dossier refuse, il peut contenir des secrets "
            "(mot de passe wifi, compte, cle). L'outil ne liste jamais "
            "ces dossiers."
        )
    if not chemin_lecture_valide(dossier or ""):
        return marquer_non_teste(
            "Erreur : dossier refuse. Donne un chemin absolu sous un "
            "dossier systeme connu (/system, /vendor, /data, /proc, "
            "/sys, /dev, /apex, /sbin, /cache, /product, /odm, /oem). "
            "Les donnees perso (applis, photos, cles) sont exclues."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root(f"ls -la {citer_chemin(dossier)}", appareil_id)
    if not resultat["ok"]:
        return marquer_non_teste(
            f"Dossier illisible : {erreur_courte(resultat['erreur'])}"
        )
    return marquer_non_teste(
        formater_liste_fichiers(
            dossier.strip(), parse_ls_la(resultat["sortie"])
        )
    )


@mcp_diagnostic.tool()
def root_lire_fichier_systeme(chemin: str, limite_lignes: int = 50) -> str:
    """Lit le debut texte d'un fichier systeme protege.

    chemin : fichier absolu sous un dossier systeme connu (voir
    root_lister_fichiers_systeme). Les fichiers a secrets (mot de
    passe wifi, comptes, cles) sont refuses. limite_lignes : 1 a
    200, 50 par defaut. Fichiers binaires refuses. Lecture seule.
    Non teste sur appareil roote.
    """
    try:
        limite_lignes = int(limite_lignes)
    except (TypeError, ValueError):
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 200."
        )
    if not 1 <= limite_lignes <= 200:
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 1 et 200."
        )
    # Secrets d'abord (audit final) : un fichier a secrets sous un
    # chemin par ailleurs interdit recoit le message "secrets".
    if chemin_sensible_refuse(chemin or ""):
        return marquer_non_teste(
            "Erreur : fichier refuse, il peut contenir des secrets "
            "(mot de passe wifi, compte, cle). L'outil ne lit jamais "
            "ces fichiers."
        )
    if not chemin_lecture_valide(chemin or ""):
        return marquer_non_teste(
            "Erreur : chemin refuse. Donne un fichier absolu sous un "
            "dossier systeme connu (/system, /vendor, /data, /proc, "
            "/sys, /dev, /apex, /sbin, /cache, /product, /odm, /oem). "
            "Les donnees perso (applis, photos, cles) sont exclues."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    taille = executer_root(
        f"wc -c -l < {citer_chemin(chemin)}", appareil_id
    )
    # Taille en octets et en lignes (audit A : `wc -c -l`), None si
    # illisible (audit B : mention "longueur inconnue").
    total, total_lignes = None, None
    if taille["ok"]:
        try:
            morceaux = taille["sortie"].strip().split()
            total, total_lignes = int(morceaux[0]), int(morceaux[1])
        except (ValueError, IndexError):
            total, total_lignes = None, None
    resultat = executer_root(
        f"head -c {TAILLE_MAXI_FICHIER} {citer_chemin(chemin)}",
        appareil_id,
    )
    if not resultat["ok"]:
        return marquer_non_teste(
            f"Fichier illisible : {erreur_courte(resultat['erreur'])}"
        )
    contenu = resultat["sortie"]
    lignes = [l[:LIGNE_MAXI_FICHIER] for l in contenu.splitlines()]
    tronque = total is not None and total > TAILLE_MAXI_FICHIER
    coupees = total_lignes is not None and total_lignes > limite_lignes
    return marquer_non_teste(
        formater_fichier_systeme(
            chemin.strip(), "\n".join(lignes[:limite_lignes]), tronque,
            lignes_coupees=coupees, taille_inconnue=total is None,
        )
    )


@mcp_diagnostic.tool()
def root_lire_erreurs_noyau(limite: int = 100) -> str:
    """Lit les erreurs recentes du noyau (dmesg).

    limite : lignes du journal examinees (10 a 500, 100 par defaut),
    les erreurs trouvees sont affichees. Lecture seule, ne modifie
    rien. Non teste sur appareil roote.
    """
    try:
        limite = int(limite)
    except (TypeError, ValueError):
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 10 et 500."
        )
    if not 10 <= limite <= 500:
        return marquer_non_teste(
            "Erreur : limite invalide, donne un nombre entre 10 et 500."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    # dmesg brut (audit A) : les options -T et -l manquent sur
    # certaines versions et leur echec silencieux faisait croire a
    # un journal sans erreur. Le tri se fait ici, en Python.
    resultat = executer_root(
        f"dmesg 2>/dev/null | tail -n {limite}",
        appareil_id,
    )
    if not resultat["ok"]:
        return marquer_non_teste(
            f"Noyau illisible : {erreur_courte(resultat['erreur'])}"
        )
    lignes, lues = parse_dmesg_erreurs(resultat["sortie"])
    return marquer_non_teste(formater_erreurs_noyau(lignes, limite, lues))


@mcp_diagnostic.tool()
def root_lire_paniques_passees() -> str:
    """Lit les traces de plantages noyau precedents (pstore, last_kmsg).

    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    presents = None
    liste = executer_root(
        "ls -d " + " ".join(FICHIERS_PANIQUE) + " 2>/dev/null", appareil_id
    )
    if liste["ok"] or liste["sortie"]:
        presents = sum(
            1 for ligne in liste["sortie"].splitlines()
            if ligne.strip() in FICHIERS_PANIQUE
        )
    sorties = []
    reussies = 0
    for chemin in FICHIERS_PANIQUE:
        resultat = executer_root(
            f"head -c 4000 {chemin} 2>/dev/null", appareil_id
        )
        if resultat["ok"]:
            reussies += 1
        sorties.append(
            (chemin, resultat["sortie"] if resultat["ok"] else "")
        )
    return marquer_non_teste(
        formater_paniques(parse_paniques(sorties), reussies, presents)
    )
