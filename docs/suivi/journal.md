# Journal strict (28/10/2026, heures locales du PC, ordre chronologique)

Heures relevées dans les logs de session et git. S1 : 01:23–03:15.
S2 : 04:09–en cours. Les faits marqués "(rapport)" viennent des
rapports d'agents ; tout le reste est vérifié (disque, git, base,
HTTP). `~` = minute approximative (déduite, pas relevée).

## 1. Sessions

- S1 `01a17fdc-ca05-7f50-a006-f2fd00a83aaa` (01:23–03:15, interrompue
  avant la fin) : cadrage produit, 3 niveaux, paliers 80/root, plan
  V1 (12-15 / 25-35 / 45-60 outils), connecteurs, 3 phases, chantiers
  A (fini), B et C (lancés, jamais livrés).
- S2 `01a1807a-5ac7-7080-b92e-e5bddc594b09` (dès 04:09) : reprise, B/C
  relancés et livrés, décision serveur d'outils, réduction, phase 2.

## 2. Décisions

S1 (01:23–03:15) : 01:33 V1 80 % sans root + app seule abandonnée ;
01:34 Windows d'abord ; 01:38 chatbot normal (corrige boutons) ;
02:23 connexion navigateur, pas token ; 02:51 build par étapes ;
03:00 3 phases ; 03:13–03:14 questions README (sans réponse, reprises
en S2).

| # | Heure | Décision | Statut | Pourquoi |
|---|-------|----------|--------|----------|
| D1 | 04:20 | Nouvelle session, pas `resume` | Active | Ancienne trop lourde (5000+ événements). |
| D2 | 04:25 | Relancer chantiers B et C | Active, exécutée | Finir la configuration. |
| D3 | 04:25 | Ne pas lancer B | Annulée (par D4) | Hésitation immédiate de Bourama. |
| D4 | 04:26 | Lancer B quand même | Active, exécutée | Ordre explicite. |
| D5 | 04:48 | class-tech = serveur d'outils seul | Active | Idée Bourama : inutile de tout ramener. Remplace D6. |
| D6 | — | Backend complet dupliqué | Abandonnée (D5) | Redondant avec la prod Classinus. |
| D7 | 04:48 | Branchement officiel | Active | Personnalisé = confirmation à chaque appel (vérifié). |
| D8 | 04:48 | Réduire le squelette B | Active, exécutée | Conséquence de D5. |
| D9 | 05:00 | 3 phases, interface en dernier | Active | Plan de Bourama. |
| D10 | 05:02 | Paliers 80 / 100 sans root / root | Active | Correction Bourama (ancien plan : 100 % = root). |
| D11 | 05:26 | Phase 2 en 6 agents + push OK | Active | Ordre explicite. |
| D12 | 05:26 | Fallback clones (isolation refusée) | Active | Runtime refuse le worktree ; base d'abord. |
| D13 | 05:49 | Activation par moi, agent annulé | Active, exécutée | Ordre explicite. |
| D14 | ~06:37 | Local d'abord, relais ensuite | Active | Render ne voit pas le téléphone branché au PC. |
| D15 | 07:13 | Jamais exécuter les root + audit 3 agents | Active, en cours | Trop risqué (ordre explicite). |
| D16 | 06:17 | Render en web service manuel | Active | Pas de blueprint trouvé. |
| D17 | — | Libellé « Téléphone branché ? » | EN ATTENTE | Proposé par builder 80. |
| D18 | — | 4 boutons + licence | EN ATTENTE | Questions ouvertes depuis S1. |
| D19 | 07:28 | Site public suivi-live (docs, refresh horaire) | Active, agent lancé | Bourama : que les gens suivent en direct. |
| D20 | 07:30 | Specs page : thème Classinus, heures repliées + tri, notes Bourama | Active | Dictées Bourama, transmises à l'agent. |
| D21 | 07:38 | Placement final A : class-tech Pages + lien Classinus + og: | Active | Route intégrée écartée ; aperçu partage exigé (balises og:). |

## 3. Agents (S2, ordre de lancement)

| # | Heures | Agent | Pourquoi | Statut et résultat |
|---|--------|-------|----------|--------------------|
| A1 | 04:25–04:25 | chantier-b/1 | Finir B (D2) | ANNULÉ avant tout travail (D3). |
| A2 | 04:26–~04:28 | chantier-c/2 | Finir C (D2) | FINI : README + briefs + doc. |
| A3 | 04:26–04:29 | chantier-b/3 | Finir B (D4) | FINI : squelette (réduit ensuite). |
| A4 | ~04:50–~04:59 | reduction | Réduire au serveur (D8) | FINI : 7 fichiers supprimés, test OK. |
| A5 | 05:26–05:40 | readiness | Base + sonde (D11) | FINI : 2 commits (`437f6da`, `7ed47e2`), `ping_serveur`, 9 tests. |
| A6 | 05:42 | activation/6 | Activer sonde (D11) | ÉCHEC démarrage (runtime), relancé A7. |
| A7 | 05:42–05:49 | activation/10 | Reprise A6 | ANNULÉ, fait par moi (D13). |
| A8 | 05:42–~06:47 | builder-80/7 | 14 outils + pont (D11) | FINI (rapport) : pont + 14, mergé, déployé, 37 tests, registre `81cfa3e`. |
| A9 | 05:42–06:22 | builder-100/8 | 14 outils 100 (D11) | FINI (rapport) : 14 outils, branche `0acb035`, activé `264e986`, 26 tests. |
| A10 | file 05:42, run 06:22–06:51 | builder-root/9 | 19 outils désactivés (D11) | FINI (rapport) : 19 outils, branche `ee71d60`, `disponible=false`. |
| A11 | ~06:52–07:11 | fusion/11 | Fusionner etc. (D11) | FINI (rapport) : merges `2ddb772`+`1bd634f`, branches supprimées, 50 outils live, 97 tests. |
| A12 | 07:14–07:52 | audit-a/12 | Diagnostiquer+corriger (D15) | FINI : 24 outils audités+corrigés, branche `audit-risques-a` (`c729c36`), non mergée. |
| A13 | dès 07:14 | audit-b/13 | Idem, indépendant (D15) | EN COURS. |
| A14 | — | audit-final | Trancher + corriger (D15) | À LANCER après A12+A13. |
| A15 | dès 07:28 | site-suivi-live/14 | Page publique (D19→D21) : class-tech Pages + lien Classinus, og:, notes | EN COURS. Redirigé 2 fois (route app puis retour plan A). |

