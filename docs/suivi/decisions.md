# Décisions

- 28/10/2026 : app seule abandonnée (trop limitée). V1 = téléphone
  branché au PC, sans root. Root gardé pour après.
- 28/10/2026 : logiciel PC pour Windows d'abord.
- 28/10/2026 : travail en 3 phases (1 configuration, 2 outils +
  connexion Classinus pour tester vite, 3 interface).
- 28/10/2026 : class-tech devient un simple serveur d'outils MCP, pas
  de backend complet. Branchement à Classinus en entrée officielle
  plus tard. Squelette B réduit (voir
  docs/etape-2-decision-architecture.md).
- 28/10/2026 : classinus-backend et classinus-frontend restent en
  lecture seule (seule exception prévue : l'entrée officielle future,
  à valider au moment).
- 28/10/2026 : création de docs/suivi/ + règle de mise à jour
  permanente (ce fichier + MUSE.md).
- 28/10/2026 : phase 2 en 6 agents (readiness sur main, activation +
  déploiement Render, 3 builders sur branches outils-80/100/root,
  fusionneur avec push + redéploiement). Push GitHub autorisé. Le
  builder 80 % merge, pousse et déploie lui-même. Paliers : 80 %
  simple, 100 % complet sans root, root désactivé (disponible=false).
- 28/10/2026 : exécution adb en local d'abord pour valider les outils
  (zéro code en plus), relais PC ensuite pour le produit. Test
  bout-en-bout ping_serveur OK via Clovis.
- 28/10/2026 : interdiction d'exécuter les outils root (tests live).
  Audit sécurité en 3 agents après fusion (2 diagnostics+corrections
  parallèles, 1 final qui tranche et corrige pour de bon).
