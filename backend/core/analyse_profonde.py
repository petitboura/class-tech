"""Lecture des diagnostics profonds du téléphone (palier 100 %, sans root).

Même contrat que analyse_systeme : fonctions pures recevant les
sorties adb brutes et renvoyant faits + résumé français. Testées sans
téléphone (voir tests/test_diagnostic_profond).

Lecture seule : ces analyses ne changent rien, elles décrivent ce que
le téléphone accepte de montrer sans root. Ce qui est illisible sur un
modèle est dit tel quel, jamais inventé. Le journal du noyau (dmesg)
reste fermé sans root et n'est promis nulle part.

Sans dépendance externe (stdlib + analyse_systeme pour les formats).
"""

from __future__ import annotations

import re

from core.analyse_systeme import formater_date_patch, formater_mo

# Seuils des verdicts, source unique (jamais recopiés ailleurs).
SEUIL_TEMP_TIEDE_C = 40.0
SEUIL_TEMP_CHAUD_C = 45.0
SEUIL_SACCADES_ATTENTION_PCT = 10.0
SEUIL_SACCADES_CRITIQUE_PCT = 30.0
SEUIL_PSI_ATTENTION_PCT = 10.0
SEUIL_PSI_CRITIQUE_PCT = 30.0
SEUIL_VERROUS_NOMBREUX = 5
SEUIL_CRASHS_ATTENTION = 3
SEUIL_GROSSE_MEMOIRE_MO = 500
# Valeur brute au dessus de laquelle une température est lue en
# dixièmes de degré (certains modèles donnent 320 pour 32 degrés).
SEUIL_TEMP_DIXIEMES = 150.0

# Nombres d'éléments cités dans les résumés, source unique.
NOMBRE_TOP_CONSO = 5
NOMBRE_TOP_TRAFIC = 5
NOMBRE_TOP_SACCADES = 5
NOMBRE_TOP_REVEILS = 5
NOMBRE_TOP_CRASHS = 5
NOMBRE_TOP_ERREURS = 3
NOMBRE_TOP_MEMOIRE = 5
NOMBRE_TOP_VERROUS = 8

# UID Android en dessous desquels vit le système (applis à partir de
# 10000). Convention Android stable, jamais recopiée ailleurs.
SEUIL_UID_APPLI = 10000


def formater_octets(octets: float) -> str:
    """12345678 octets en texte français (o, Ko, Mo ou Go)."""
    if octets >= 1024 ** 3:
        return f"{octets / 1024 ** 3:.1f}".replace(".", ",") + " Go"
    if octets >= 1024 ** 2:
        return f"{octets / 1024 ** 2:.1f}".replace(".", ",") + " Mo"
    if octets >= 1024:
        return f"{octets / 1024:.0f} Ko"
    return f"{octets:.0f} o"


def formater_temperature(celsius: float) -> str:
    """32.9 en '32,9 degrés', sans symbole spécial."""
    return f"{celsius:.1f}".replace(".", ",") + " degrés"


def analyser_temperatures(sortie_thermal: str) -> dict:
    """Températures internes d'après dumpsys thermalservice.

    Chaque sonde donne son nom et sa valeur. Les modèles qui ne
    partagent pas leurs sondes donnent un verdict honnête.
    """
    sondes = []
    for trouve in re.finditer(
        r"mValue=([\d.]+).*?mName=([^,}]+)", sortie_thermal
    ):
        try:
            valeur = float(trouve.group(1))
        except ValueError:
            continue
        if valeur > SEUIL_TEMP_DIXIEMES:
            valeur = valeur / 10
        sondes.append({"nom": trouve.group(2).strip(), "celsius": valeur})
    if not sondes:
        return {
            "sondes": [],
            "resume": (
                "Températures internes illisibles sur ce téléphone, "
                "le modèle ne partage pas ses sondes."
            ),
        }
    sondes.sort(key=lambda s: -s["celsius"])
    details = ", ".join(
        f"{s['nom']} ({formater_temperature(s['celsius'])})" for s in sondes
    )
    plus_chaude = sondes[0]
    resume = f"Températures internes : {details}. "
    if plus_chaude["celsius"] >= SEUIL_TEMP_CHAUD_C:
        resume += (
            f"Le point le plus chaud ({plus_chaude['nom']}) dépasse "
            f"{formater_temperature(SEUIL_TEMP_CHAUD_C)}, laissez "
            "reposer le téléphone à l'ombre."
        )
    elif plus_chaude["celsius"] >= SEUIL_TEMP_TIEDE_C:
        resume += "Températures élevées mais acceptables."
    else:
        resume += "Températures normales."
    return {"sondes": sondes, "resume": resume}