S1 : 13 lancés 01:52–03:14, 11 livrés (inspecteur, lecteurs,
inventaire, audit connexions, 5 installateurs, audit README, chantier
A) ; B/C S1 lancés jamais livrés (repris en A2/A3).

## 4. Étapes et jalons vérifiés (heures)

- 05:38–05:39 : base + sonde poussées (`437f6da`, `7ed47e2`).
- 06:11 : activation poussée `40d176e` (rebase résolu par union).
- 06:12–06:13 : suivi vague 2 poussé.
- 06:15–06:17 : palier 80 poussé + mergé (`6bc8e09`, `baf3d08`).
- 06:19–06:21 : palier 100 poussé + activé (`0acb035`, `264e986`).
- ~06:26 : service Render créé par Bourama ; ~06:29 : URL répond 200,
  list_tools OK (adresse conforme au registre).
- 06:30 : correctif Render 80 (`1de1d0b`).
- 06:36 : test bout-en-bout ping via Clovis OK (réponse oui).
- 06:39 : registre 80 poussé (`81cfa3e`).
- 06:44–06:50 : palier root poussé + enregistré désactivé (`ee71d60`,
  `3f3f267`).
- ~07:02 : validation locale 80 sur vrai téléphone (R92WC0N34BP,
  Samsung SM-A055F, Android 13 : détection + batterie 83 %, 31,5 °C).
- 07:07–07:10 : fusion poussée (`2ddb772`, `1bd634f`), 50 outils.
- 07:17–07:22 : docs strictes (journal, bilan, bugs) poussées.

## 5. Règles de tenue de ce journal

- Toute décision de Bourama y entre avec statut (active / annulée /
  en attente) et motif ; une annulation n'efface jamais la ligne.
- Tout agent lancé y entre avec son pourquoi et son résultat.
- Faits vérifiés distingués des rapports d'agents.
- Chaque entrée porte date + heure relevées (logs session, git) dans
  le même geste que l'événement, jamais après coup.

## 6. Bugs et incidents (qui a trouvé, comment, quand)

| # | Heure | Quoi | Trouvé par | Comment | Corrigé par | Statut |
|---|-------|------|------------|---------|-------------|--------|
| B1 | ~06:05 | Montage HTTP MCP cassé | Builder 80 | Déploiement : rien ne répondait | Builder 80 | Corrigé, gardé par fusionneur |
| B2 | ~06:05 | Sessions MCP non démarrées | Builder 80 | Idem | Builder 80 | Corrigé |
| B3 | ~06:15 | Anti-rebond bloque hôte Render | Builder 80 | Idem | Builder 80 (via env) | Corrigé |
| B4 | 06:19 | pont_adb dupliqué, API divergentes | Builder 100 | Lecture des 2 branches | Fusionneur (pont unique) | Corrigé |
| B5 | 04:10 | Shell sandbox principal en panne | Moi | Échecs répétés | Contourné (escaladé + agents) | Ouvert (système) |
| B6 | ~06:55 | Approbations désactivées un temps | Moi | Appel refusé | Cause inconnue, refonctionne | Clos |
| B7 | 05:55 | Token Supabase mal décodé | Moi | API : JWT illisible | Moi (UTF-8) | Corrigé |
| B8 | 05:38 | Branche master + dépôt vide | Readiness | Inspection git | Readiness (main + push) | Corrigé |
| B9 | ~07:08 | Tests en égalité exacte après union | Fusionneur | pytest | Fusionneur (sous-ensemble) | Corrigé |
| B10 | ~04:55 | 3 textes approximatifs | Réduction | Relecture | Personne | Ouvert mineur |
| B11 | ~05:39 | Pas d'endpoint /health | Readiness | Lecture render.yaml | Personne (optionnel) | Ouvert mineur |
| B12 | S1 ~02:25 | Installateurs CLI bloqués EPERM | Installateurs S1 | Sorties shell | Non (contourné) | Clos S1 |
| B13 | 06:11 | Conflit rebase registre | Moi | Push avec sync | Moi (union, rien jeté) | Corrigé |
| B14 | 07:11 | Root joignables malgré false ? | Fusionneur (doute) | Lecture code | Audit en cours | SUSPECT, non confirmé |
| B15 | ~06:30 | Montage cassé resté en branches | Builder 80 | Comparaison | Fusionneur (gardé le sien) | Corrigé |
