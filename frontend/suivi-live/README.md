# Suivi en direct (page publique)

Page web qui affiche la documentation du projet pour le public :
elle lit les fichiers `docs/` en direct sur la branche main GitHub
et se ré-affiche seule toutes les heures.

- Page : https://petitboura.github.io/class-tech/
- Dépôt lu : petitboura/class-tech, branche main
- Actualisation : toutes les 60 minutes (voir `config.js`,
  `refreshMinutes`), plus au retour sur l'onglet si l'heure est
  passée. La mention « Dernière mise à jour » affiche la date et
  l'heure du dernier chargement réussi.

## Sections

Accueil (état du projet), Journal (progression regroupée par
heure, repliée, tri récent ou ancien, plus le journal complet),
Notes de Bourama (absente tant que Bourama ne dicte rien),
Bilan, Décisions, Étapes et documents, Contexte.

## Fichiers

- `index.html` : structure, balises Open Graph, appel des scripts.
- `config.js` : seul endroit avec le dépôt, la branche, la liste
  des documents et le délai. Rien d'autre n'est écrit en dur.
- `app.js` : lecture des documents, navigation, réaffichage horaire.
- `md.js` : petit rendu markdown maison (titres, listes, tableaux,
  code, liens). Testé sur les vrais docs (voir plus bas).
- `progression.js` : regroupement du journal par heure.
- `styles.css` : thème repris de Classinus (tons dorés, clair et
  sombre suivis du téléphone).
- `favicon.svg`, `apercu.jpg` : icône et image d'aperçu de partage.

## Vérifications avant de toucher

- `node C:\Users\dell\suivi-live-test\verifier.js` contrôle le rendu
  et le regroupement sur les vrais documents (compte la sonde hors
  dépôt, elle n'est pas livrée).
- Texte affiché : jamais de `--` ni de tiret long, français simple.

## Déploiement

La page est servie par GitHub Pages depuis la branche `gh-pages`
(racine = contenu de ce dossier). Pour republier après un
changement : committer ce dossier sur main, puis pousser le
sous-arbre vers `gh-pages` (voir l'historique des commandes dans
la session du 28/10/2026).