def analyser_historique_batterie(sortie_batterystats: str) -> dict:
    """Historique batterie d'après dumpsys batterystats.

    Autonomie depuis la dernière charge, conso estimée, plus gros
    consommateurs et nombre de réveils (prises de verrou et alarmes).
    """
    temps = re.search(r"Time on battery:\s*(.+)", sortie_batterystats)
    temps_batterie = temps.group(1).strip() if temps else None
    drain = re.search(
        r"Computed drain:\s*([\d.]+),\s*actual drain:\s*([\d.\-]+)", sortie_batterystats
    )
    conso_estimee = float(drain.group(1)) if drain else None
    conso_reelle = drain.group(2) if drain else None
    debut = sortie_batterystats.find("Estimated power use")
    zone = sortie_batterystats[debut:] if debut >= 0 else ""
    consommateurs = []
    for trouve in re.finditer(
        r"^\s*Uid\s+(\S+?)(?:\s*\(([^)]+)\))?\s*:\s*([\d.]+)",
        zone, re.MULTILINE,
    ):
        try:
            consommateurs.append({
                "uid": trouve.group(1),
                "paquet": trouve.group(2) or "",
                "mah": float(trouve.group(3)),
            })
        except ValueError:
            continue
    consommateurs.sort(key=lambda c: -c["mah"])
    reveils_verrous = len(re.findall(r"\+wake_lock\b", sortie_batterystats))
    reveils_alarmes = len(re.findall(r"\*alarm\*", sortie_batterystats))
    if temps_batterie is None and not consommateurs and not drain:
        return {
            "temps_batterie": None, "consommateurs": [],
            "reveils_verrous": 0, "reveils_alarmes": 0,
            "resume": "Historique batterie illisible sur ce téléphone.",
        }
    morceaux = []
    if temps_batterie:
        morceaux.append(f"sur batterie depuis {temps_batterie}")
    if conso_estimee is not None:
        texte_conso = (
            f"conso estimée {str(conso_estimee).replace('.', ',')} mAh"
        )
        if conso_reelle:
            texte_conso += f" (mesurée {conso_reelle} mAh)"
        morceaux.append(texte_conso)
    if consommateurs:
        details = ", ".join(
            f"{c['paquet'] or c['uid']} "
            f"({str(round(c['mah'], 1)).replace('.', ',')} mAh)"
            for c in consommateurs[:NOMBRE_TOP_CONSO]
        )
        morceaux.append(f"plus gros consommateurs : {details}")
    total_reveils = reveils_verrous + reveils_alarmes
    if total_reveils:
        morceaux.append(
            f"{total_reveils} réveils enregistrés "
            f"({reveils_verrous} prises de verrou, {reveils_alarmes} alarmes)"
        )
    else:
        morceaux.append("aucun réveil enregistré dans l'historique")
    resume = "Historique batterie : " + ". ".join(morceaux) + "."
    return {
        "temps_batterie": temps_batterie,
        "conso_estimee_mah": conso_estimee,
        "consommateurs": consommateurs[:NOMBRE_TOP_CONSO],
        "reveils_verrous": reveils_verrous,
        "reveils_alarmes": reveils_alarmes,
        "resume": resume,
    }


def associer_uid_paquets(sortie_pm: str) -> dict[str, list[str]]:
    """Table {uid: [paquets]} d'après pm list packages -U."""
    table: dict[str, list[str]] = {}
    for trouve in re.finditer(r"^package:(\S+)\s+uid:(\d+)", sortie_pm, re.MULTILINE):
        table.setdefault(trouve.group(2), []).append(trouve.group(1))
    return table


