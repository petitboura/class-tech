"""Outils stockage du telephone : espace, gros fichiers, vide des caches.

- lire_stockage et lister_gros_fichiers : lectures seules, sans danger.
- vider_cache_applis : efface les caches (action reelle, outil sensible,
  confirmation demandee par Classinus avant execution).
"""

import re

from core.outils_diagnostic_commun import mcp_diagnostic
from core.pont_adb import (
    DELAI_ADB_LENT_SECONDES,
    erreur_courte,
    executer_shell,
    parametre_shell_valide,
    preparer_appel,
)

# Dossiers autorises pour la recherche de gros fichiers. Jamais de
# racine systeme : on reste dans le stockage accessible sans root.
DOSSIERS_RECHERCHE_AUTORISES = ("/sdcard", "/storage", "/data/local/tmp")

MOTIF_LIGNE_DF = re.compile(
    r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)%\s+(\S+)\s*$"
)
MOTIF_LS_TAILLE = re.compile(
    r"^[-dlpscbD][rwxst-]{9}\s+\S+\s+\S+\s+\S+\s+(\S+)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+)$"
)
MOTIF_TAILLE_HUMAINE = re.compile(r"^([\d.]+)\s*([KMGT])?$", re.IGNORECASE)
MULTIPLICATEURS_TAILLE = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}


def taille_en_octets(texte):
    """Convertit 123M, 1.2G... en octets. Fonction pure, -1 si illisible."""
    if not texte:
        return -1
    trouve = MOTIF_TAILLE_HUMAINE.match(texte.strip())
    if not trouve:
        return -1
    try:
        nombre = float(trouve.group(1))
    except ValueError:
        return -1
    unite = (trouve.group(2) or "").upper()
    return int(nombre * MULTIPLICATEURS_TAILLE.get(unite, 1))


def parse_df(texte):
    """Parse `df -h` en liste de disques. Fonction pure.

    Gere les lignes coupees en deux (systeme de fichiers seul sur sa
    ligne, chiffres sur la suivante). Chaque disque donne {"point",
    "total", "utilise", "dispo", "pct"}.
    """
    disques = []
    if not texte:
        return disques
    lignes = [l for l in (l.strip() for l in texte.splitlines()) if l]
    assemblees = []
    tampon = ""
    for ligne in lignes[1:]:
        if len(ligne.split()) == 1:
            tampon = ligne
            continue
        if tampon:
            ligne = tampon + " " + ligne
            tampon = ""
        assemblees.append(ligne)
    for ligne in assemblees:
        trouve = MOTIF_LIGNE_DF.match(ligne)
        if trouve:
            _sys, total, utilise, dispo, pct, point = trouve.groups()
            disques.append({
                "point": point, "total": total, "utilise": utilise,
                "dispo": dispo, "pct": int(pct),
            })
    return disques


def formater_stockage(disques):
    """Texte de reponse pour l'espace disque. Fonction pure."""
    if not disques:
        return "Espace disque illisible pour le moment."
    morceaux = []
    for disque in disques:
        morceaux.append(
            f"{disque['point']} : {disque['dispo']} libres sur {disque['total']} "
            f"({disque['pct']} % utilises)"
        )
    texte = "Stockage : " + ", ".join(morceaux) + "."
    pleins = [d["point"] for d in disques if d["pct"] >= 90]
    if pleins:
        texte += " Stockage presque plein sur " + ", ".join(pleins) + "."
    return texte


def parse_gros_fichiers(texte, taille_min_octets=0):
    """Parse des lignes `ls -lh` en [(chemin, taille_texte, octets)].

    Fonction pure, triee du plus gros au plus petit.
    """
    trouves = []
    if not texte:
        return trouves
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        trouve = MOTIF_LS_TAILLE.match(ligne)
        if not trouve:
            continue
        taille_texte, chemin = trouve.groups()
        octets = taille_en_octets(taille_texte)
        if octets >= taille_min_octets:
            trouves.append((chemin, taille_texte, octets))
    trouves.sort(key=lambda item: item[2], reverse=True)
    return trouves


def formater_gros_fichiers(trouves, taille_min_mo, dossier, limite=20):
    """Texte de reponse pour les gros fichiers. Fonction pure."""
    if not trouves:
        return f"Aucun fichier de plus de {taille_min_mo} Mo dans {dossier}."
    lignes = [f"{chemin} ({taille})" for chemin, taille, _octets in trouves[:limite]]
    texte = f"Gros fichiers dans {dossier} : " + ", ".join(lignes) + "."
    if len(trouves) > limite:
        texte += f" Et {len(trouves) - limite} autres."
    return texte


