# backend/ : serveur d'outils MCP de diagnostic (étape 2, palier 80 %)

Plus de chaîne LLM dans ce dossier : le cerveau (modèle, boucle
d'outils, confirmations, affichage) vit dans Classinus, qui appelle ce
serveur en HTTP MCP. Ici, seulement les outils de diagnostic et leur
serveur (voir docs/etape-2-decision-architecture.md).

Rôle de chaque fichier et dossier :

- api/main.py : app FastAPI minimale, monte le serveur MCP sur /mcp/diagnostic (avec démarrage explicite du gestionnaire de sessions).
- core/serveur_mcp_diagnostic.py : rassemble les modules d'outils sur l'objet partagé mcp_diagnostic.
- core/outils_diagnostic_commun.py : objet FastMCP partagé par tous les outils.
- core/outils_etat_appareil.py : outils exemple du squelette (sonde de santé, résumé du symptôme).
- core/outils_sonde.py : sonde de test ping_serveur (répond ok, version, heure).
- core/pont_adb.py : pont PC vers téléphone via ADB (recherche d'ADB, appareils, exécution, messages standards). Aucun outil, que du transport partagé.
- core/outils_telephone_base.py : détection du téléphone branché (modèle, version Android).
- core/outils_telephone_batterie.py : état batterie, conso par appli.
- core/outils_telephone_stockage.py : espace disque, gros fichiers, vide des caches (sensible).
- core/outils_telephone_applis.py : liste des applis, plantages récents, applis inutilisées.
- core/outils_telephone_systeme.py : version Android, erreurs récentes.
- core/outils_telephone_reseau.py : état réseau, détails wifi.
- core/outils_telephone_capteurs.py : test groupé des capteurs.
- core/registre_outils.py : données signalétiques des outils (noms, labels français, icônes, onglets, catégories, outils sensibles). Sans dépendance externe.
- connexions/ : vide, accueillera les connexions externes si un outil en a besoin un jour.
- indexers/, migrations/, scripts/ : dossiers réservés, vides pour l'instant.
- tests/ : tests (registre et pont ADB sans dépendance externe, le reste avec les dépendances installées).
- requirements.txt : dépendances utiles seules.

Lancement local (depuis backend/) :

    uvicorn api.main:app --port 8000

Tests (depuis backend/, dépendances installées) :

    pytest tests

Pour ajouter un outil : mode d'emploi en tête de core/registre_outils.py.
