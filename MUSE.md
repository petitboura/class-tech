# Instructions permanentes pour Muse sur ce dépôt

Ce fichier remplace les anciens CLAUDE.md de Classinus (renommé pour Muse).
Il s'applique à tout le dépôt class-tech : backend/ aujourd'hui, frontend/ plus tard.

## Le dépôt et les chantiers

- class-tech a deux parties : backend/ (serveur d'outils MCP de diagnostic, le cerveau reste dans Classinus) et frontend/ (interface, phase plus tard).
- Les dépôts sources classinus-backend et classinus-frontend ont servi de modèles. Ils se lisent en lecture seule, on ne les modifie jamais depuis ce dépôt.
- Étape 1 terminée : chantier A (structure), chantier B (squelette, voir docs/etape-1-chantier-b.md), chantier C (README.md). Étape 2 (voir docs/etape-2-decision-architecture.md) : backend réduit au seul serveur d'outils, plus de chaîne LLM ici.
- README.md de la racine : sections À FINALISER contre le code réduit (voir docs/etape-1-chantier-c.md), ne le réécrire qu'avec une consigne explicite.
- Ni commit ni push sans consigne explicite de Bourama.
- En cas de doute, le code fait foi, pas les vieux documents.

## Jamais de tirets doubles ("--") dans un texte AFFICHÉ

Bourama déteste totalement les "--" (substitut de tiret long) dans tout texte qu'un utilisateur voit à l'écran. Concrètement, jamais dans :
- les messages d'erreur renvoyés par l'API ;
- le texte que les outils renvoient à l'IA pour être relayé en chat ;
- tout label, nom ou description généré et stocké pour être affiché ;
- plus tard côté frontend : labels, titres, placeholders, messages d'erreur, textes de boutons en JSX, et tout texte injecté dynamiquement.

Ça reste totalement acceptable dans :
- le code lui-même (commentaires, docstrings) ;
- les séparateurs markdown intentionnels de type ligne horizontale.

À la place : une virgule, un point, une parenthèse, ou reformuler la phrase.
À vérifier avant de livrer tout texte destiné à être affiché, sans que Bourama ait à le répéter.

## Toute nouvelle donnée liée à un utilisateur doit être purgée à la suppression du compte

Repris de classinus-backend (erreur constatée le 12/10/2026 : la suppression de compte ne supprimait qu'une partie des données, car presque aucune table n'a de suppression en cascade vers le compte).

Règle, à appliquer sans que Bourama ait à la répéter : chaque fois qu'on crée une table, une colonne ou un fichier de stockage qui contient une donnée d'un utilisateur (colonne user_id, owner_id, proprietaire_id, etudiant_id, auteur_id, etc.), dans la même livraison :
1. l'ajouter à la purge de compte (équivalent de core/purge_compte.py) ;
2. l'ajouter à l'export des données personnelles ;
3. préférer ON DELETE CASCADE vers auth.users, et ne jamais créer de clé étrangère sans cascade vers un compte (elle bloque la suppression) ;
4. vérifier le schéma réel de la base, pas seulement le code ;
5. si la donnée est volontairement gardée (journal de sécurité), le dire dans la politique de confidentialité.

Aucune table liée à un compte ne doit être livrée sans passer par ces points.

## Règles frontend (dorment jusqu'à la phase frontend)

Reprises de classinus-frontend. À appliquer dès qu'on construit dans frontend/ :

- Base FAQ/AEO : dès qu'une fonctionnalité, un comportement ou un affichage change, mettre à jour la documentation publique correspondante dans le même geste.
- Couche du haut réservée à l'agent (z-index) : les éléments de l'agent restent au dessus de tout (plein écran, popups, menus). Source unique pour ces valeurs, aucun autre élément ne les dépasse, jamais de valeur en dur ailleurs.
- STAGING : le blocage d'indexation de la copie de test ne va JAMAIS dans main ni en production. Ne jamais le copier, le fusionner ou l'assouplir, et vérifier chaque fusion de staging vers main.
- Menus, listes et bulles ancrés : toujours via le composant d'ancrage partagé, jamais de placement réglé au cas par cas.
- Listes et cases à cocher : jamais de select ni de checkbox natifs, toujours les composants maison. Le choix de langue vit dans les paramètres, pas en pastille flottante.

## Façon de travailler

- Ne jamais supposer, ne jamais deviner. En cas de doute, demander à Bourama avant d'agir.
- Avant d'ajouter quoi que ce soit, lire le code réel et vérifier l'état réel du dépôt (il peut avoir changé hors de cette conversation).
- S'en tenir strictement à la demande explicite, ne rien ajouter par extrapolation.
- Après chaque changement, vérifier son impact réel sur le fonctionnement, pas seulement que ça compile.
- Expliquer en langage simple, sans jargon inutile. Bourama n'a pas de background code.
- Tenir à jour docs/suivi/ (état, décisions, contexte) à chaque avancée importante, pour reprendre en nouvelle session comme si de rien n'était.
