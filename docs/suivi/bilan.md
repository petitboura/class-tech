# Bilan Bourama (ténu à jour à chaque phase, 28/10/2026)

Document demandé par Bourama : ce qu'il voulait, ses erreurs, ses
décisions, ses délégations, son rôle. Sans filtre, sans flatterie. Le
détail daté vit dans `journal.md`, ce fichier est la lecture
qualitative. Heures locales du PC.

## 1. Ce qu'il voulait faire

Un chatbot normal qui diagnostique par IA : téléphones Android via le
PC d'abord (sans root), puis PC, puis élargir. Le LLM ne fait que des
appels d'outils, lecture libre, et rien ne se corrige sans son OK.
V1 à 80 %, puis 100 %, puis root. Cap tenu du début (S1, 01:23) à ce
jour.

## 2. Erreurs des deux côtés, séparées

### Côté Bourama (4, toutes corrigées)

- **E1 — Ordre de lancement des agents (05:43).** L'activation s'est
  retrouvée en file derrière les builders. Détecté par Bourama
  lui-même, corrigé par repriorisation (activation par moi).
- **E2 — Hésitation chantier B (04:25–04:26).** Annulé puis relancé
  en une minute. Coût nul : l'agent annulé n'avait rien produit.
- **E3 — Ambiguïté 100 % vs root (S1 01:33 → S2 05:02).** L'ancien
  plan disait 100 % = avec root ; redéfini en palier sans root.
  Clarifié ensemble, sans impact code.
- **E4 — Point de vigilance, pas une faute (07:10).** Outils root
  mergés et déployés (protégés par flags + hors catégorie). Risque
  couvert par l'audit en 3 agents exigé par Bourama lui-même.

### Côté Muse, l'IA (12, toutes corrigées)

- **M1 — Flux routeur présenté comme la prod (04:41).** En réalité
  routeur mort, demander/garder réels. Trouvé par Bourama,
  corrigé par retraçage du vrai chemin exécuté.
- **M2 — Ordre et priorité des agents faux (05:43).** Activation en
  file derrière les builders. Trouvé par Bourama, corrigé par
  repriorisation + activation par moi.
- **M3 — Catégories proposées au lieu des paliers (05:02).** Trouvé
  par Bourama, corrigé par relecture de l'ancienne session.
- **M4 — Interface à boutons proposée (S1 01:38).** Trouvé par
  Bourama (chatbot normal), corrigé (log S1).
- **M5 — Isolation worktree supposée dispo (05:26).** 3 rejets
  runtime. Trouvé par le runtime, corrigé (clones build-tmp).
- **M6 — Écritures fichiers en parallèle en conflit (05:03).** Trouvé
  par moi (erreurs outil), corrigé en séquentiel.
- **M7 — edit_file multiligne sur CRLF, 3 échecs (~06:02).** Trouvé
  par moi, corrigé (script python + consigne aux builders).
- **M8 — pip install système avant le skill (~07:00).** Trouvé par
  rappel système, corrigé (venv ensuite).
- **M9 — Check MCP sans follow_redirects (~07:03).** Trouvé par moi
  (test), corrigé.
- **M10 — Edit suivi devancé par commit (06:12).** Trouvé par moi
  (git status), corrigé (recommit).
- **M11 — Téléphone affirmé non rooté sans preuve (~10:20).**
  Trouvé par Bourama, corrigé par vérification outil sur son
  ordre (10:30) : non rooté confirmé.
- **M12 — Commit suivi parti sur la branche de l'agent (~21:45).**
  Le checkout partagé avait basculé sur outils-profonds.
  Trouvé par moi (sortie git), corrigé (rejoué sur main,
  branche remise au propre) ; clone frais imposé aux agents suivants.

Total : 5 détectées par Bourama, 7 par moi, le système ou le runtime.
Détail bugs techniques dans `journal.md` §6.

## 3. Ce qu'il a décidé

Tout ce qui compte (détail daté dans `journal.md` §2) : périmètre
(pont PC, pas d'app seule, Windows d'abord), 3 phases (interface en
dernier), architecture serveur d'outils seule — sa meilleure
simplification —, branchement officiel, 6 agents + push autorisé,
activation par l'agent principal, interdiction des tests root, local
avant relais, Render en web service manuel, site suivi public +
commentaires sans login.

## 4. Ce qu'il a délégué

Tout le code (readiness, 3 builders, fusion, audits), l'activation
technique, les vérifications, la documentation. Gardé pour lui : les
décisions go/no-go, le dashboard Render, le téléphone de test, les
tests via le chat. Voir `journal.md` §3 pour l'inventaire exact des
25 agents et leur résultat.

## 5. Son rôle

Décideur et valideur : il tranche, dit go ou non à chaque étape, et
teste en conditions réelles (téléphone branché, chat, Render). Jamais
exécutant du code. C'est le partage qui a fait avancer le projet sans
dérive : aucune ligne écrite sans son ordre, aucune décision
technique prise sans sa validation.