def analyser_trafic_applis(sortie_netstats: str, table_uid: dict | None = None) -> dict:
    """Trafic internet par appli d'après dumpsys netstats.

    Octets reçus et envoyés par UID, traduits en noms d'applis quand
    la table pm est fournie. Le système (petits UID) est nommé tel quel.
    """
    table_uid = table_uid or {}
    trafics: dict[str, dict] = {}
    uid_courant = None
    for ligne in sortie_netstats.splitlines():
        trouve_uid = re.search(r"\buid=(-?\d+)", ligne)
        if trouve_uid:
            uid_courant = trouve_uid.group(1)
        trouve_octets = re.search(r"rxBytes=(\d+).*?txBytes=(\d+)", ligne)
        if trouve_octets and uid_courant is not None:
            entree = trafics.setdefault(
                uid_courant, {"uid": uid_courant, "recus": 0, "envoyes": 0}
            )
            entree["recus"] += int(trouve_octets.group(1))
            entree["envoyes"] += int(trouve_octets.group(2))
    utilises = [t for t in trafics.values() if t["recus"] or t["envoyes"]]
    if not utilises:
        return {
            "trafics": [],
            "resume": "Trafic internet par appli illisible sur ce téléphone.",
        }
    for trafic in utilises:
        uid = trafic["uid"]
        try:
            numero = int(uid)
        except ValueError:
            numero = SEUIL_UID_APPLI
        if uid in table_uid:
            trafic["nom"] = table_uid[uid][0]
        elif numero < SEUIL_UID_APPLI:
            trafic["nom"] = "système Android"
        else:
            trafic["nom"] = f"appli inconnue (uid {uid})"
        trafic["total"] = trafic["recus"] + trafic["envoyes"]
    utilises.sort(key=lambda t: -t["total"])
    total = sum(t["total"] for t in utilises)
    details = ", ".join(
        f"{t['nom']} ({formater_octets(t['total'])}, "
        f"dont {formater_octets(t['envoyes'])} envoyés)"
        for t in utilises[:NOMBRE_TOP_TRAFIC]
    )
    resume = (
        f"Trafic internet total : {formater_octets(total)}. "
        f"Plus gros consommateurs : {details}."
    )
    return {
        "trafics": utilises[:NOMBRE_TOP_TRAFIC],
        "total_octets": total,
        "resume": resume,
    }


def analyser_fluidite(sortie_gfxinfo: str) -> dict:
    """Saccades d'affichage d'après dumpsys gfxinfo.

    Images saccadées par appli, avec verdict simple sur la fluidité.
    """
    applis = []
    section = None
    for ligne in sortie_gfxinfo.splitlines():
        processus = re.search(
            r"Graphics info for pid \d+ \[([^\]]+)\]", ligne
        )
        if processus:
            section = {"paquet": processus.group(1)}
            applis.append(section)
            continue
        if section is None:
            continue
        saccadees = re.search(r"Janky frames:\s*(\d+)\s*\(([\d.]+)%\)", ligne)
        if saccadees:
            section["saccadees"] = int(saccadees.group(1))
            section["saccadees_pct"] = float(saccadees.group(2))
        rendues = re.search(r"Total frames rendered:\s*(\d+)", ligne)
        if rendues:
            section["rendues"] = int(rendues.group(1))
    mesurees = [a for a in applis if "saccadees_pct" in a]
    if not mesurees:
        return {
            "applis": [],
            "resume": (
                "Fluidité de l'écran illisible sur ce téléphone "
                "(ouvrez une appli puis réessayez)."
            ),
        }
    mesurees.sort(key=lambda a: -a["saccadees_pct"])
    details = ", ".join(
        f"{a['paquet']} "
        f"({str(a['saccadees_pct']).replace('.', ',')} % saccadées)"
        for a in mesurees[:NOMBRE_TOP_SACCADES]
    )
    pire = mesurees[0]["saccadees_pct"]
    resume = f"Fluidité de l'écran : {details}. "
    if pire >= SEUIL_SACCADES_CRITIQUE_PCT:
        resume += "Affichage très saccadé, le téléphone peine."
    elif pire >= SEUIL_SACCADES_ATTENTION_PCT:
        resume += "Quelques saccades visibles par moments."
    else:
        resume += "Affichage fluide."
    return {"applis": mesurees[:NOMBRE_TOP_SACCADES], "resume": resume}


