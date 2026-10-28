"""Lecture des réponses matérielles du téléphone (palier 100 %).

Fonctions pures : chacune reçoit la sortie brute d'une commande adb et
renvoie un dictionnaire de faits, avec un résumé en français simple
prêt à relayer. Testées sans téléphone (voir tests/test_diagnostic_100).

Sans dépendance externe (stdlib uniquement).
"""

from __future__ import annotations

import math
import re
import struct
import wave

# Codes de touches physiques vus dans `getevent -p` (hexadécimal),
# traduits en noms simples. Source : codes d'événements Linux.
NOMS_TOUCHES = {
    0x66: "accueil",
    0x72: "volume bas",
    0x73: "volume haut",
    0x74: "marche/arrêt",
    0x9E: "retour",
    0xD4: "appareil photo",
    0xE7: "assistant vocal",
    0xF4: "appel",
    0xF5: "fin d'appel",
    0x244: "applis récentes",
}

# Code ABS_MT_POSITION_X : position tactile multi-doigts. Sa présence
# prouve un écran tactile multipoint.
CODE_ABS_MULTITOUCH = 0x35


def lister_peripheriques_entree(sortie_getevent_p: str) -> list[dict]:
    """Inventaire des périphériques d'entrée d'après `getevent -p`.

    Renvoie une liste de {"nom": str, "touches": [int], "absolus": [int]}.
    Les lignes de continuation (codes sur plusieurs lignes) sont suivies.
    """
    peripheriques = []
    courant = None
    section = None
    for ligne in sortie_getevent_p.splitlines():
        if ligne.startswith("add device"):
            courant = {"nom": "", "touches": [], "absolus": []}
            peripheriques.append(courant)
            section = None
            continue
        if courant is None:
            continue
        depouillee = ligne.strip()
        if depouillee.startswith("name:"):
            courant["nom"] = depouillee[5:].strip().strip('"')
            section = None
        elif re.match(r"KEY\s*\(0001\)\s*:", depouillee):
            section = "touches"
            _ajouter_codes(depouillee.split(":", 1)[1], courant["touches"])
        elif re.match(r"ABS\s*\(0003\)\s*:", depouillee):
            section = "absolus"
            _ajouter_codes(depouillee.split(":", 1)[1], courant["absolus"], premier_seul=True)
        elif re.match(r"[A-Z]+\s*\([0-9a-fA-F]+\)\s*:", depouillee):
            section = None
        elif section and re.match(r"^[0-9a-fA-F]{4}\b", depouillee):
            _ajouter_codes(depouillee, courant[section], premier_seul=(section == "absolus"))
    return peripheriques


def _ajouter_codes(texte: str, destination: list[int], premier_seul: bool = False) -> None:
    """Ajoute les codes hexadécimaux à 4 chiffres trouvés dans texte.

    premier_seul sert aux lignes ABS, où seul le premier code est un
    axe (la suite donne value, min, max, qui ressemblent à des codes).
    """
    trouves = re.findall(r"\b[0-9a-fA-F]{4}\b", texte)
    if premier_seul:
        trouves = trouves[:1]
    for morceau in trouves:
        destination.append(int(morceau, 16))


def nom_touche(code: int) -> str:
    """Nom simple d'un code de touche, ou son numéro sinon."""
    return NOMS_TOUCHES.get(code, f"touche 0x{code:02x}")


