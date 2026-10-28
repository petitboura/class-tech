# Étape 1 : chantier B, chaîne LLM dans backend/

Date : 28/10/2026.

## But

Amener la chaîne LLM dans class-tech/backend/, en squelette adapté au
nouveau projet (diagnostic du téléphone d'abord, de l'ordinateur
ensuite). Le squelette reprend l'architecture de classinus-backend (lu
en lecture seule, jamais modifié) : question reçue en HTTP, boucle avec
le modèle, outils via un serveur MCP interne, catalogue d'outils exposé.
Sans secrets, sans valeurs en dur, sans base de données pour l'instant.

## Vérifications avant de commencer

- C:\Users\dell\class-tech\backend existe avec la structure du chantier A
  (api/, core/, connexions/, indexers/, migrations/, scripts/, tests/,
  chacun avec .gitkeep, plus LISEZ-MOI.md). Condition remplie.
- C:\Users\dell\class-tech\docs\etape-1-chantier-a.md lu : le chantier B
  amène le code et le chantier C écrira le README racine.
- Skill classinus-standards-dev lu via read_skill, MUSE.md de class-tech
  lu. Règles appliquées : ne jamais deviner (les doutes sont listés plus
  bas au lieu d'être tranchés seul), aucune valeur en dur (tout passe
  par l'environnement), dépôts sources jamais modifiés.

## Sources lues dans classinus-backend (preuves)

Lecture seule uniquement. Ce qui a été repris de chaque fichier :

- api/chat.py : route POST /api/chat (fonction envoyer_message), payload
  Pydantic, conversion du générateur Python en flux SSE (data: {...} puis
  data: [DONE]) via StreamingResponse. Repris dans api/diagnostic.py.
- core/main.py : fonction chat(), générateur d'événements (statut,
  outil_resultat, reponse, confirmation_requise avec etat_reprise,
  meta). Repris en version courte dans core/diagnostic.py.
- core/boucle_agent.py : boucle qui appelle le modèle, exécute les outils
  demandés, interrompt sur outil sensible. Repris dans _boucle().
- core/registre_outils.py : SERVEURS_MCP (entrées nom, url_builder,
  headers_builder, outils_autorises, prefixe_outils),
  REGISTRE_AFFICHAGE_OUTILS (label, icone, onglet), VERBES_ACTIONS,
  CATEGORIES_OUTILS, OUTILS_SENSIBLES, outils_de_la_categorie().
  Repris en version réduite dans core/registre_outils.py.
