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

# Fichiers de trace noyau cherches dans l'ordre.
FICHIERS_PANIQUE = (
    "/sys/fs/pstore/console-ramoops",
    "/sys/fs/pstore/dmesg-ramoops-0",
    "/proc/last_kmsg",
)


def parse_ls_la(texte):
    """Parse `ls -la` en [(nom, taille, droits)]. Fonction pure."""
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


def formater_fichier_systeme(chemin, contenu, tronque):
    """Texte de reponse pour root_lire_fichier_systeme. Pure."""
    if not est_texte_affichable(contenu):
        return f"Fichier {chemin} non texte (binaire), affichage refuse."
    if not contenu.strip():
        return f"Fichier {chemin} vide."
    texte = f"Contenu de {chemin} :\n{contenu.rstrip()}"
    if tronque:
        texte += "\n[debut du fichier, suite non affichee]"
    return texte


def parse_dmesg_erreurs(texte):
    """Garde les lignes dmesg utiles, bornees. Fonction pure."""
    if not texte:
        return []
    lignes = []
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if ligne:
            lignes.append(ligne[:300])
    return lignes


def formater_erreurs_noyau(lignes, limite):
    """Texte de reponse pour root_lire_erreurs_noyau. Pure."""
    if not lignes:
        return "Aucune erreur noyau recente."
    texte = (
        f"{len(lignes)} ligne(s) d'erreur noyau "
        f"(dernieres {min(len(lignes), limite)} affichees) :\n"
    )
    return texte + "\n".join(lignes[-limite:])


def parse_paniques(sorties):
    """Assemble les traces de panique trouvees. Fonction pure.

    sorties : [(chemin, contenu ou "")]. Ne garde que les contenus
    non vides, bornes a 2000 caracteres chacun.
    """
    traces = []
    for chemin, contenu in sorties:
        if contenu and contenu.strip():
            traces.append((chemin, contenu.strip()[:2000]))
    return traces


def formater_paniques(traces):
    """Texte de reponse pour root_lire_paniques_passees. Pure."""
    if not traces:
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
    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    if not chemin_lecture_valide(dossier or ""):
        return marquer_non_teste(
            "Erreur : dossier refuse. Donne un chemin absolu sous un "
            "dossier systeme connu (/system, /vendor, /data, /proc, "
            "/sys, /dev, /apex, /sbin, /cache, /product, /odm, /oem)."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    resultat = executer_root(f"ls -la {citer_chemin(dossier)}", appareil_id)
    if not resultat["ok"]:
        return marquer_non_teste(f"Dossier illisible : {resultat['erreur']}")
    return marquer_non_teste(
        formater_liste_fichiers(
            dossier.strip(), parse_ls_la(resultat["sortie"])
        )
    )


@mcp_diagnostic.tool()
def root_lire_fichier_systeme(chemin: str, limite_lignes: int = 50) -> str:
    """Lit le debut texte d'un fichier systeme protege.

    chemin : fichier absolu sous un dossier systeme connu (voir
    root_lister_fichiers_systeme). limite_lignes : 1 a 200, 50 par
    defaut. Fichiers binaires refuses. Lecture seule.
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
    if not chemin_lecture_valide(chemin or ""):
        return marquer_non_teste(
            "Erreur : chemin refuse. Donne un fichier absolu sous un "
            "dossier systeme connu (/system, /vendor, /data, /proc, "
            "/sys, /dev, /apex, /sbin, /cache, /product, /odm, /oem)."
        )
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    taille = executer_root(
        f"wc -c < {citer_chemin(chemin)}", appareil_id
    )
    total = 0
    if taille["ok"]:
        try:
            total = int(taille["sortie"].strip().split()[0])
        except (ValueError, IndexError):
            total = 0
    resultat = executer_root(
        f"head -c {TAILLE_MAXI_FICHIER} {citer_chemin(chemin)}",
        appareil_id,
    )
    if not resultat["ok"]:
        return marquer_non_teste(f"Fichier illisible : {resultat['erreur']}")
    contenu = resultat["sortie"]
    lignes = contenu.splitlines()[:limite_lignes]
    return marquer_non_teste(
        formater_fichier_systeme(
            chemin.strip(), "\n".join(lignes), total > TAILLE_MAXI_FICHIER
        )
    )


@mcp_diagnostic.tool()
def root_lire_erreurs_noyau(limite: int = 100) -> str:
    """Lit les erreurs recentes du noyau (dmesg).

    limite : lignes affichees (10 a 500, 100 par defaut). Lecture
    seule, ne modifie rien. Non teste sur appareil roote.
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
    resultat = executer_root(
        f"dmesg -T -l err,crit,alert,emerg 2>/dev/null | tail -n {limite}",
        appareil_id,
    )
    if not resultat["ok"]:
        return marquer_non_teste(f"Noyau illisible : {resultat['erreur']}")
    lignes = parse_dmesg_erreurs(resultat["sortie"])
    return marquer_non_teste(formater_erreurs_noyau(lignes, limite))


@mcp_diagnostic.tool()
def root_lire_paniques_passees() -> str:
    """Lit les traces de plantages noyau precedents (pstore, last_kmsg).

    Lecture seule, ne modifie rien. Non teste sur appareil roote.
    """
    appareil_id, erreur = preparer_root()
    if erreur:
        return marquer_non_teste(erreur)
    sorties = []
    for chemin in FICHIERS_PANIQUE:
        resultat = executer_root(
            f"head -c 4000 {chemin} 2>/dev/null", appareil_id
        )
        sorties.append(
            (chemin, resultat["sortie"] if resultat["ok"] else "")
        )
    return marquer_non_teste(formater_paniques(parse_paniques(sorties)))