def generer_bip_wav(chemin: str, frequence: int = 880, duree_ms: int = 1200) -> None:
    """Écrit un bip pur en WAV (utilisé par le test haut-parleur)."""
    taux = 22050
    trames = int(taux * duree_ms / 1000)
    with wave.open(chemin, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(taux)
        for i in range(trames):
            amplitude = int(12000 * math.sin(2 * math.pi * frequence * i / taux))
            wav.writeframes(struct.pack("<h", amplitude))


def analyser_ecran(
    sortie_getevent_p: str,
    sortie_wm_size: str,
    sortie_wm_density: str,
    sortie_display: str,
) -> dict:
    """État de l'écran tactile d'après getevent, wm et dumpsys display."""
    tactile = False
    multitouch = False
    for peripherique in lister_peripheriques_entree(sortie_getevent_p):
        if "touch" in peripherique["nom"].lower():
            tactile = True
        if CODE_ABS_MULTITOUCH in peripherique["absolus"]:
            tactile = True
            multitouch = True
    taille = re.search(r"(\d+x\d+)", sortie_wm_size)
    densite = re.search(r"(\d+)", sortie_wm_density)
    allume = "mScreenState=ON" in sortie_display
    eteint = "mScreenState=OFF" in sortie_display
    if tactile and multitouch:
        verdict = "Écran tactile multipoint détecté par le téléphone."
    elif tactile:
        verdict = "Écran tactile détecté, multipoint non confirmé."
    else:
        verdict = "Aucun écran tactile détecté dans la liste du téléphone."
    details = []
    if taille:
        details.append(f"résolution {taille.group(1)}")
    if densite:
        details.append(f"densité {densite.group(1)}")
    if allume:
        details.append("écran allumé")
    elif eteint:
        details.append("écran éteint")
    resume = verdict
    if details:
        resume += f" ({', '.join(details)})."
    resume += (
        " Pour finir le test, touchez chaque coin de l'écran puis tracez "
        "une ligne sur toute la surface : dites si une zone ne répond pas."
    )
    return {
        "tactile_detecte": tactile,
        "multitouch": multitouch,
        "taille": taille.group(1) if taille else None,
        "densite": densite.group(1) if densite else None,
        "ecran_allume": allume if (allume or eteint) else None,
        "resume": resume,
    }


# Modes de localisation Android (settings secure location_mode).
MODES_LOCALISATION = {
    "0": "localisation coupée",
    "1": "appareils uniquement (GPS seul)",
    "2": "économie de batterie (réseau seul)",
    "3": "haute précision (GPS et réseau)",
}


def analyser_gps(mode_localisation: str, sortie_location: str) -> dict:
    """État du GPS d'après le mode et dumpsys location."""
    mode = mode_localisation.strip()
    libelle = MODES_LOCALISATION.get(mode)
    fournisseurs = {
        "gps": bool(re.search(r"(?i)\bgps\s*=\s*true\b", sortie_location)),
        "reseau": bool(re.search(r"(?i)\bnetwork\s*=\s*true\b", sortie_location)),
    }
    position_connue = bool(
        re.search(r"(?i)last[^:\n]*location[^:\n]*=.*gps", sortie_location)
        or re.search(r"(?i)Location\[gps", sortie_location)
    )
    if libelle is None:
        verdict = "Mode de localisation illisible sur ce téléphone."
    elif mode == "0":
        verdict = "Localisation coupée sur le téléphone."
    else:
        verdict = f"Localisation réglée sur {libelle}."
    if fournisseurs["gps"]:
        verdict += " Le GPS est actif."
    elif libelle is not None and mode != "0":
        verdict += " Le GPS ne semble pas actif."
    if position_connue:
        verdict += " Une position GPS récente est enregistrée."
    verdict += (
        " Pour finir le test, sortez à découvert et ouvrez une appli de "
        "carte : dites si votre position s'affiche en moins d'une minute."
    )
    return {
        "mode": mode,
        "mode_libelle": libelle,
        "gps_actif": fournisseurs["gps"],
        "reseau_actif": fournisseurs["reseau"],
        "position_connue": position_connue,
        "resume": verdict,
    }


def analyser_micro(sortie_audio: str) -> dict:
    """Indice de présence du micro d'après dumpsys audio."""
    indices = []
    for ligne in sortie_audio.splitlines():
        basse = ligne.lower()
        if "in_builtin_mic" in basse or "built-in micro" in basse or "builtin_mic" in basse:
            nettoyee = " ".join(ligne.split())
            if nettoyee not in indices:
                indices.append(nettoyee)
    micro = bool(indices)
    if micro:
        verdict = "Micro interne détecté par le système audio du téléphone."
    else:
        verdict = "Micro interne non confirmé dans l'état audio du téléphone."
    verdict += (
        " Pour finir le test, enregistrez un mémo vocal de quelques "
        "secondes puis réécoutez : dites si votre voix est claire."
    )
    return {"micro_detecte": micro, "indices": indices[:3], "resume": verdict}


def analyser_haut_parleur(sortie_audio: str) -> dict:
    """État audio (volumes, mode) d'après dumpsys audio."""
    volumes = {}
    for ligne in sortie_audio.splitlines():
        trouve = re.match(r"\s*(STREAM_\w+):", ligne)
        if not trouve:
            continue
        nom = trouve.group(1).replace("STREAM_", "").lower()
        muet = re.search(r"(?i)muted:\s*true", ligne) is not None
        maximum = re.search(r"[Mm]ax:\s*(\d+)", ligne)
        courant = re.search(r"\(\w+\):\s*(\d+)", ligne)
        volumes[nom] = {
            "muet": muet,
            "maximum": int(maximum.group(1)) if maximum else None,
            "courant": int(courant.group(1)) if courant else None,
        }
    mode = re.search(r"(MODE_\w+)", sortie_audio)
    morceaux = []
    for nom in ("music", "ring", "alarm", "voice_call"):
        if nom in volumes:
            v = volumes[nom]
            if v["courant"] is None or v["maximum"] in (None, 0):
                morceaux.append(f"{nom} : niveau illisible")
            elif v["muet"] or v["courant"] == 0:
                morceaux.append(f"{nom} : coupé ou à zéro")
            else:
                morceaux.append(f"{nom} : {v['courant']} sur {v['maximum']}")
    verdict = "État audio lu sur le téléphone"
    if mode:
        verdict += f" (mode {mode.group(1)})"
    verdict += " : " + (", ".join(morceaux) if morceaux else "volumes illisibles") + "."
    return {"volumes": volumes, "mode": mode.group(1) if mode else None, "resume": verdict}


def analyser_vibreur(sortie_vibrator: str, reussi: bool) -> dict:
    """Présence du vibreur d'après dumpsys vibrator."""
    details = []
    for ligne in sortie_vibrator.splitlines():
        basse = ligne.lower()
        if "capabilit" in basse or "supported" in basse or "effect" in basse or "vibrator" in basse:
            nettoyee = " ".join(ligne.split())
            if nettoyee and nettoyee not in details:
                details.append(nettoyee)
    present = reussi and bool(sortie_vibrator.strip())
    if present:
        verdict = "Vibreur détecté par le téléphone."
    else:
        verdict = "Vibreur non confirmé sur ce téléphone."
    return {"present": present, "details": details[:4], "resume": verdict}


def analyser_camera(sortie_camera: str) -> dict:
    """Caméras vues par le téléphone d'après dumpsys media.camera."""
    nombre = re.search(r"(?i)number of camera devices:\s*(\d+)", sortie_camera)
    if nombre:
        total = int(nombre.group(1))
    else:
        trouves = set(re.findall(r"(?i)(?:camera device|device)\s+(\d+)", sortie_camera))
        total = len(trouves)
    facades = []
    for trouve in re.findall(r"(?i)facing[:=\s]+(back|front)", sortie_camera):
        facades.append("arrière" if trouve.lower() == "back" else "avant")
    if total == 0:
        verdict = "Aucune caméra détectée par le téléphone."
    elif total == 1:
        verdict = "1 caméra détectée par le téléphone."
    else:
        verdict = f"{total} caméras détectées par le téléphone."
    if facades:
        verdict += f" ({', '.join(facades)})."
    return {"nombre": total, "facades": facades, "resume": verdict}


def analyser_boutons(sortie_getevent_p: str) -> dict:
    """Boutons physiques déclarés d'après `getevent -p`."""
    boutons = []
    for peripherique in lister_peripheriques_entree(sortie_getevent_p):
        for code in peripherique["touches"]:
            nom = nom_touche(code)
            if nom not in boutons and not nom.startswith("touche 0x"):
                boutons.append(nom)
    if boutons:
        verdict = f"Boutons déclarés par le téléphone : {', '.join(boutons)}."
    else:
        verdict = "Aucun bouton physique déclaré par le téléphone."
    return {"boutons": boutons, "resume": verdict}


def analyser_ecoute_boutons(sortie_getevent: str) -> dict:
    """Touches appuyées pendant l'écoute (getevent -l ou brut)."""
    recues = []
    for ligne in sortie_getevent.splitlines():
        nomme = re.search(r"KEY_(\w+)\s+(DOWN|UP)", ligne)
        if nomme and nomme.group(2) == "DOWN":
            nom = nomme.group(1).lower().replace("_", " ")
            if nom not in recues:
                recues.append(nom)
            continue
        brut = re.search(r"\b0001\s+([0-9a-fA-F]{4})\s+00000001\b", ligne)
        if brut:
            nom = nom_touche(int(brut.group(1), 16))
            if nom not in recues:
                recues.append(nom)
    if recues:
        verdict = f"Touches reçues par le téléphone : {', '.join(recues)}."
    else:
        verdict = "Aucune touche reçue pendant l'écoute."
    return {"touches_appuyees": recues, "resume": verdict}
