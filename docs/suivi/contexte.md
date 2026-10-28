# Contexte stable

## But

Class-Tech : diagnostiquer par IA d'abord les téléphones (Android), puis
les PC, puis élargir. L'utilisateur décrit le problème avec ses mots,
l'IA guide le diagnostic, propose des corrections, et rien ne s'exécute
sans validation.

## Dépôts (C:\Users\dell)

- `class-tech` : le nouveau dépôt (GitHub petitboura/class-tech, public).
  C'est ici qu'on travaille.
- `classinus-backend`, `classinus-frontend` : les modèles, en lecture
  seule. On ne les modifie jamais sauf décision explicite (l'entrée
  officielle future du serveur diagnostic en sera une).

## Archi cible (décidée le 28/10/2026)

- Le cerveau reste dans Classinus : `demander_outils`, `garder_outils`,
  outils mémoire, confirmations, affichage. Tout ça tourne en prod.
- `class-tech/backend` est seulement un serveur d'outils MCP de
  diagnostic, que Classinus appellera en HTTP.
- Branchement prévu en entrée officielle (registre + migration SQL),
  pas en serveur personnalisé (confirmation exigée à chaque appel, même
  en lecture, vérifié dans le code).

## Prod Classinus, points vérifiés (ne pas se fier aux vieux commentaires)

- Routeur d'outils mort (`ROUTEUR_OUTILS_AUTO_DESACTIVE = True`).
- Le frontend envoie toujours `outil_force: []` (menu Outils retiré).
- Flux réel : paquet de départ (contexte + retenus + mémoire), puis le
  modèle tire ses outils avec `demander_outils` et les garde avec
  `garder_outils` (retenus en base, table `outils_retenus_conversation`).

## Paliers téléphone (décidés, détail à affiner)

- App seule sur le téléphone : abandonnée, trop limitée.
- Téléphone branché au PC (câble + mode développeur) : la voie V1, sans
  root, sans risque.
- Root : pour après, risqué.
- Périmètre : Android d'abord via pont PC (Windows d'abord), puis PC,
  puis scale.

## Règles clé de Bourama (détail dans MUSE.md et les skills)

- Jamais supposer, jamais deviner, toujours demander avant d'agir.
- S'en tenir strictement à la demande, ne rien ajouter par extrapolation.
- Ni commit ni push sans consigne explicite.
- Jamais de valeurs en dur, jamais de texte affiché avec "--".
- Expliquer en français simple, sans jargon.

## Sessions Muse

- Session du 28/10 au matin (`01a17fdc...`, interrompue avant la fin) :
  cadrage produit, connecteurs, chantiers A/B/C lancés (A fini, B et C
  jamais livrés là-bas).
- Session en cours (`01a1807a...`) : reprise, B et C relancés et livrés,
  décision serveur d'outils, réduction faite, suivi créé.
- Les logs vivent sous `.local/share/muse/sessions/AAAA/MM/JJ/<id>/`.

## Plan V1 outils (agréé le 28/10 au matin, ancienne session)

- Ordre : 80 % sans root d'abord (PC + câble), 100 % avec root après.
  App seule abandonnée.
- Interface : chatbot normal, langage simple, boutons tout prêts
  configurables (pas en dur). LLM via API, jamais full auto, que des
  appels d'outils. Lecture libre, corrections avec OK.
- Nombres : V1 80 % simple = 12 à 15 outils ; finale 80 % complète
  sans root = 25 à 35 ; 100 % root = 45 à 60.
- Étapes : 1) base connexion PC-phone (détection, infos de base),
  2) chat + 4 boutons (batterie, stockage, lenteurs, applis qui
  plantent), 3) outils V1 (batterie, stockage, applis, système,
  réseau, 1 test capteurs groupé), 4) finale 80 % (tests matériel
  unitaires, mémoire/CPU/RAM, permissions, sécurité, mises à jour),
  5) root (système profond, corrections profondes avec avertissement).
- Risque 1 : connexion câble stable, à valider en premier sur 2 à 3
  phones. Vie privée : seul du texte résumé part vers l'API.
- Évolution depuis : l'interface passe en dernier (phase 3), et le
  cerveau reste dans Classinus (décision serveur d'outils).
- Questions restées ouvertes : 4 boutons validés ?