def analyser_saturation(
    sortie_psi_cpu: str, sortie_psi_mem: str, sortie_psi_io: str
) -> dict:
    """Saturation CPU, mémoire et stockage d'après /proc/pressure.

    Chaque valeur dit quel pourcentage du temps récent le téléphone a
    manqué de cette ressource (moyenne sur 10 secondes).
    """
    ressources = []
    for nom, sortie in (
        ("processeur", sortie_psi_cpu),
        ("mémoire", sortie_psi_mem),
        ("stockage", sortie_psi_io),
    ):
        trouve = re.search(r"^some\s+avg10=([\d.]+)", sortie, re.MULTILINE)
        if trouve:
            ressources.append({"nom": nom, "attente_pct": float(trouve.group(1))})
    if not ressources:
        return {
            "ressources": [],
            "resume": (
                "Saturation interne illisible sur ce téléphone "
                "(les compteurs ne sont pas partagés)."
            ),
        }
    details = ", ".join(
        f"{r['nom']} {str(r['attente_pct']).replace('.', ',')} % d'attente"
        for r in ressources
    )
    pire = max(r["attente_pct"] for r in ressources)
    resume = f"Saturation interne : {details}. "
    if pire >= SEUIL_PSI_CRITIQUE_PCT:
        resume += "Le téléphone manque nettement de souffle en ce moment."
    elif pire >= SEUIL_PSI_ATTENTION_PCT:
        resume += "Légère saturation par moments."
    else:
        resume += "Aucune saturation, le téléphone respire."
    return {"ressources": ressources, "resume": resume}


def analyser_reveils(sortie_alarm: str, sortie_jobs: str) -> dict:
    """Alarmes et tâches planifiées d'après alarm et jobscheduler.

    Compte les réveils par appli et les tâches en attente, pour trouver
    ce qui réveille le téléphone en arrière plan.
    """
    reveils: dict[str, int] = {}
    paquet_courant = None
    for ligne in sortie_alarm.splitlines():
        ligne_nette = ligne.strip()
        if ligne_nette and re.fullmatch(r"[a-z][a-z0-9_.]*", ligne_nette):
            paquet_courant = ligne_nette
            continue
        trouve = re.search(r"(\d+)\s+wakeups", ligne)
        if trouve and paquet_courant:
            reveils[paquet_courant] = reveils.get(paquet_courant, 0) + int(
                trouve.group(1)
            )
            paquet_courant = None
    taches: dict[str, int] = {}
    for trouve in re.finditer(r"JOB\s+#(\S+?)[/:]", sortie_jobs):
        taches[trouve.group(1)] = taches.get(trouve.group(1), 0) + 1
    if not reveils and not taches:
        return {
            "reveils": [], "taches": {},
            "resume": "Alarmes et tâches planifiées illisibles sur ce téléphone.",
        }
    classes = sorted(reveils.items(), key=lambda item: -item[1])
    morceaux = []
    if classes:
        total = sum(reveils.values())
        details = ", ".join(
            f"{paquet} ({nombre} réveils)"
            for paquet, nombre in classes[:NOMBRE_TOP_REVEILS]
        )
        morceaux.append(
            f"{total} réveils par alarmes, les plus actifs : {details}"
        )
    else:
        morceaux.append("aucun réveil par alarme enregistré")
    if taches:
        total_taches = sum(taches.values())
        morceaux.append(f"{total_taches} tâches planifiées par le système")
    else:
        morceaux.append("aucune tâche planifiée visible")
    resume = "Réveils et tâches cachées : " + ". ".join(morceaux) + "."
    return {
        "reveils": [
            {"paquet": p, "nombre": n} for p, n in classes[:NOMBRE_TOP_REVEILS]
        ],
        "taches": taches,
        "resume": resume,
    }


