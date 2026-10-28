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
- core/registre_outils.py : données signalétiques des outils (noms, labels français, icônes, onglets, catégories, outils sensibles). Sans dépendance externe.
- connexions/ : vide, accueillera les connexions externes si un outil en a besoin un jour.
- indexers/, migrations/, scripts/ : dossiers réservés, vides pour l'instant.
- tests/ : tests sans dépendance externe.
- requirements.txt : dépendances utiles seules.

Lancement local (depuis backend/) :

    uvicorn api.main:app --port 8000

Tests :

    python tests/test_registre_outils.py

Pour ajouter un outil : mode d'emploi en tête de core/registre_outils.py.
