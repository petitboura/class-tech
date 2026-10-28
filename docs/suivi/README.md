# Suivi du projet (mémoire entre les sessions)

Ce dossier est la mémoire du projet. Tout ce qui est important va ici,
pour reprendre dans une nouvelle session comme si de rien n'était.

## Les fichiers

- `contexte.md` : les faits stables (but, dépôts, archi, règles clé).
- `etat.md` : où on en est, ce qui est fini, ce qui est en cours, ce qui
  attend Bourama. Le fichier à lire en premier.
- `decisions.md` : les décisions prises, avec leur date.
- `journal.md` : le registre strict (décisions actives/annulées/en
  attente avec motifs, tous les agents avec pourquoi et résultat).
- `bilan.md` : le bilan Bourama (but, erreurs, décisions,
  délégations, rôle), tenu à jour à chaque phase.
- Les docs `etape-*.md` à la racine de `docs/` restent les traces
  détaillées de chaque étape (on ne les réécrit pas).

## Protocole (règle miroir dans MUSE.md)

- Début de session : lire `etat.md`, puis `decisions.md` (et
  `contexte.md` au besoin) avant d'agir.
- À chaque avancée importante : mettre à jour `etat.md` aussitôt, et
  `decisions.md` si une décision a été prise.
- Ne jamais laisser `etat.md` dire l'inverse du dépôt : en cas de doute,
  relire le code réel avant d'écrire.
