"""Lecture des réponses système du téléphone (palier 100 %).

Même contrat que analyse_materiel : fonctions pures recevant les
sorties adb brutes et renvoyant faits + résumé français. Testées sans
téléphone (voir tests/test_diagnostic_100).

Sans dépendance externe (stdlib uniquement).
"""

from __future__ import annotations

import re
from datetime import date

# Seuils des verdicts, source unique (jamais recopiés ailleurs).
SEUIL_MEMOIRE_JUSTE_PCT = 20
SEUIL_MEMOIRE_CRITIQUE_PCT = 10
SEUIL_PATCH_RETARE_JOURS = 90
SEUIL_PATCH_TRES_RETARE_JOURS = 180
SEUIL_PERMISSIONS_INQUIETANT = 2

MOIS_FR = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)

# Permissions Android jugées sensibles pour le grand public. Source
# unique, lue par l'inventaire et par l'outil de retrait.
PERMISSIONS_RISQUEES = frozenset({
    "android.permission.READ_CALENDAR",
    "android.permission.WRITE_CALENDAR",
    "android.permission.CAMERA",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.GET_ACCOUNTS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_PHONE_STATE",
    "android.permission.READ_PHONE_NUMBERS",
    "android.permission.CALL_PHONE",
    "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG",
    "android.permission.ANSWER_PHONE_CALLS",
    "android.permission.BODY_SENSORS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_MMS",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_MEDIA_IMAGES",
    "android.permission.READ_MEDIA_VIDEO",
    "android.permission.READ_MEDIA_AUDIO",
})

# Noms courts acceptés par l'outil de retrait, vers les vraies permissions.
RACCOURCIS_PERMISSIONS = {
    "calendrier": ["android.permission.READ_CALENDAR", "android.permission.WRITE_CALENDAR"],
    "camera": ["android.permission.CAMERA"],
    "contacts": ["android.permission.READ_CONTACTS", "android.permission.WRITE_CONTACTS"],
    "localisation": [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
    ],
    "micro": ["android.permission.RECORD_AUDIO"],
    "telephone": ["android.permission.READ_PHONE_STATE", "android.permission.CALL_PHONE"],
    "sms": ["android.permission.SEND_SMS", "android.permission.RECEIVE_SMS", "android.permission.READ_SMS"],
    "fichiers": [
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.READ_MEDIA_VIDEO",
        "android.permission.READ_MEDIA_AUDIO",
    ],
}


def formater_mo(valeur_mo: float) -> str:
    """12 ou 1536 Mo en texte français (Mo, ou Go avec virgule)."""
    if valeur_mo >= 1024:
        return f"{valeur_mo / 1024:.1f}".replace(".", ",") + " Go"
    return f"{valeur_mo:.0f} Mo"


def formater_date_patch(texte: str) -> str | None:
    """'2026-09-05' en '5 septembre 2026', None si illisible."""
    trouve = re.match(r"(\d{4})-(\d{2})-(\d{2})", texte.strip())
    if not trouve:
        return None
    annee, mois, jour = (int(g) for g in trouve.groups())
    if not 1 <= mois <= 12:
        return None
    return f"{jour} {MOIS_FR[mois - 1]} {annee}"


