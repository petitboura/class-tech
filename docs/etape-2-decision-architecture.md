# Étape 2 : décision d'architecture, class-tech devient un serveur d'outils

Date : 28/10/2026. Décidé par Bourama (3 réponses du 28/10).

## Décisions

1. Fini le backend complet dans class-tech : plus de chaîne LLM dupliquée
   (moteur, boucle, routes de diagnostic). Le cerveau reste dans
   Classinus, qui tourne déjà en prod.
2. class-tech ne contient que nos outils de diagnostic et leur serveur
   MCP. Classinus les appellera comme n'importe quel serveur d'outils ;
   `demander_outils` les trouvera, `garder_outils` les gardera.
3. Branchement en entrée officielle plus tard (entrée registre +
   migration SQL dans classinus-backend, geste normal d'ajout d'outil),
   pas en serveur personnalisé (confirmation exigée à chaque appel, même
   en lecture, vérifié dans le code).
4. Le squelette du chantier B est réduit au serveur d'outils (cette
   étape). La structure (A), les règles (MUSE.md) et le README (C)
   restent valables.

## Cible

```
Classinus (cerveau : routeur mort, demander_outils, garder_outils,
moteur MCP, confirmations, affichage)
   | appelle en HTTP MCP
class-tech/backend (serveur d'outils MCP : outils diagnostic + serveur)
```

## Sort des fichiers du chantier B

- SUPPRIMER : core/moteur_outils.py, core/fournisseur_llm.py,
  core/diagnostic.py, api/diagnostic.py, api/outils_registre.py.
- RÉDUIRE : api/main.py (app minimale qui monte /mcp/diagnostic,
  `uvicorn api.main:app` reste la commande), core/registre_outils.py
  (seules données signalétiques : noms, labels, icônes, onglets,
  catégories, sensibles + outils_de_la_categorie), tests adapté,
  backend/LISEZ-MOI.md (rôles réels).
- SUPPRIMER SI INUTILISÉS : core/configuration.py, .env.example (si plus
  rien ne les référence, sinon réduire au strict utile).
- GARDER : outils (core/outils_*.py), serveur (serveur_mcp_diagnostic.py),
  requirements.txt (dépendances utiles seules), docs/etape-1-*.md
  (traces, jamais réécrites), MUSE.md (mis à jour séparément).

## Interdits de cette étape

- Ne pas toucher à classinus-backend ni classinus-frontend (l'entrée
  officielle viendra plus tard, quand de vrais outils existeront).
- Ni commit ni push.

## Suites

- Mettre à jour MUSE.md (backend = serveur d'outils MCP, plus chaîne LLM).
- Finaliser les sections du README marquées À FINALISER contre le code
  réduit, puis générer les images.
- Construire les vrais outils diagnostic (téléphone d'abord).
- Quand ils existent : entrée officielle dans Classinus (registre +
  migration SQL).
