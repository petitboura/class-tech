# Étape 1 : chantier C, README vitrine de class-tech

Date : 28/10/2026.

## But

Écrire le README.md de la racine (vitrine du dépôt) et les briefs des visuels, sans toucher à aucun autre fichier. Ni commit ni push.

## Vérifications avant de commencer

- C:\Users\dell\class-tech existe (dépôt présent).
- README.md racine : absent (normal, réservé à ce chantier, confirmé dans docs/etape-1-chantier-a.md).
- État réel du dépôt relu le 28/10/2026 : MUSE.md, .gitignore, backend/LISEZ-MOI.md, frontend/LISEZ-MOI.md, docs/README.md, docs/etape-1-chantier-a.md. Aucun code backend, aucun requirements.txt, aucun exemple de variables : le chantier B n'a pas encore eu lieu (docs/etape-1-chantier-b.md absent).
- classinus-backend lu en lecture seule (requirements.txt : FastAPI, uvicorn, supabase, fournisseurs LLM). Aucun fichier d'exemple de variables trouvé dans classinus-backend. Sources non modifiées.
- Skill classinus-standards-dev et MUSE.md lus et appliqués : pas de supposition, doutes signalés ci-dessous au lieu d'être tranchés seul.
- Texte affiché vérifié : aucun "--" dans le README (règle MUSE.md).

## Fichiers créés

- README.md : titre, description courte (diagnostic phone puis PC par LLM), prérequis, démarrage rapide, variables essentielles, production en bref, structure du dépôt, contribuer, licence. Emplacements des visuels prévus : docs/img/banniere.png, docs/img/schema-demarrage.png, docs/img/schema-architecture.png.
- docs/briefs-images.md : trois briefs précis (contenu, style, nom de fichier) pour la bannière et les deux schémas. Les images elles-mêmes seront générées par un autre chantier.
- docs/etape-1-chantier-c.md : ce fichier.

## Choix faits

- Sections techniques (prérequis, démarrage rapide, variables, production) écrites en brouillon marqué "À FINALISER après le chantier B", inspiré de classinus-backend mais sans rien affirmer : il n'y a pas encore de code à vérifier dans class-tech, et en cas de doute le code fait foi.
- Section structure en 7 lignes, marquée "À FINALISER après les chantiers A et B", brouillon basé sur la structure vide vérifiée du chantier A.
- README rédigé en français simple, cohérent avec le reste du dépôt.

## Doutes signalés (à trancher par Bourama, pas par moi)

1. Commandes, versions et noms de variables du README : à confirmer contre le vrai code quand le chantier B sera livré.
2. Licence du dépôt : aucune choisie, section en attente dans le README.
3. Schéma d'architecture : mon brouillon suppose FastAPI plus Supabase plus LLM (repris de classinus-backend). Si le chantier B choisit autre chose, le brief est à revoir avant de générer l'image.

## Interdits respectés

- Aucun autre fichier touché. Ni commit ni push.

## Suites

- Chantier B : amener la chaîne IA dans backend/.
- Après le chantier B : finaliser les sections marquées ⏳ dans le README (commandes, variables, production, structure exacte).
- Autre chantier : générer les trois images vers docs/img/ en suivant docs/briefs-images.md.
- Bourama : choisir la licence.
