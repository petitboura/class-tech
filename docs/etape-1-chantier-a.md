# Étape 1 : chantier A, structure du dépôt class-tech

Date : 28/10/2026.

## But

Créer la structure vide du nouveau dépôt class-tech, prête à recevoir la chaîne LLM (chantier B) puis le README (chantier C). Ne rien coder, ne rien publier.

## Vérifications avant de commencer

- C:\Users\dell\class-tech existe et ne contient que .git (clone frais, vide). Condition remplie, chantier lancé.
- Origine du clone : https://github.com/petitboura/class-tech.git (lue dans .git/config).
- Dépôts sources étudiés en lecture seule, jamais modifiés :
  - C:\Users\dell\classinus-backend : README.md (structure core/, api/, connexions/, indexers/, migrations/, scripts/, ...), CLAUDE.md (2 règles), .gitignore, requirements.txt.
  - C:\Users\dell\classinus-frontend : README.md (structure Next.js app/, components/, lib/, ...), CLAUDE.md (6 règles), .gitignore, .env.local.example, package.json.

## Fichiers créés

- MUSE.md : fusion des deux CLAUDE.md, adaptée à class-tech (backend aujourd'hui, règles frontend en sommeil, chantiers A/B/C, lecture seule des sources).
- .gitignore : fusion des deux .gitignore (Python + Next.js), chemins frontend préfixés par frontend/.
- backend/LISEZ-MOI.md : rôle de chaque dossier (api/, core/, connexions/, indexers/, migrations/, scripts/, tests/).
- backend/api/.gitkeep, backend/core/.gitkeep, backend/connexions/.gitkeep, backend/indexers/.gitkeep, backend/migrations/.gitkeep, backend/scripts/.gitkeep, backend/tests/.gitkeep : dossiers vides conservés dans git.
- frontend/LISEZ-MOI.md : note "phase plus tard", rien à construire.
- docs/README.md : base de la doc (un fichier par étape).
- docs/etape-1-chantier-a.md : ce fichier.

## Choix faits

- Structure backend miroir de classinus-backend (mêmes noms de dossiers), sans les dossiers désactivés ni le déploiement (Dockerfile, Procfile, railpack) : le chantier B amènera le code, avec son déploiement si besoin.
- Pas de __init__.py ni de code : tout code backend appartient au chantier B.
- LISEZ-MOI.md dans les sous dossiers plutôt que README.md, pour ne pas confondre avec le README.md racine du chantier C.
- Règles frontend gardées dans MUSE.md mais marquées "en sommeil" : elles s'appliqueront quand frontend/ sera construit.
- .gitignore avec .venv/ et .pytest_cache/ en plus des sources, pour un environnement Python propre.

## Interdits respectés

- README.md racine : ni créé ni modifié (chantier C).
- Code de la chaîne LLM : aucun (chantier B).
- Ni commit ni push.
- Sources classinus-backend et classinus-frontend : lues seulement, aucune modification.

## Suites

- Chantier B : amener la chaîne LLM dans backend/ (remplace les .gitkeep).
- Chantier C : écrire le README.md racine.
- Phase plus tard : construire frontend/.