@mcp_diagnostic.tool()
def lire_stockage() -> str:
    """Lit l'espace disque reel : total, utilise, libre sur data et sdcard.

    Lecture seule via ADB, ne modifie rien sur le telephone.
    """
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    resultat = executer_shell("df -h /data /sdcard", appareil_id)
    if not resultat["ok"]:
        return f"Stockage illisible : {resultat['erreur']}"
    return formater_stockage(parse_df(resultat["sortie"]))


@mcp_diagnostic.tool()
def lister_gros_fichiers(taille_min_mo: int = 100, dossier: str = "/sdcard") -> str:
    """Liste les fichiers les plus gros du stockage, du plus gros au plus petit.

    taille_min_mo : taille minimum en Mo (1 a 10000, 100 par defaut).
    dossier : ou chercher (/sdcard par defaut). Lecture seule.
    """
    try:
        taille_min_mo = int(taille_min_mo)
    except (TypeError, ValueError):
        return "Erreur : taille invalide, donne un nombre entre 1 et 10000."
    if not 1 <= taille_min_mo <= 10000:
        return "Erreur : taille invalide, donne un nombre entre 1 et 10000."
    dossier = (dossier or "").strip() or "/sdcard"
    if not dossier.startswith(DOSSIERS_RECHERCHE_AUTORISES):
        return "Erreur : dossier refuse, reste dans /sdcard ou /storage."
    if not parametre_shell_valide(dossier):
        return "Erreur : nom de dossier invalide."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    commande = (
        f"find {dossier} -type f -size +{taille_min_mo}M "
        "-exec ls -lh {} + 2>/dev/null | head -n 60"
    )
    resultat = executer_shell(commande, appareil_id, delai=DELAI_ADB_LENT_SECONDES)
    if not resultat["ok"]:
        return f"Recherche impossible : {resultat['erreur']}"
    trouves = parse_gros_fichiers(resultat["sortie"], taille_min_mo * 1024 * 1024)
    return formater_gros_fichiers(trouves, taille_min_mo, dossier)


@mcp_diagnostic.tool()
def vider_cache_applis(espace_voulu_mo: int = 500) -> str:
    """Vide les caches des applis pour liberer de l'espace disque.

    Action reelle (les caches se reconstruisent seuls ensuite), jamais
    les donnees des applis. Classinus demande confirmation avant.
    """
    try:
        espace_voulu_mo = int(espace_voulu_mo)
    except (TypeError, ValueError):
        return "Erreur : taille invalide, donne un nombre entre 100 et 8192."
    if not 100 <= espace_voulu_mo <= 8192:
        return "Erreur : taille invalide, donne un nombre entre 100 et 8192."
    appareil_id, erreur = preparer_appel()
    if erreur:
        return erreur
    avant = executer_shell("df /data", appareil_id)
    octets = espace_voulu_mo * 1024 * 1024
    nettoye = executer_shell(f"pm trim-caches {octets}", appareil_id, delai=DELAI_ADB_LENT_SECONDES)
    if not nettoye["ok"]:
        return f"Nettoyage refuse : {erreur_courte(nettoye['erreur'])}"
    apres = executer_shell("df /data", appareil_id)
    liberes = _octets_liberes(parse_df(avant["sortie"] if avant["ok"] else ""),
                              parse_df(apres["sortie"] if apres["ok"] else ""))
    if liberes is None:
        return "Caches vides. Espace libere non mesurable pour le moment."
    if liberes <= 0:
        return "Caches vides, mais presque rien a liberer (caches deja petits)."
    return f"Caches vides, environ {liberes} Mo liberes."


def _octets_liberes(avant, apres):
    """Mo liberes entre deux lectures df, ou None. Fonction pure."""
    def dispo(disques):
        for disque in disques:
            if disque["point"] == "/data":
                return taille_en_octets(disque["dispo"] + "K") if disque["dispo"].isdigit() else taille_en_octets(disque["dispo"])
        return -1
    a, b = dispo(avant), dispo(apres)
    if a < 0 or b < 0:
        return None
    return max(0, round((b - a) / (1024 * 1024)))
