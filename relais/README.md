# Relais PC Class-Tech

Le relais est le petit serveur qui tourne sur ton PC, à côté du
téléphone branché en USB. Il exécute le diagnostic en local, là où le
téléphone est visible, avec les vrais outils Class-Tech.

## Étape 1 : préparer le téléphone et le PC

Sur le téléphone :

- Active le mode développeur puis le débogage USB.
- Branche le téléphone au PC avec un câble USB.
- Valide la demande d'autorisation sur l'écran du téléphone.

Sur le PC :

- Installe Python 3.12 ou plus récent.
- Installe les platform-tools Google (le programme ADB).

## Étape 2 : récupérer le relais et installer

- Récupère la branche relais-pc du dépôt class-tech sur ton PC.
- Depuis la racine du dépôt, installe les dépendances :

  python -m pip install -r backend/requirements.txt

## Étape 3 : lancer et vérifier

- Double clique sur Lancer-Relais.bat dans le dossier relais. Une
  fenêtre dit sur quelle adresse le relais écoute.
- Ouvre la page de santé dans un navigateur, à l'adresse dite par la
  fenêtre, plus /relais/sante.
- Preuve : python relais/verifier_relais.py affiche les vraies
  données du téléphone branché.

## Réglages

Tout est dans relais/reglages.json : hote (adresse d'écoute), port,
delai_lancement_s (attente maxi d'une réponse) et chemin_adb (vide
veut dire recherche auto, sinon chemin complet vers adb). Chaque
valeur peut aussi être forcée par une variable d'environnement :
RELAIS_PC_HOTE, RELAIS_PC_PORT, RELAIS_PC_DELAI, RELAIS_PC_ADB.
Aucun port ni chemin ni adresse n'est écrit en dur dans le code.

## Dépannage

- Téléphone pas vu : change de câble ou de port USB, vérifie le
  débogage USB, revalide la demande sur l'écran du téléphone.
- ADB introuvable : renseigne chemin_adb dans relais/reglages.json
  avec le chemin complet vers adb.
- Port occupé : change port dans relais/reglages.json puis relance.
- Relais injoignable : vérifie que la fenêtre du relais est toujours
  ouverte.

## Lecture seule

Le relais n'expose que des lectures. Les 5 outils sensibles et tous
les outils root sont refusés par construction.
