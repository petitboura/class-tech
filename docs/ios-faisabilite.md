# Faisabilité iOS des 31 outils diagnostic

Branche ios-pont. Voie retenue : libimobiledevice sur PC Windows,
lecture seule, sans jailbreak (interdit). Tout ce qui demande un Mac,
Xcode ou un jailbreak est marqué impossible.

## Prérequis vérifiés en ligne

PC Windows :
r1. Apple Mobile Device Support (pilote USB + service usbmux). Fourni
    avec iTunes téléchargé depuis le site Apple (pas la version
    Microsoft Store) ou avec l'appli Apple Devices.
r2. Binaires Windows de libimobiledevice. Sources vues :
    jrjr/libimobiledevice-windows (versions courantes, ex v20260524),
    libimobiledevice-win32/imobiledevice-net (plus ancien),
    paquet MSYS2 mingw-w64-x86_64-libimobiledevice, ou scoop.
r3. Projet de référence : https://libimobiledevice.org/

iPhone :
r4. Câble USB, iPhone déverrouillé, "faire confiance à cet ordinateur"
    validé sur l'écran. Vérifiable en lecture seule passive avec
    idevicepair validate (aucun nouvel appairage déclenché).

## Légende

faisable : portable tel quel en lecture seule.
partiel : une partie seulement est lisible, le reste est bloqué par Apple.
impossible : bloqué par Apple sans jailbreak, à signaler tel quel.
porté : déjà écrit dans backend/core/outils_iphone_base.py.

## Outils communs (3, sans téléphone)

| outil | avis | pourquoi en 1 ligne |
|---|---|---|
| verifier_chaine | faisable | pur PC, rien à porter. |
| resumer_symptome | faisable | pur texte, rien à porter. |
| ping_serveur | faisable | sonde serveur, rien à porter. |

## Palier 80 pour cent (14)

| outil | avis | pourquoi en 1 ligne |
|---|---|---|
| detecter_telephone | porté | detecter_iphone via idevice_id + ideviceinfo. |
| lire_batterie | partiel + porté | niveau et charge portés, santé et température à valider en live. |
| lire_conso_batterie | impossible | iOS ne donne pas la conso par appli. |
| lire_stockage | porté | lire_stockage_iphone via domaine disk_usage. |
| lister_gros_fichiers | partiel | AFC ne montre que médias et dossiers partagés, pas tout le stockage. |
| vider_cache_applis | impossible | aucune API pour vider les caches, et ce serait une écriture. |
| lister_applis | partiel | ideviceinstaller liste les applis tierces, pas les systèmes, à valider. |
| lire_crashs_recents | partiel | idevicecrashreport récupère les rapports, format Apple, à valider. |
| lister_applis_inutilisees | impossible | pas de stats d'usage exposées par iOS. |
| lire_version_systeme | porté | lire_version_iphone via ProductVersion et BuildVersion. |
| lire_erreurs_recentes | partiel | idevicesyslog très filtré sur iOS récent, pas de tampon groupé. |
| lire_etat_reseau | impossible | état wifi et données mobiles non exposé en USB. |
| lire_infos_wifi | impossible | SSID et force du signal non exposés. |
| tester_capteurs | impossible | pas de lecture des valeurs capteurs en direct. |

## Tests matériel 100 pour cent (7)

| outil | avis | pourquoi en 1 ligne |
|---|---|---|
| tester_ecran_tactile | impossible | pas de lecture des touches ni d'injection. |
| tester_gps | impossible | pas de position exposée en USB. |
| tester_micro | impossible | pas d'enregistrement à distance. |
| tester_haut_parleur | impossible | pas de lecture audio à distance, et ce serait une action. |
| tester_vibreur | impossible | aucune commande vibration exposée. |
| tester_camera | impossible | pas de déclenchement photo à distance. |
| tester_boutons | impossible | pas de lecture des appuis boutons. |

## Performance 100 pour cent (3)

| outil | avis | pourquoi en 1 ligne |
|---|---|---|
| analyser_memoire_vive | impossible | mémoire vive non exposée en USB. |
| analyser_cpu | impossible | charge processeur non exposée. |
| analyser_applications_gourmandes | impossible | pas de top ni de stats par appli. |

## Sécurité 100 pour cent (4)

| outil | avis | pourquoi en 1 ligne |
|---|---|---|
| lister_permissions_risquees | impossible | permissions accordées non listables. |
| revoquer_permission | impossible | aucun retrait possible, et ce serait une écriture. |
| verifier_securite | partiel | version et modèle lisibles, pas l'état du verrouillage ni du patch. |
| verifier_mises_a_jour | impossible | pas d'état de mise à jour exposé en USB. |

## Compte

4 portés, 3 faisables sans téléphone, 6 partiels, 18 impossibles.
Total 31.

## Limites Apple trouvées

L1. Pas de shell à distance : aucun équivalent du shell ADB.
L2. Pas de journaux système complets sur iOS récent.
L3. Pas de stats batterie, mémoire, CPU ou usage par appli.
L4. Fichiers limités au partage AFC (médias, dossiers d'applis qui partagent).
L5. Aucune action test possible (son, vibration, photo, boutons).
L6. Diagnostics avancés (idevicediagnostics) dépendent du modèle et
    d'iOS, à valider en live un par un.

## Reste à valider en live (iPhone requis)

V1. Clés du domaine batterie (niveau, charge).
V2. Clés du domaine stockage (total, disponible).
V3. idevicepair validate sur iPhone non apparié puis apparié.
V4. ideviceinstaller et idevicecrashreport (liste applis, rapports).
V5. idevicediagnostics (santé batterie type nombre de cycles).

Statut live : non testé, iPhone requis.
