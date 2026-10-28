# Bilan Bourama (ténu à jour à chaque phase)

Document demandé par Bourama le 28/10/2026 : ce qu'il voulait, ses
erreurs, ses décisions, ses délégations, son rôle. Sans filtre, sans
flatterie. Le détail daté vit dans `journal.md`, ce fichier est la
lecture qualitative.

## 1. Ce qu'il voulait faire

Un chatbot normal qui diagnostique par IA : téléphones Android via le
PC d'abord (sans root), puis PC, puis élargir. Le LLM ne fait que des
appels d'outils, lecture libre, et rien ne se corrige sans son OK.
V1 à 80 %, puis 100 %, puis root. Cap tenu du début (S1) à ce jour.

## 2. Erreurs des deux côtés, séparées

### Côté Bourama (4, toutes corrigées)

- **E1 — Ordre de lancement des agents (S2).** L'activation s'est
  retrouvée en file derrière les builders alors qu'elle devait passer
  devant. Détecté par Bourama lui-même, corrigé par repriorisation
  (activation faite par l'agent principal).
- **E2 — Hésitation chantier B (S2).** Annulé puis relancé en une
  minute. Coût nul : l'agent annulé n'avait rien produit.
- **E3 — Ambiguïté 100 % vs root (S1→S2).** L'ancien plan disait
  100 % = avec root ; redéfini ensuite en palier sans root.
  Clarifié ensemble, sans impact code.
- **E4 — Point de vigilance, pas une faute.** Outils root mergés et
  déployés (protégés par flags + hors catégorie). Risque couvert par
  l'audit en 3 agents exigé par Bourama lui-même.

### Côté Muse, l'IA (10, toutes corrigées)

- **M1 — Flux routeur présenté comme la prod (S2).** En réalité
  routeur mort, demander/garder réels. Trouvé par Bourama
  (« tu as manqué demander_outils »), corrigé par retraçage du vrai
  chemin exécuté. Faute : s'être fié aux commentaires.
- **M2 — Ordre et priorité des agents faux (S2).** Activation en file
  derrière les builders. Trouvé par Bourama (« t'as mal compris
  l'ordre »), corrigé par repriorisation + activation par moi.
- **M3 — Catégories proposées au lieu des paliers 80/100/root (S2).**
  Trouvé par Bourama (« non les outils... »), corrigé par relecture
  de l'ancienne session.
- **M4 — Interface à boutons proposée (S1).** Trouvé par Bourama
  (« c'est un chatbot normal »), corrigé (log S1).
- **M5 — Isolation worktree supposée dispo (S2).** 3 rejets runtime.
  Trouvé par le runtime, corrigé par fallback clones build-tmp.
- **M6 — Écritures fichiers en parallèle en conflit (S2).** Trouvé par
  moi (erreurs outil), corrigé en séquentiel.
- **M7 — edit_file multiligne sur fichier CRLF, 3 échecs (S2).**
  Trouvé par moi, corrigé par script python + consigne aux builders.
- **M8 — pip install dans l'interpréteur système avant le skill (S2).**
  Trouvé par rappel système, corrigé (venv ensuite).
- **M9 — Script check MCP sans follow_redirects, réponses vides (S2).**
  Trouvé par moi (test), corrigé.
- **M10 — Edit suivi devancé par commit git, recommit nécessaire (S2).**
  Trouvé par moi (git status), corrigé.

Total : 4 détectées par Bourama, 6 par moi, le système ou le runtime.
Détail bugs techniques dans `journal.md` §6.

## 3. Ce qu'il a décidé

Tout ce qui compte (détail daté dans `journal.md` §2) : périmètre
(pont PC, pas d'app seule, Windows d'abord), 3 phases (interface en
dernier), architecture serveur d'outils seule — sa meilleure
simplification —, branchement officiel, 6 agents + push autorisé,
activation par l'agent principal, interdiction des tests root, local
avant relais, Render en web service manuel.

## 4. Ce qu'il a délégué

Tout le code (readiness, 3 builders, fusion, audits), l'activation
technique, les vérifications, la documentation. Gardé pour lui : les
décisions go/no-go, le dashboard Render, le téléphone de test, les
tests via le chat. Voir `journal.md` §3 pour l'inventaire exact des
14 agents et leur résultat.

## 5. Son rôle

Décideur et valideur : il tranche, dit go ou non à chaque étape, et
teste en conditions réelles (téléphone branché, chat, Render). Jamais
exécutant du code. C'est le partage qui a fait avancer le projet sans
dérive : aucune ligne écrite sans son ordre, aucune décision
technique prise sans sa validation.