def analyser_memoire(sortie_meminfo: str) -> dict:
    """Mémoire vive d'après /proc/meminfo (valeurs en ko)."""
    valeurs = {}
    for cle in ("MemTotal", "MemAvailable", "MemFree", "Cached", "SwapTotal", "SwapFree"):
        trouve = re.search(rf"^{cle}:\s+(\d+)", sortie_meminfo, re.MULTILINE)
        valeurs[cle] = int(trouve.group(1)) / 1024 if trouve else None
    total = valeurs["MemTotal"]
    disponible = valeurs["MemAvailable"]
    if disponible is None and valeurs["MemFree"] is not None:
        disponible = valeurs["MemFree"] + (valeurs["Cached"] or 0)
    if total in (None, 0) or disponible is None:
        return {
            "total_mo": total, "disponible_mo": disponible,
            "pct_disponible": None,
            "resume": "Mémoire vive illisible sur ce téléphone.",
        }
    pct = round(disponible / total * 100)
    resume = (
        f"Mémoire vive : {formater_mo(total)} au total, "
        f"{formater_mo(disponible)} libres ({pct} %). "
    )
    if pct < SEUIL_MEMOIRE_CRITIQUE_PCT:
        resume += "Très peu de mémoire libre : fermez les applis ouvertes."
    elif pct < SEUIL_MEMOIRE_JUSTE_PCT:
        resume += "Mémoire un peu juste : fermez les applis inutilisées."
    else:
        resume += "Niveau correct."
    return {
        "total_mo": round(total), "disponible_mo": round(disponible),
        "pct_disponible": pct, "resume": resume,
    }


def analyser_cpu(sortie_cpuinfo: str, sortie_loadavg: str) -> dict:
    """Processeur d'après /proc/cpuinfo et /proc/loadavg."""
    coeurs = len(re.findall(r"^processor\s*:", sortie_cpuinfo, re.MULTILINE))
    modele = re.search(r"^(?:Hardware|model name)\s*:\s*(.+)$", sortie_cpuinfo, re.MULTILINE)
    charge = re.search(r"^([\d.]+)", sortie_loadavg.strip())
    charge_1 = float(charge.group(1)) if charge else None
    resume = ""
    if coeurs:
        resume += f"Processeur : {coeurs} cœurs"
        if modele:
            resume += f" ({modele.group(1).strip()})"
        resume += ". "
    else:
        resume += "Processeur : nombre de cœurs illisible. "
    if charge_1 is not None and coeurs:
        resume += f"Charge actuelle : {str(charge_1).replace('.', ',')} pour {coeurs} cœurs. "
        if charge_1 > coeurs:
            resume += "Le téléphone est très sollicité en ce moment."
        elif charge_1 > coeurs / 2:
            resume += "Activité moyenne."
        else:
            resume += "Activité calme."
    elif charge_1 is not None:
        resume += f"Charge actuelle : {str(charge_1).replace('.', ',')}."
    else:
        resume += "Charge illisible."
    return {
        "coeurs": coeurs or None,
        "modele": modele.group(1).strip() if modele else None,
        "charge_1min": charge_1,
        "resume": resume,
    }


def analyser_top(sortie_top: str, sortie_meminfo_dump: str) -> dict:
    """Applis les plus gourmandes (top pour le CPU, meminfo pour la RAM)."""
    processus = []
    for ligne in sortie_top.splitlines():
        morceaux = ligne.split()
        # Ligne type : PID ... %CPU ... COMMANDE (colonnes variables).
        if len(morceaux) < 6 or not morceaux[0].isdigit():
            continue
        nom = morceaux[-1]
        if "/" in nom:
            nom = nom.rsplit("/", 1)[-1]
        pcts = re.findall(r"(\d+(?:[.,]\d+)?)%", ligne)
        cpu = None
        if pcts:
            cpu = float(pcts[0].replace(",", "."))
        processus.append({"nom": nom, "cpu_pct": cpu})
    processus.sort(key=lambda p: (p["cpu_pct"] is None, -(p["cpu_pct"] or 0)))
    gourmands_cpu = [p for p in processus if p["cpu_pct"]] [:5]
    memoire = []
    for ligne in sortie_meminfo_dump.splitlines():
        trouve = re.match(r"\s*([\d,]+)K:\s*(\S+)\s+\(pid", ligne)
        if trouve:
            ko = int(trouve.group(1).replace(",", ""))
            memoire.append({"paquet": trouve.group(2), "mo": round(ko / 1024)})
    memoire.sort(key=lambda a: -a["mo"])
    gourmands_ram = memoire[:8]
    morceaux = []
    if gourmands_cpu:
        details = ", ".join(
            f"{p['nom']} ({str(p['cpu_pct']).replace('.', ',')} %)" for p in gourmands_cpu
        )
        morceaux.append(f"CPU en ce moment : {details}")
    if gourmands_ram:
        details = ", ".join(f"{a['paquet']} ({formater_mo(a['mo'])})" for a in gourmands_ram[:5])
        morceaux.append(f"RAM : {details}")
    if morceaux:
        resume = "Plus gros consommateurs : " + ". ".join(morceaux) + "."
    else:
        resume = "Consommation par appli illisible sur ce téléphone."
    return {"top_cpu": gourmands_cpu, "top_ram": gourmands_ram, "resume": resume}