- core/mcp_tools.py : moteur générique (list_tools sur chaque serveur,
  conversion au format LLM, rappel du bon serveur à l'exécution).
  Repris dans core/moteur_outils.py.
- core/outils_generation_commun.py : objet FastMCP partagé
  (mcp_generation = FastMCP(name=...)). Repris tel quel comme
  mcp_diagnostic dans core/outils_diagnostic_commun.py.
- core/serveur_mcp_generation.py : motif "rassembler les modules
  outils_*.py par import". Repris dans core/serveur_mcp_diagnostic.py.
- core/outils_minuteurs.py (outil gerer_minuteur) : motif d'outil
  (@mcp.tool(), paramètres typés, texte français renvoyé au modèle).
  Repris pour les deux outils exemples.
- core/serveur_mcp_public.py (outils ping, qui_suis_je) : motif de sonde
  de santé sans donnée utilisateur. Repris pour verifier_chaine.
- api/outils_registre.py : route GET /api/outils/registre qui sérialise
  le registre (outils, verbes_actions, prefixes_applis). Repris à
  l'identique dans api/outils_registre.py.
- api/main.py : app FastAPI, include_router des routes, montage des
  serveurs MCP via app.mount("/mcp/...",
  mcp.streamable_http_app(...)). Repris dans api/main.py.
- core/fournisseurs_llm.py et core/clients_outils_llm.py (rôle
  seulement) : appel modèle avec outils. Repris en version
  mono fournisseur OpenAI compatible dans core/fournisseur_llm.py.
- requirements.txt : versions repères (mcp==2.0.0). Reprise dans
  backend/requirements.txt.

## Fichiers créés

Tous dans C:\Users\dell\class-tech\backend (patch : aucun fichier du
chantier A modifié, aucun fichier modifié dans classinus-backend) :

- requirements.txt : dépendances (fastapi, uvicorn, mcp, httpx, pytest).
- .env.example : toutes les variables lues par le squelette, sans
  secrets. À copier vers .env (ignoré par git).
- core/configuration.py : seul module qui lit l'environnement
  (get_secret, PORT, délais, plafonds).
- core/registre_outils.py : SERVEURS_MCP (serveur interne diagnostic),
  TYPES_APPAREILS (telephone, ordinateur), REGISTRE_AFFICHAGE_OUTILS,
  VERBES_ACTIONS, CATEGORIES_OUTILS, OUTILS_SENSIBLES (vide),
  outils_de_la_categorie(). Sans dépendance externe.
- core/outils_diagnostic_commun.py : objet FastMCP partagé.
- core/outils_etat_appareil.py : outils exemples verifier_chaine
  (sonde) et resumer_symptome (fiche structurée, sans diagnostic).
- core/serveur_mcp_diagnostic.py : rassemble les modules d'outils,
  réexporte mcp_diagnostic.
- core/moteur_outils.py : liste les outils de chaque serveur MCP,
  exécute un outil sur le bon serveur.
- core/fournisseur_llm.py : appel modèle OpenAI compatible (adresse,
  clé, modèle depuis l'environnement). Erreur claire si non configuré.
- core/diagnostic.py : diagnostiquer(), générateur d'événements
  (statut, outil_resultat, reponse, confirmation_requise, meta,
  erreur), avec reprise après confirmation et filtre par appareil.
- api/diagnostic.py : route POST /api/diagnostic en flux SSE.
- api/outils_registre.py : route GET /api/outils/registre.
- api/main.py : app FastAPI, routes branchées, serveur MCP monté sur
  /mcp/diagnostic. Lancement : depuis backend/,
  uvicorn api.main:app (port 8000).
- api/__init__.py, core/__init__.py, connexions/__init__.py,
  tests/__init__.py : paquets Python (connexions reste vide, pour plus
  tard, comme prévu au chantier A).
- tests/test_registre_outils.py : cohérence du registre (serveurs,
  catégories, entrées complètes, aucun tiret double affiché, outils
  sensibles connus). Tourne sans dépendance externe.

## Comment la chaîne fonctionne

1. Le client envoie POST /api/diagnostic avec le message (et
   l'historique, la fiche, l'appareil, ou une reprise).
2. La route appelle diagnostiquer(), qui liste les outils via le moteur
   MCP (le serveur interne répond sur /mcp/diagnostic, même processus).
3. La boucle appelle le modèle avec les outils, exécute chaque outil
   demandé, renvoie les résultats au modèle, jusqu'à la réponse finale.
4. Chaque étape sort en flux SSE : statut, outil_resultat, reponse,
   puis meta. Un outil sensible déclenche confirmation_requise et attend
   l'accord avant de continuer.
5. Le futur site lit GET /api/outils/registre pour afficher les outils
   (labels, icônes) sans jamais coder leur liste en dur.

## Choix faits et simplifications assumées

- Noms adaptés au diagnostic (diagnostiquer, resumer_symptome,
  fiche_id, appareil) plutôt que copiés du scolaire (chat, eleve,
  conversation). La correspondance exacte est donnée plus haut.
- Imports en paquets (from core.x import ...) plutôt que le sys.path de
  la source : lancement depuis backend/, plus propre pour un dépôt neuf.
- Un seul serveur MCP interne (diagnostic), un seul outil métier
  exemple, une seule catégorie par appareil : le minimum qui prouve que
  la chaîne complète fonctionne.
- Fournisseur LLM au format OpenAI compatible, sans SDK : l'adresse, la
  clé et le modèle viennent de l'environnement, aucun fournisseur codé
  en dur (le choix reste ouvert, voir plus bas).
- Réponse en un seul bloc (pas de streaming mot à mot), pas de mémoire,
  pas d'historique persisté, pas de cascade multi modèles : repris plus
  tard depuis la source si besoin.
- OUTILS_SENSIBLES vide : aucun outil destructeur sans validation de
  Bourama. La plomberie de confirmation existe déjà et attend le premier
  outil sensible.
- Règle MUSE.md sur les données liées à un compte : sans objet pour ce
  squelette, qui ne stocke rien (ni table, ni fichier). Rappel noté dans
  l'outil exemple pour la première donnée future.
- Pas de mécanisme de traduction pour l'instant (signalé, comme le
  demande le skill quand il n'existe pas) : tous les textes sont en
  français direct.
- Les .gitkeep du chantier A sont laissés en place : ma consigne
  interdisait de toucher aux fichiers du chantier A, même si la doc du
  chantier A prévoyait leur remplacement. À trancher (voir plus bas).

## Points ouverts pour Bourama (à trancher, pas devinés)

1. Fournisseur LLM : Groq, OpenAI, Claude, Gemini, DeepSeek, autre ?
   Le squelette accepte tout service OpenAI compatible via .env, mais le
   choix officiel (et la clé) manque pour un premier vrai diagnostic.
2. Faut il retirer les .gitkeep maintenant que le code est là, ou les
   garder tant que indexers/, migrations/ et scripts/ sont vides ?
3. Authentification : confirmer qu'on reste sans comptes (donc sans
   user_id) jusqu'à nouvel ordre.
4. Base de données : confirmer que le squelette reste sans état (pas de
   Supabase) pour l'instant.
5. Contrat du futur site : les formats SSE et registre sont repris de
   la source, à valider quand le site se construira.

## Vérifications faites

- Compilation de tous les fichiers : python -m compileall sur api,
  core, tests, connexions, sans erreur.
- Test du registre : python tests/test_registre_outils.py affiche OK
  (7 contrôles : serveurs, catégories, entrées, tirets doubles,
  sensibles, filtre, appareils).
- Câblage complet avec doublures des librairies tierces (script
  temporaire, supprimé après usage) : routes branchées, serveur MCP
  monté, outils enregistrés, chemins sans LLM (message vide, reprise
  incomplète, outils exemples, flux SSE, registre), aucun tiret double
  dans les textes affichés. Affiche OK.
- Recherche de tirets doubles dans backend : uniquement dans une
  commande shell en commentaire et dans le test qui les interdit, jamais
  dans un texte affiché.
- Lancement réel non fait ici : les dépendances (fastapi, mcp, httpx)
  ne sont pas installées sur ce poste et le modèle demande une clé.
  Commande prévue : depuis backend/, pip install -r requirements.txt
  puis uvicorn api.main:app (port 8000).

## Interdits respectés

- README.md racine : ni créé ni modifié (chantier C).
- MUSE.md : non modifié.
- Fichiers du chantier A (LISEZ-MOI.md, .gitkeep, etape-1-chantier-a.md,
  docs/README.md, .gitignore) : non modifiés.
- classinus-backend : lu seulement (11 fichiers lus, voir plus haut),
  aucune modification.
- Ni commit ni push.

## Suites

- Chantier C : écrire le README.md racine (contrat du dépôt).
- Réponses de Bourama aux 5 points ouverts, puis premier vrai tour de
  diagnostic avec le fournisseur retenu.
- Plus tard : mémoire, historique, comptes, streaming mot à mot,
  deuxième outil métier, puis frontend/.