def analyser_journaux(
    sortie_logcat_crash: str, sortie_logcat_systeme: str, sortie_dropbox: str
) -> dict:
    """Plantages et erreurs système (logcat crash et system, dropbox).

    Compte les plantages par appli, les erreurs système par sujet et
    les rapports conservés par le téléphone.
    """
    plantages: dict[str, int] = {}
    for trouve in re.finditer(r"^Process:\s*(\S+)", sortie_logcat_crash, re.MULTILINE):
        plantages[trouve.group(1).rstrip(",")] = (
            plantages.get(trouve.group(1).rstrip(","), 0) + 1
        )
    erreurs: dict[str, int] = {}
    for ligne in sortie_logcat_systeme.splitlines():
        trouve = re.search(r"\bE\s+(\S+):", ligne)
        if trouve:
            erreurs[trouve.group(1)] = erreurs.get(trouve.group(1), 0) + 1
    rapports: dict[str, int] = {}
    for ligne in sortie_dropbox.splitlines():
        trouve = re.match(r"\s*([a-z_][a-z0-9_]*)\s+\(", ligne)
        if trouve:
            rapports[trouve.group(1)] = rapports.get(trouve.group(1), 0) + 1
    if not plantages and not erreurs and not rapports:
        return {
            "plantages": [], "erreurs": [], "rapports": {},
            "resume": "Journaux système illisibles sur ce téléphone.",
        }
    morceaux = []
    if plantages:
        classes = sorted(plantages.items(), key=lambda item: -item[1])
        details = ", ".join(
            f"{paquet} ({nombre})" for paquet, nombre in classes[:NOMBRE_TOP_CRASHS]
        )
        morceaux.append(f"plantages récents : {details}")
        if sum(plantages.values()) >= SEUIL_CRASHS_ATTENTION:
            morceaux.append("plusieurs plantages, une appli pose problème")
    else:
        morceaux.append("aucun plantage récent dans le journal")
    if erreurs:
        classes_erreurs = sorted(erreurs.items(), key=lambda item: -item[1])
        details = ", ".join(
            f"{sujet} ({nombre})"
            for sujet, nombre in classes_erreurs[:NOMBRE_TOP_ERREURS]
        )
        morceaux.append(f"erreurs système : {details}")
    if rapports:
        total = sum(rapports.values())
        morceaux.append(f"{total} rapports conservés par le téléphone")
    resume = "Journaux système : " + ". ".join(morceaux) + "."
    return {
        "plantages": [
            {"paquet": p, "nombre": n}
            for p, n in sorted(plantages.items(), key=lambda item: -item[1])[
                :NOMBRE_TOP_CRASHS
            ]
        ],
        "erreurs": [
            {"sujet": s, "nombre": n}
            for s, n in sorted(erreurs.items(), key=lambda item: -item[1])[
                :NOMBRE_TOP_ERREURS
            ]
        ],
        "rapports": rapports,
        "resume": resume,
    }


def analyser_carte_systeme(
    sortie_getprop: str, sortie_services: str, sortie_lshal: str
) -> dict:
    """Carte du système : version, modèle, services et composants.

    Tirée de getprop, service list et lshal, tous en lecture seule.
    """
    proprietes = dict(
        re.findall(r"\[([^\]]+)\]:\s*\[([^\]]*)\]", sortie_getprop)
    )
    version = proprietes.get("ro.build.version.release", "").strip() or None
    correctif = formater_date_patch(
        proprietes.get("ro.build.version.security_patch", "")
    )
    marque = proprietes.get("ro.product.brand", "").strip() or None
    modele = proprietes.get("ro.product.model", "").strip() or None
    sdk = proprietes.get("ro.build.version.sdk", "").strip() or None
    trouve_services = re.search(r"Found\s+(\d+)\s+services", sortie_services)
    nombre_services = int(trouve_services.group(1)) if trouve_services else None
    if nombre_services is None:
        lignes = [
            ligne for ligne in sortie_services.splitlines()
            if re.match(r"\d+\s+\S+:", ligne.strip())
        ]
        nombre_services = len(lignes) or None
    composants = [
        ligne.strip() for ligne in sortie_lshal.splitlines()
        if "::" in ligne
    ]
    if not proprietes and nombre_services is None and not composants:
        return {
            "resume": "Carte du système illisible sur ce téléphone.",
        }
    morceaux = []
    if marque or modele:
        morceaux.append(f"téléphone {' '.join(p for p in (marque, modele) if p)}")
    if version:
        texte_version = f"Android {version}"
        if sdk:
            texte_version += f" (niveau {sdk})"
        morceaux.append(texte_version)
    if correctif:
        morceaux.append(f"correctif du {correctif}")
    if nombre_services:
        morceaux.append(f"{nombre_services} services système actifs")
    if composants:
        morceaux.append(f"{len(composants)} composants matériels déclarés")
    else:
        morceaux.append("liste des composants matériels illisible")
    resume = "Carte du système : " + ". ".join(morceaux) + "."
    return {
        "version": version, "correctif": correctif,
        "marque": marque, "modele": modele,
        "nombre_services": nombre_services,
        "nombre_composants": len(composants) or None,
        "resume": resume,
    }