def analyser_permissions(sortie_package: str, perimetre: str = "tierces") -> dict:
    """Applis détenant des permissions risquées (dumpsys package)."""
    paquet = None
    code_path = ""
    dans_permissions = False
    detenues: dict[str, dict] = {}
    for ligne in sortie_package.splitlines():
        nouveau = re.match(r"Package \[([^\]]+)\]", ligne)
        if nouveau:
            paquet = nouveau.group(1)
            code_path = ""
            dans_permissions = False
            continue
        if paquet is None:
            continue
        chemin = re.match(r"\s*codePath=(.+)$", ligne)
        if chemin:
            code_path = chemin.group(1).strip()
            continue
        if re.match(r"\s*runtime permissions:", ligne):
            dans_permissions = True
            continue
        if dans_permissions:
            if re.match(r"\s{0,3}\S", ligne):
                dans_permissions = False
            else:
                perm = re.match(r"\s+(android\.permission\.\w+):\s*granted=(\w+)", ligne)
                if perm and perm.group(2) == "true" and perm.group(1) in PERMISSIONS_RISQUEES:
                    entree = detenues.setdefault(
                        paquet, {"paquet": paquet, "systeme": None, "permissions": []}
                    )
                    entree["permissions"].append(perm.group(1))
        if paquet in detenues and code_path:
            detenues[paquet]["systeme"] = not code_path.startswith("/data/app/")
    applications = sorted(detenues.values(), key=lambda a: -len(a["permissions"]))
    if perimetre == "tierces":
        applications = [a for a in applications if not a["systeme"]]
    elif perimetre == "systeme":
        applications = [a for a in applications if a["systeme"]]
    inquiete = [a for a in applications if len(a["permissions"]) >= SEUIL_PERMISSIONS_INQUIETANT]
    resume = ""
    if not applications:
        resume = "Aucune appli ne détient de permission à risque dans ce périmètre."
    else:
        resume = f"{len(applications)} applis détiennent des permissions à risque"
        if inquiete:
            resume += f", dont {len(inquiete)} avec {SEUIL_PERMISSIONS_INQUIETANT} ou plus"
        resume += ". "
        for appli in inquiete[:8]:
            noms = ", ".join(p.rsplit(".", 1)[-1] for p in appli["permissions"][:4])
            resume += f"{appli['paquet']} ({noms}). "
        resume = resume.strip()
    return {"applications": applications[:15], "total": len(applications), "resume": resume}


def normaliser_permission(demande: str) -> list[str]:
    """Traduit une demande ('localisation', 'android.permission.CAMERA'...)
    en liste de vraies permissions. Liste vide si inconnue."""
    texte = demande.strip().lower()
    if texte in RACCOURCIS_PERMISSIONS:
        return list(RACCOURCIS_PERMISSIONS[texte])
    brut = demande.strip()
    if re.fullmatch(r"android\.permission\.[A-Z_]+", brut):
        return [brut]
    return []


