# Class-Tech

Diagnostic technique intelligent, d'abord sur téléphone, puis sur PC, grâce à un modèle d'IA (LLM).

![Bannière Class-Tech](docs/img/banniere.png)

Class-Tech aide à comprendre ce qui ne va pas avec un appareil : l'utilisateur décrit le problème avec ses mots, et l'IA guide le diagnostic étape par étape. Le projet commence par les téléphones, puis s'étendra aux PC.

> Note : le dépôt est en construction. La chaîne IA (dossier `backend/`) arrive au chantier B, l'interface (dossier `frontend/`) dans une phase plus tard.

## Prérequis

> ⏳ À FINALISER après le chantier B (brouillon ci-dessous, à vérifier contre le vrai code).

Brouillon, inspiré du dépôt source classinus-backend :

- Python récent avec `pip`
- Une clé API pour au moins un fournisseur de modèle IA
- Une base Supabase (URL de projet et clé)

## Démarrage rapide

> ⏳ À FINALISER après le chantier B (brouillon ci-dessous, à vérifier contre le vrai code).

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Puis ouvrir la documentation interactive de l'API dans le navigateur.

![Schéma de démarrage](docs/img/schema-demarrage.png)

## Variables essentielles

> ⏳ À FINALISER après le chantier B (brouillon ci-dessous, à vérifier contre le vrai code).

| Variable | Rôle |
| --- | --- |
| Clé API du modèle IA | Permet au backend d'appeler le modèle |
| URL du projet Supabase | Adresse de la base de données |
| Clé Supabase | Accès à la base de données |

Les noms exacts seront confirmés quand le code du chantier B sera en place.

## Production en bref

> ⏳ À FINALISER après le chantier B.

Principe prévu : le même backend tourne en production avec des clés de production, derrière HTTPS. Les détails du déploiement (plateforme, commandes) seront écrits ici quand le chantier B aura apporté son mode de déploiement, s'il y en a un.

![Schéma d'architecture](docs/img/schema-architecture.png)

## Structure du dépôt

> ⏳ À FINALISER après les chantiers A et B. Brouillon basé sur le chantier A (structure vide vérifiée le 28/10/2026) :

```text
class-tech/
├── backend/      chaîne IA : api/, core/, connexions/, indexers/, migrations/, scripts/, tests/
├── frontend/     interface (phase plus tard, vide pour l'instant)
├── docs/         un fichier par étape du projet, plus les visuels dans docs/img/
├── MUSE.md     règles de travail sur ce dépôt
└── README.md     ce fichier
```

## Contribuer

Le projet est jeune et les règles de contribution ne sont pas encore écrites. En attendant : lire `MUSE.md` avant toute modification, ne toucher qu'à ce qui est demandé, et ne jamais deviner en cas de doute.

## Licence

⏳ À préciser par Bourama : aucune licence n'a encore été choisie pour ce dépôt.
