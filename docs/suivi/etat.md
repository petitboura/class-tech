# État au 28/10/2026 au soir

## Phases (3, décidées par Bourama)

1. Configuration : TERMINÉE (structure, squelette puis réduction en
   serveur d'outils, README, décision d'archi).
2. Builder les outils + les connecter à Classinus : EN COURS
   (readiness OK. Activation sonde par moi : registre + migration +
   SQL + push faits ; reste création service Render puis test.
   Builders 80, 100 et root finis et fusionnés dans main (50 outils,
   branches supprimées, Render redéployé). Audit sécurité root lancé
   (2 parallèles puis 1 final : diagnostiquer + corriger, JAMAIS
   d'exécution live des outils root).
   Render live (17 outils listés). Test bout-en-bout ping OK via
   Clovis. Décidé : local d'abord pour valider, relais PC ensuite.
   Validation locale 80 OK sur vrai téléphone (Samsung SM-A055F,
   Android 13 : détection + batterie réelles). Reste : valider le
   palier 100 après fusion, relais PC à designer ensuite.
   Site suivi-live public + commentaires (nom optionnel, sans login)
   live et vérifiés 08:36 ; 3 lignes test à effacer au dashboard
   Supabase (table suivi_commentaires).
   Relais PC fini et vérifié 10:55 (branche relais-pc, main
   intacte) : santé + batterie réelle via relais ; pas de tunnel
   cloud ; merge dans main après audit final.
   B16 corrigé 11:12 et vérifié sur téléphone 11:23 (8 cœurs
   MT6768, test ciblé + 202 verts), poussé. Relais-install nettoyé
   11:18 ; relance agent installateur après le push B16.
3. Construire l'interface : après.

## Ce qui est en place (vérifié sur disque)

- `backend/` : serveur d'outils MCP seul. `api/main.py` monte
  `/mcp/diagnostic` (`uvicorn api.main:app` depuis backend/).
  2 outils exemple : sonde `verifier_chaine`, `resumer_symptome`.
  Registre réduit aux données signalétiques, test adapté OK,
  `LISEZ-MOI.md` à jour, MUSE.md à jour.
- `docs/` : traces etape-1 (A, B, C), décision etape-2, ce dossier suivi.
- `README.md` : vitrine rédigée, briefs des 3 images prêts.

## Restes connus (pas oubliés)

- README : sections À FINALISER contre le code réduit ; licence à
  choisir (Bourama) ; brief du schéma d'archi à ajuster (pas de
  Supabase pour l'instant).
- 3 petits textes approximatifs (`api/__init__.py`, `core/__init__.py`,
  docstring du serveur : mots "chaîne", "même processus").
- Lancement uvicorn réel jamais fait (dépendances non installées).

## En attente de Bourama

- Paliers tranchés : 80 % simple (12-15 outils), 100 % complet sans
  root (25-35 au total), root (45-60 au total). Reste : valider les 4
  boutons de départ (batterie, stockage, lenteurs, applis qui plantent).
- Validation locale palier 100 après la fusion (téléphone branché,
  même protocole que le palier 80).
- Libellé à choisir : « Téléphone branché ? » (proposé par le builder
  80) au lieu de « Détecter le phone ».
- Premières catégories d'outils phone à builder.
- Choix de la licence.
