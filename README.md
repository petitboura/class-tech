# Suivi en direct (page publique)

Page web qui affiche la documentation du projet pour le public :
elle lit les fichiers en direct sur la branche main GitHub et se
ré-affiche seule toutes les 5 heures.

- Page : https://petitboura.github.io/class-tech/
- Dépôt lu : petitboura/class-tech, branche main
- Actualisation : toutes les 5 heures (voir `config.js`,
  `refreshMinutes`), plus au retour sur l'onglet si le délai est
  passé. La mention « Dernière mise à jour » affiche la date et
  l'heure du dernier chargement réussi, plus le compte à rebours
  avant la prochaine.

## Deux faces

Bascule Normal / Technique en haut de page (Normal par défaut),
même fond, deux niveaux de lecture.

Normal : Accueil (état + contexte hackathon), Journal
(progression regroupée par heure, repliée, tri récent ou ancien,
plus le journal complet), Notes de Bourama (état vide tant que
Bourama ne dicte rien), Bilan, Décisions, Étapes et documents,
Contexte.

Technique : Accueil, Commits (derniers commits sur main, en
direct), Outils (registre en direct : total, par palier, avec
mention quand une confirmation est exigée), Tests (totaux cités
dans le journal + fichiers de test sur main), Architecture,
Journal, Étapes et documents.

Le regroupement par heure affiche toutes les tranches, même
vides (« Rien pour l'instant »), sans jamais sauter une heure.

## Fichiers

- `index.html` : structure, balises Open Graph, appel des scripts.
- `config.js` : seul endroit avec le dépôt, la branche, la liste
  des documents, le délai et le contexte hackathon. Rien d'autre
  n'est écrit en dur.
- `app.js` : lecture des documents, navigation, faces, réaffichage.
- `md.js` : petit rendu markdown maison (titres, listes, tableaux,
  code, liens). Testé sur les vrais docs (voir plus bas).
- `progression.js` : regroupement du journal par heure.
- `technique.js` : lecture du registre d'outils et des totaux de
  tests cités dans le journal.
- `styles.css` : thème repris de Classinus (tons dorés, clair et
  sombre suivis du téléphone).
- `favicon.svg`, `apercu.jpg` : icône et image d'aperçu de partage.

## Vérifications avant de toucher

- `node C:\Users\dell\suivi-live-test\verifier.js` contrôle le rendu,
  le regroupement et le registre sur les vrais documents.
- `node C:\Users\dell\suivi-live-test\tirets.js` contrôle qu'aucun
  texte affiché ne contient `--` nu ni tiret long.
- `node C:\Users\dell\suivi-live-test\live.js` rejoue le chemin live
  exact (fichiers raw + API GitHub). Ces sondes vivent hors dépôt,
  elles ne sont pas livrées.
- Texte affiché : jamais de `--` ni de tiret long, français simple.

## Déploiement

La page est servie par GitHub Pages depuis la branche `gh-pages`
(racine = contenu de ce dossier). Pour republier après un
changement : committer ce dossier sur main, puis pousser le
sous-arbre vers `gh-pages` (voir l'historique des commandes dans
la session du 28/10/2026).
