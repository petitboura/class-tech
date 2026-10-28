# backend/ : serveur d'outils MCP de diagnostic (étape 2)

Plus de chaîne LLM dans ce dossier : le cerveau (modèle, boucle
d'outils, confirmations, affichage) vit dans Classinus, qui appelle ce
serveur en HTTP MCP. Ici, seulement les outils de diagnostic et leur
serveur (voir docs/etape-2-decision-architecture.md).

Rôle de chaque fichier et dossier :

- api/main.py : app FastAPI minimale, monte le serveur MCP sur /mcp/diagnostic.
- core/serveur_mcp_diagnostic.py : rassemble les modules d'outils sur l'objet partagé mcp_diagnostic.
- core/outils_diagnostic_commun.py : objet FastMCP partagé par tous les outils.
- core/outils_etat_appareil.py : outils exemple du squelette (sonde de santé, résumé du symptôme).
- core/outils_sonde.py : sonde de test ping_serveur (répond ok, version, heure).
- core/pont_adb.py : pont PC vers téléphone via ADB (transport partagé, repris du palier 80 %).
- core/pont_root.py : transport root partagé (commandes su, vérification root, marque non testé).
- core/outils_root_acces.py : vérification root, infos su et modules.
- core/outils_root_systeme.py : fichiers système protégés, erreurs et paniques noyau.
- core/outils_root_partitions.py : partitions, montages, intégrité du système.
- core/outils_root_batterie.py : batterie brute, températures, remise à zéro des stats.
- core/outils_root_firmware.py : firmware, bootloader, slot de démarrage A/B.
- core/outils_root_processus.py : processus gourmands, verrous de réveil.
- core/outils_root_corrections.py : corrections profondes (crashs, Dalvik, trim, reboot).
- core/registre_outils.py : données signalétiques des outils (noms, labels français, icônes, onglets, catégories, outils sensibles). Sans dépendance externe.
- connexions/ : vide, accueillera les connexions externes si un outil en a besoin un jour.
- indexers/, migrations/, scripts/ : dossiers réservés, vides pour l'instant.
- tests/ : tests sans dépendance externe.
- requirements.txt : dépendances utiles seules.

Palier root : 19 outils root (tous sensibles, confirmation exigée),
non testés sur appareil rooté (aucun disponible), chaque réponse le
signale.

Lancement local (depuis backend/) :

    uvicorn api.main:app --port 8000

Tests :

    python tests/test_registre_outils.py
    pytest tests/

Pour ajouter un outil : mode d'emploi en tête de core/registre_outils.py.
