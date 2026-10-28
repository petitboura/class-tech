# Journal strict (ordre chronologique, J = 28/10/2026)

Tenu à jour à chaque décision et chaque agent. Les faits marqués
"(rapport)" viennent des rapports d'agents, pas encore revérifiés par
l'agent principal ; tout le reste est vérifié (disque, git, base, HTTP).

## 1. Sessions

- S1 `01a17fdc-ca05-7f50-a006-f2fd00a83aaa` (matin, interrompue avant la
  fin) : cadrage produit, 3 niveaux, paliers 80/root, plan V1 (12-15 /
  25-35 / 45-60 outils), connecteurs, 3 phases, chantiers A (fini), B
  et C (lancés, jamais livrés).
- S2 `01a1807a-5ac7-7080-b92e-e5bddc594b09` (en cours) : reprise,
  B/C relancés et livrés, décision serveur d'outils, réduction, phase 2.

## 2. Décisions (S2, sauf noté)

| # | Décision | Statut | Pourquoi / pourquoi annulée |
|---|----------|--------|------------------------------|
| D1 | Continuer en NOUVELLE session, pas en `resume` | Active | Ancienne trop lourde (5000+ événements, ~280 messages). |
| D2 | Relancer chantiers B et C non livrés en S1 | Active, exécutée | Finir la configuration. |
| D3 | Ne pas lancer B | Annulée 1 min après (par D4) | Hésitation immédiate de Bourama. |
| D4 | Lancer B quand même | Active, exécutée | Ordre explicite "lance le". |
| D5 | class-tech = serveur d'outils MCP seul, cerveau dans Classinus | Active | Proposé par Bourama : inutile de tout ramener, le seul but est que le LLM appelle les outils. Remplace D6. |
| D6 | Backend complet dupliqué dans class-tech | Abandonnée (remplacée par D5) | Redondant avec la prod Classinus. |
| D7 | Branchement officiel (registre + migration) | Active | Serveur personnalisé = confirmation à chaque appel, même en lecture (vérifié dans le code). |
| D8 | Réduire le squelette B au serveur seul | Active, exécutée | Conséquence de D5. |
| D9 | 3 phases : 1 config (finie), 2 outils+connexion, 3 interface | Active | Plan de Bourama (interface en dernier). |
| D10 | Paliers 80 simple / 100 complet sans root / root | Active | Correction de Bourama : affine l'ancien plan où 100 % = root. |
| D11 | Phase 2 en 6 agents + push GitHub autorisé | Active, exécutée avec D13 | Ordre explicite (readiness, activation, 3 builders sur branches, fusionneur). |
| D12 | Isolation worktree pour les builders | Impossible, fallback clones `build-tmp/` | Runtime refuse (dépôt non reconnu) ; ordre logique préservé : base d'abord. |
| D13 | Activation faite par moi, agent activation annulé | Active, exécutée | Ordre explicite "toi même fais". |
| D14 | Valider adb en local d'abord, relais PC ensuite | Active | Serveur Render ne voit pas le téléphone branché au PC ; local = zéro code pour valider vite. |
| D15 | Interdiction d'exécuter les outils root + audit en 3 agents | Active, en cours | Trop risqué (ordre explicite). |
| D16 | Render en web service manuel (pas de blueprint) | Active | Pas de blueprint trouvé par Bourama. |
| D17 | Libellé « Téléphone branché ? » | EN ATTENTE | Proposé par builder 80 contre « Détecter le phone ». |
| D18 | 4 boutons de départ + licence | EN ATTENTE | Questions ouvertes depuis S1. |

## 3. Agents (S2, ordre de lancement)

| # | Agent | Pourquoi lancé | Statut et résultat |
|---|-------|----------------|--------------------|
| A1 | chantier-b/1 | Finir B (D2) | ANNULÉ par Bourama avant tout travail (D3). |
| A2 | chantier-c/2 | Finir C (D2) | FINI : README + briefs images + doc étape. |
| A3 | chantier-b/3 | Finir B (D4) | FINI : squelette chaîne LLM (réduit ensuite par D8). |
| A4 | reduction | Réduire au serveur d'outils (D8) | FINI : 7 fichiers supprimés, MCP seul, test OK. |
| A5 | readiness | Base + sonde avant builders (D11) | FINI : PRÊT, 2 commits poussés (`437f6da`, `7ed47e2`), sonde `ping_serveur`, 9 tests, fichiers Render. |
| A6 | activation/6 | Activer la sonde (D11) | ÉCHEC démarrage (panne runtime), relancé en A7. |
| A7 | activation/10 | Reprise de A6 | ANNULÉ, fait par moi (D13). |
| A8 | builder-80/7 | 14 outils palier 80 + pont (D11) | FINI (rapport) : pont ADB + 14 outils, mergé (`baf3d08`), déployé, 37 tests, registre poussé (`81cfa3e`). |
| A9 | builder-100/8 | 14 outils palier 100 (D11) | FINI (rapport) : 14 outils, branche `outils-100` (`0acb035`), activé (`264e986`), 26 tests. |
| A10 | builder-root/9 | 19 outils root désactivés (D11) | FINI (rapport) : 19 outils, branche `outils-root` (`ee71d60`), `disponible=false`. |
| A11 | fusion/11 | Fusionner, nettoyer, redéployer (D11) | FINI (rapport) : merges `2ddb772`+`1bd634f`, branches supprimées, 50 outils live sur Render, 97 tests. |
| A12 | audit-a/12 | Diagnostiquer+corriger risques (D15) | EN COURS. |
| A13 | audit-b/13 | Idem, indépendant (D15) | EN COURS. |
| A14 | audit-final | Trancher + corriger pour de bon (D15) | À LANCER après A12+A13. |

S1 : 13 lancés, 11 livrés (inspecteur, lecteurs, inventaire, audit
connexions, 5 installateurs, audit README, chantier A) ; B/C lancés
jamais livrés (repris en A2/A3).

## 4. Étapes et jalons vérifiés

- Phase 1 finie : structure (A), squelette (B) puis réduction serveur,
  README (C), décision archi (étape 2).
- Activation sonde faite par moi : 5 entrées registre + migration SQL
  + ligne Supabase `disponible=true` (relue) + push `40d176e`
  (rebase résolu par union avec le travail parallèle).
- Service Render `class-tech-outils` créé par Bourama
  (`https://class-tech-outils.onrender.com`, `srv-dbgocjui0phs738j7heg`),
  répond 200, URL conforme au registre.
- Test bout-en-bout ping via Clovis : OK (réponse oui).
- Validation locale 80 sur vrai téléphone (R92WC0N34BP, Samsung
  SM-A055F, Android 13) : 17 outils listés, détection + batterie
  réelles (83 %, 31,5 °C).
- Fusion vérifiée sur disque : merges dans main, branches distantes
  supprimées, 50 outils = 3 base + 14 + 14 + 19.

## 5. Règles de tenue de ce journal

- Toute décision de Bourama y entre avec statut (active / annulée /
  en attente) et motif ; une annulation n'efface jamais la ligne.
- Tout agent lancé y entre avec son pourquoi et son résultat.
- Faits vérifiés distingués des rapports d'agents.
- Mis à jour dans le même geste que l'événement, jamais après coup.
