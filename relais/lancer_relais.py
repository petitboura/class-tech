"""Lance le relais PC Class-Tech. Double clic ou python relais/lancer_relais.py."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relais_config import (
    adresse_base,
    appliquer_chemin_adb,
    charger_reglages,
    preparer_imports,
    valider_reglages,
)


def main():
    """Lit les réglages puis démarre le serveur local."""
    reglages = charger_reglages()
    erreur = valider_reglages(reglages)
    if erreur:
        print(erreur)
        return 1
    erreur = appliquer_chemin_adb(reglages)
    if erreur:
        print(erreur)
        return 1
    preparer_imports()
    import uvicorn

    from serveur_relais import app

    base = adresse_base(reglages)
    print("Relais PC Class-Tech en route sur " + base)
    print("Page de sante : " + base + "/relais/sante")
    print("Branche le telephone en USB puis lance un diagnostic.")
    print("Arret avec Ctrl+C.")
    uvicorn.run(app, host=reglages["hote"], port=reglages["port"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
