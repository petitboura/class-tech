# Décisions et reste à faire (29/10/2026)

État vérifié de la nuit du 28 au 29 octobre. Langage simple, pour Bourama.

## Décisions prises

### Téléphone et relais
- D29 : les 5 outils sensibles sont validés pour le test en direct (jamais sans ordre en dehors de ça).
- D30 : le relais est intégré à Classinus PC, câble USB d'abord (le sans fil viendra plus tard).
- D31 : relais embarqué dans l'appli PC (un seul téléchargement).
- D36 : relais embarqué publié dans la 1.0.5.
- D37 : zéro étape. Brancher le téléphone et demander à l'IA suffit, le relais démarre tout seul. La carte Paramètres n'est qu'un voyant, ses boutons restant en secours.
- D17 : garder le libellé "Détecter le phone". Les boutons d'action sont repoussés en phase 3 (on passe par l'IA).
- D39 (29/10) : les outils téléphone s'exécutent via l'appli PC (pont vers le relais local), jamais sur le cloud. L'IA appelle, l'outil joint le téléphone tout seul, l'IA ne choisit rien.
- Jamais d'outil root sans ordre clair. Téléphone non rooté. Jamais de jailbreak.

### Diagnostic
- D33 : le root est écarté (rooter efface le téléphone).
- D34 : 10 outils profonds en lecture seule d'abord (niveau technicien), 16 autres après.
- D35 : pont iOS en lecture seule, sans jailbreak (4 outils de base, le reste étant impossible chez Apple).
- D38 : diagnostic du PC par l'appli installée, plus un secours de panne préparé.

### Versions PC
- D32 : publier une version PC pour que Bourama teste.
- 1.0.4 publiée (sans relais auto), 1.0.5 publiée (avec relais auto).

### Meta (staging uniquement, jamais la prod)
- Muse Spark 1.3 au niveau avancé, Muse Wonder au niveau pro, affichés en "Bientôt". Mode Standard seulement (jamais de version qui entraînerait Meta avec les données des élèves).
- NOUVEAU 29/10 : Meta passe AVANT Grok dans la liste (ça remplace "Meta en dernier").
- Règle permanente : un modèle affiche exactement les niveaux qu'il permet (6 chacun ici), on enlève ce qu'il refuse.

### Méthodes de travail (permanentes)
- Branches neuves depuis main, jamais de fusion vers main ou staging sans ordre. Vérification du dépôt distant au moment exact de pousser.
- Enregistrer très souvent (commit et push toutes les 30 minutes max), un dossier frais par agent.
- Français simple, jamais supposer ni deviner, toujours demander en cas de doute.
- Mémoire tenue à jour à chaque étape, reprise par lecture du fichier d'état.

## État actuel vérifié
- PC 1.0.5 en ligne avec relais auto (installeur environ 148 Mo). Le relais démarre seul, voit le Samsung branché, exécute les outils en local.
- Serveur d'outils : 41 outils sains sur Render (31 de base plus 10 profonds). Testé à chaud, à froid, en parallèle, avec arguments bizarres : répond toujours proprement.
- Meta staging : backend et frontend fusionnés et déployés, base migrée (1 fournisseur Meta en Bientôt, 2 modèles). Correctifs du panneau en attente, vérification visuelle à faire.
- Pont téléphone : côté serveur fait et testé (branche fix-pont-telephone, 7 tests verts, envoyée). Côté appli pas encore codé.
- Plus aucun agent en cours (tous arrêtés ou tombés, vérifié).

## Reste à faire, exactement
1. Pont téléphone côté appli : coder (réception canal plus méthode plugin RelaisPc), vérifications, envoyer la branche. Puis dire "fusionne" : fusion serveur (prod auto) plus appli, et release 1.0.6.
2. Installer la 1.0.6, brancher le téléphone, demander à l'IA : le test des vraies données.
3. Meta panneau : logo Meta en couleurs même grisé, Meta avant Grok (code plus base), vérification visuelle sur staging.
4. Diagnostic PC : relancer le travail (agent tombé sans rien écrire).
5. Sensibles : vibration, photo nette, test de retrait, sur ordre de Bourama, un par un.
6. Petits correctifs : bip inaudible, libellé caméras, caches non mesurés.
7. Côté Bourama, plus tard : clé Meta, vérification contrainte agents, 3 lignes de test, licence.
8. iOS : décider de la fusion, tester avec un vrai iPhone.
9. 16 outils restants après les 10 profonds (décision D34).

## Liens utiles
- Installeur 1.0.5 : https://github.com/petitboura/classinus-updates-pc/releases/latest/download/Classinus-Setup-1.0.5.exe
- Page des versions PC : https://github.com/petitboura/classinus-updates-pc/releases/latest
- Branche pont téléphone serveur : https://github.com/petitboura/classinus-backend/tree/fix-pont-telephone
- Serveur d'outils : https://class-tech-outils.onrender.com/mcp/diagnostic/
- Services Render : classinus-backend (prod), class-tech-outils, classinus-staging.