def analyser_securite(donnees: dict[str, str | None], aujourd_hui: date | None = None) -> dict:
    """Bilan sécurité de base à partir des valeurs lues sur le téléphone.

    donnees contient tout ou partie de : patch, bootloader, crypto,
    sources_inconnues, adb_active, options_dev. aujourd_hui est
    injectable pour les tests.
    """
    points = []
    patch = (donnees.get("patch") or "").strip()
    jour = aujourd_hui or date.today()
    date_patch = formater_date_patch(patch)
    age = None
    if re.match(r"\d{4}-\d{2}-\d{2}", patch):
        try:
            annee, mois, num = (int(v) for v in patch[:10].split("-"))
            age = (jour - date(annee, mois, num)).days
        except ValueError:
            age = None
    if date_patch and age is not None and age >= 0:
        if age > SEUIL_PATCH_TRES_RETARE_JOURS:
            points.append(("Correctif de sécurité", "attention",
                           f"daté du {date_patch}, très en retard"))
        elif age > SEUIL_PATCH_RETARE_JOURS:
            points.append(("Correctif de sécurité", "attention",
                           f"daté du {date_patch}, à mettre à jour"))
        else:
            points.append(("Correctif de sécurité", "ok", f"daté du {date_patch}"))
    else:
        points.append(("Correctif de sécurité", "a_verifier", "date illisible"))
    bootloader = (donnees.get("bootloader") or "").strip().lower()
    if bootloader in ("locked", "yes", "1"):
        points.append(("Démarrage vérifié", "ok", "verrouillé"))
    elif bootloader in ("unlocked", "no", "0", "orange"):
        points.append(("Démarrage vérifié", "attention", "déverrouillé, téléphone plus exposé"))
    else:
        points.append(("Démarrage vérifié", "a_verifier", "état illisible"))
    crypto = (donnees.get("crypto") or "").strip().lower()
    if crypto == "encrypted":
        points.append(("Chiffrement", "ok", "données chiffrées"))
    elif crypto:
        points.append(("Chiffrement", "attention", f"état : {crypto}"))
    else:
        points.append(("Chiffrement", "a_verifier", "état illisible"))
    sources = (donnees.get("sources_inconnues") or "").strip()
    if sources == "1":
        points.append(("Sources inconnues", "attention", "autorisées, à couper si inutile"))
    elif sources == "0":
        points.append(("Sources inconnues", "ok", "bloquées"))
    else:
        points.append(("Sources inconnues", "a_verifier", "réglage illisible"))
    if (donnees.get("adb_active") or "").strip() == "1":
        points.append(("Débogage USB", "attention", "encore actif, à couper après le diagnostic"))
    phrases = []
    for sujet, statut, detail in points:
        marque = {"ok": "bon", "attention": "à revoir", "a_verifier": "non vérifié"}[statut]
        phrases.append(f"{sujet} : {detail} ({marque})")
    return {"points": points, "resume": "Bilan sécurité. " + ". ".join(phrases) + "."}


def analyser_mises_a_jour(
    version_android: str, patch: str, aujourd_hui: date | None = None
) -> dict:
    """État des mises à jour (version Android + âge du correctif)."""
    version = version_android.strip() or None
    date_patch = formater_date_patch(patch)
    jour = aujourd_hui or date.today()
    age = None
    if re.match(r"\d{4}-\d{2}-\d{2}", patch.strip()):
        try:
            annee, mois, num = (int(v) for v in patch.strip()[:10].split("-"))
            age = (jour - date(annee, mois, num)).days
        except ValueError:
            age = None
    morceaux = []
    if version:
        morceaux.append(f"Android {version}")
    if date_patch and age is not None and age >= 0:
        morceaux.append(f"correctif du {date_patch}")
        if age > SEUIL_PATCH_TRES_RETARE_JOURS:
            morceaux.append("très en retard, mettez à jour dès que possible")
        elif age > SEUIL_PATCH_RETARE_JOURS:
            morceaux.append("en retard, une mise à jour est conseillée")
        else:
            morceaux.append("à jour")
    elif date_patch:
        morceaux.append(f"correctif du {date_patch}")
    else:
        morceaux.append("date du correctif illisible")
    resume = "Mises à jour : " + ", ".join(morceaux) + "."
    resume += " Pour vérifier : Paramètres, Système, Mise à jour logicielle."
    return {"version": version, "patch": date_patch, "age_jours": age, "resume": resume}
