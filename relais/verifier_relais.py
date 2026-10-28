"""Vérifie le relais avec le vrai téléphone branché.

Appelle la santé puis les trois lectures de preuve :
detecter_telephone, lire_batterie, lire_stockage. Affiche les
réponses et dit si la preuve est complète. Lecture seule.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relais_config import adresse_base, charger_reglages, valider_reglages

PREUVES = (
    ("detecter_telephone", "Telephone detecte"),
    ("lire_batterie", "Batterie"),
    ("lire_stockage", "Stockage"),
)


def main():
    """Joue la preuve et renvoie 0 si elle est complète."""
    import httpx

    reglages = charger_reglages()
    erreur = valider_reglages(reglages)
    if erreur:
        print(erreur)
        return 1
    base = adresse_base(reglages)
    delai = reglages["delai_lancement_s"]
    try:
        sante = httpx.get(base + "/relais/sante", timeout=delai).json()
    except Exception:
        print("Relais injoignable sur " + base + ". Lance le relais d'abord.")
        return 1
    print("Sante : " + str(sante.get("service", "")) + ", version " + str(sante.get("version", "?")))
    liaison = sante.get("liaison")
    if not isinstance(liaison, dict):
        liaison = {}
    if liaison.get("pret"):
        choisi = liaison.get("appareil_choisi") or {}
        print("Telephone pret : " + str(choisi.get("id", "?")))
    else:
        print("Telephone pas pret : " + str(liaison.get("message", "?")))
    reussites = 0
    for nom, marqueur in PREUVES:
        try:
            reponse = httpx.post(base + "/relais/outil/" + nom, json={}, timeout=delai).json()
        except Exception:
            print("Echec d'appel pour " + nom + ".")
            continue
        if reponse.get("ok"):
            texte = str(reponse.get("resultat", ""))
        else:
            texte = str(reponse.get("erreur", ""))
        print("Outil " + nom + " : " + texte)
        if reponse.get("ok") and marqueur in texte:
            reussites += 1
    if reussites == len(PREUVES):
        print("Preuve OK : les 3 lectures donnent les vraies donnees du telephone.")
        return 0
    print("Preuve incomplete : reussites " + str(reussites) + " sur 3.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
