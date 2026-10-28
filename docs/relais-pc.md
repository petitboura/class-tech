# Le relais PC Class-Tech

Date : 28/10/2026. Branche relais-pc.

## Le problème

Le serveur Class-Tech tourne dans le cloud. Le cloud ne voit pas le
téléphone branché en USB sur le PC de l'utilisateur. Sans relais, seul
le PC qui héberge le serveur peut diagnostiquer un téléphone.

## Le rôle exact du relais

Le relais est un petit serveur qui tourne sur le PC de l'utilisateur,
à côté du téléphone branché. Il réutilise tel quel le pont ADB et les
outils du dépôt. Il reçoit les demandes de diagnostic et les exécute
en local, là où le téléphone est visible.

## D'où il tourne

Sur le PC de l'utilisateur, dans le dossier du dépôt (branche
relais-pc). Un seul programme à lancer. Il écoute sur une adresse
locale, avec un port réglable dans relais/reglages.json.

## Comment le téléphone branché devient joignable

1. L'utilisateur branche son téléphone en USB, avec le débogage USB
   actif, et valide la demande sur l'écran du téléphone.
2. Le relais tourne sur ce même PC, donc le pont ADB existant trouve
   le téléphone par le câble, sans rien changer au code des outils.
3. Le diagnostic demandé est exécuté sur place et la réponse repart
   vers le demandeur.

## Schéma

```text
Produit visé :
[Telephone en USB] relié à [Relais sur le PC] relié à [Cerveau Classinus]
Le relais exécute près du téléphone. Le cerveau guide depuis le cloud.

Ce qui marche aujourd'hui :
[Telephone en USB] relié à [Relais sur le PC]
Le diagnostic local répond avec les vraies données du téléphone.
```

## Ce que le relais expose

- Le serveur d'outils MCP existant, sur /mcp/diagnostic, pour le
  branchement futur au cerveau.
- Deux routes simples pour le diagnostic local : /relais/sante
  (état et téléphone vu) et /relais/outil/nom (exécute un outil
  de lecture et renvoie son texte).
- Seulement des lectures. Les 5 outils sensibles et tous les outils
  root sont refusés par construction.

## Choix simples assumés

- Un seul programme, un seul port, pas de service à installer.
- Port, adresse, délai et chemin ADB en réglages, jamais en dur.
- Pas de tunnel vers le cloud dans cette version. Le diagnostic
  local marche. Le lien vers le cerveau viendra ensuite, par une
  connexion sortante depuis le relais, sans ouvrir de port sur le PC.

## Limites connues

- Le PC doit rester allumé, avec le relais lancé et le téléphone
  branché pendant le diagnostic.
- Windows d'abord. Le pont ADB sait chercher sur d'autres systèmes,
  mais seul Windows est testé.
- Un seul téléphone à la fois. S'il y en a plusieurs, le premier
  prêt est utilisé.