def analyser_memoire_temps(sortie_procstats: str) -> dict:
    """Mémoire par appli dans le temps d'après dumpsys procstats.

    Moyennes sur les dernières heures : qui garde beaucoup de mémoire
    et qui varie le plus.
    """
    applis = []
    paquet_courant = None
    for ligne in sortie_procstats.splitlines():
        processus = re.match(r"\s*\*?\s*([\w.]+)\s*/\s*u\d+", ligne)
        if processus and "/" in ligne:
            paquet_courant = processus.group(1)
            continue
        if paquet_courant is None:
            continue
        memoire = re.search(
            r"PSS:\s*min=(\d+)\s+avg=(\d+)\s+max=(\d+)", ligne
        )
        if memoire:
            applis.append({
                "paquet": paquet_courant,
                "min_mo": round(int(memoire.group(1)) / 1024),
                "moyenne_mo": round(int(memoire.group(2)) / 1024),
                "max_mo": round(int(memoire.group(3)) / 1024),
            })
            paquet_courant = None
    if not applis:
        return {
            "applis": [],
            "resume": (
                "Mémoire par appli dans le temps illisible sur ce téléphone."
            ),
        }
    applis.sort(key=lambda a: -a["moyenne_mo"])
    details = ", ".join(
        f"{a['paquet']} (moyenne {formater_mo(a['moyenne_mo'])})"
        for a in applis[:NOMBRE_TOP_MEMOIRE]
    )
    resume = f"Mémoire sur les dernières heures : {details}. "
    if applis[0]["moyenne_mo"] >= SEUIL_GROSSE_MEMOIRE_MO:
        resume += (
            f"{applis[0]['paquet']} garde en moyenne "
            f"{formater_mo(applis[0]['moyenne_mo'])}, c'est beaucoup."
        )
    else:
        resume += "Aucune appli ne garde une mémoire excessive."
    return {"applis": applis[:NOMBRE_TOP_MEMOIRE], "resume": resume}


def analyser_verrous_veille(sortie_power: str) -> dict:
    """Verrous empêchant la veille d'après dumpsys power.

    Liste ce qui retient le téléphone éveillé en ce moment.
    """
    eveil = re.search(r"mWakefulness=(\w+)", sortie_power)
    etat = eveil.group(1) if eveil else None
    verrous = []
    for trouve in re.finditer(
        r"(\S*WAKE_LOCK\S*)\s+'([^']+)'\s*\(uid=(\d+)", sortie_power
    ):
        verrous.append({
            "type": trouve.group(1),
            "nom": trouve.group(2),
            "uid": trouve.group(3),
        })
    taille = re.search(r"Wake Locks:\s*size=(\d+)", sortie_power)
    if taille and int(taille.group(1)) == 0:
        verrous = []
    if taille is None and not verrous and etat is None:
        return {
            "verrous": [],
            "resume": "Verrous de veille illisibles sur ce téléphone.",
        }
    if not verrous:
        resume = "Aucun verrou ne retient le téléphone, il peut dormir."
        if etat:
            resume += f" État actuel : {etat}."
        return {"etat": etat, "verrous": [], "resume": resume}
    details = ", ".join(
        f"{v['nom']}" for v in verrous[:NOMBRE_TOP_VERROUS]
    )
    resume = (
        f"{len(verrous)} verrous retiennent le téléphone éveillé : "
        f"{details}. "
    )
    if len(verrous) >= SEUIL_VERROUS_NOMBREUX:
        resume += "Beaucoup de verrous, la batterie peut fondre vite."
    else:
        resume += "Fermez les applis citées si la batterie fond."
    return {"etat": etat, "verrous": verrous, "resume": resume}
