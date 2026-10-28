"""Données signalétiques des outils de diagnostic (étape 2).

Réduit du squelette du chantier B : plus de parties serveur ni moteur
(le cerveau vit dans Classinus). Ne reste que la description des
outils : noms, labels français, icônes, onglets, catégories, outils
sensibles, plus outils_de_la_categorie().

POUR AJOUTER UN NOUVEL OUTIL :
déclare la fonction avec @mcp_diagnostic.tool() dans un module
core/outils_*.py, importe ce module dans serveur_mcp_diagnostic.py, puis
ajoute une entrée dans REGISTRE_AFFICHAGE_OUTILS ci-dessous et, si besoin,
dans CATEGORIES_OUTILS. Aucun autre fichier à toucher.

Ce module ne dépend d'aucune librairie externe, pour que les tests
du registre tournent sans rien installer.
"""

# Outils qui écrivent ou déclenchent une action réelle : Classinus
# interrompt pour confirmation avant exécution. Palier 100 % : bip de
# test, vibration de test, ouverture de l'appli photo, retrait d'une
# permission.
OUTILS_SENSIBLES = {
    "tester_haut_parleur",
    "tester_vibreur",
    "tester_camera",
    "revoquer_permission",
}

# Types d'appareils pris en charge, dans l'ordre du projet (téléphone
# d'abord, ordinateur ensuite). Source unique, lue par les outils
# (jamais recopiée ailleurs).
TYPES_APPAREILS = ("telephone", "ordinateur")

# Source unique de vérité pour l'affichage des outils côté futur site.
# Chaque entrée : label (texte affiché, 18 caractères au plus conseillés
# pour le téléphone), icone (nom lucide-react, converti par le site),
# onglet (None = outil jamais cliquable dans un menu, mais affiché
# quand il s'exécute dans le fil de discussion).
REGISTRE_AFFICHAGE_OUTILS = {
    "verifier_chaine": {
        "label": "Vérification",
        "icone": "Activity",
        "onglet": None,
    },
    "resumer_symptome": {
        "label": "Résumé du symptôme",
        "icone": "ClipboardList",
        "onglet": "diagnostiquer",
    },
    "ping_serveur": {
        "label": "Ping serveur",
        "icone": "Radio",
        "onglet": None,
    },
    # --- Palier 100 % : tests matériel unitaires ---
    "tester_ecran_tactile": {
        "label": "Test écran tactile",
        "icone": "Smartphone",
        "onglet": "diagnostiquer",
    },
    "tester_gps": {
        "label": "Test GPS",
        "icone": "MapPin",
        "onglet": "diagnostiquer",
    },
    "tester_micro": {
        "label": "Test micro",
        "icone": "Mic",
        "onglet": "diagnostiquer",
    },
    "tester_haut_parleur": {
        "label": "Test haut-parleur",
        "icone": "Volume2",
        "onglet": "diagnostiquer",
    },
    "tester_vibreur": {
        "label": "Test vibreur",
        "icone": "Vibrate",
        "onglet": "diagnostiquer",
    },
    "tester_camera": {
        "label": "Test caméra",
        "icone": "Camera",
        "onglet": "diagnostiquer",
    },
    "tester_boutons": {
        "label": "Test boutons",
        "icone": "Power",
        "onglet": "diagnostiquer",
    },
    # --- Palier 100 % : mémoire, CPU, applis gourmandes ---
    "analyser_memoire_vive": {
        "label": "Mémoire vive",
        "icone": "MemoryStick",
        "onglet": "diagnostiquer",
    },
    "analyser_cpu": {
        "label": "Processeur (CPU)",
        "icone": "Cpu",
        "onglet": "diagnostiquer",
    },
    "analyser_applications_gourmandes": {
        "label": "Applis gourmandes",
        "icone": "Gauge",
        "onglet": "diagnostiquer",
    },
    # --- Palier 100 % : permissions, sécurité, mises à jour ---
    "lister_permissions_risquees": {
        "label": "Permissions à risque",
        "icone": "KeyRound",
        "onglet": "diagnostiquer",
    },
    "revoquer_permission": {
        "label": "Retirer une permission",
        "icone": "ShieldOff",
        "onglet": "diagnostiquer",
    },
    "verifier_securite": {
        "label": "Sécurité du téléphone",
        "icone": "ShieldCheck",
        "onglet": "diagnostiquer",
    },
    "verifier_mises_a_jour": {
        "label": "Mises à jour",
        "icone": "RefreshCw",
        "onglet": "diagnostiquer",
    },
}

# Verbe d'action -> (libellé, petite icône). Même source pour le texte
# et l'icône, pour que les deux ne se contredisent jamais.
VERBES_ACTIONS = {
    "verifier": ("Vérification", "Check"),
    "resumer": ("Résumé", "List"),
    "decrire": ("Description", "Eye"),
    "lister": ("Liste", "List"),
    "tester": ("Test", "FlaskConical"),
    "analyser": ("Analyse", "Activity"),
    "revoquer": ("Retrait", "ShieldOff"),
}

# Catégories d'outils, lues par outils_de_la_categorie.
CATEGORIES_OUTILS = {
    "telephone": ["resumer_symptome"],
    "ordinateur": ["resumer_symptome"],
    "commun": ["verifier_chaine", "ping_serveur"],
    "materiel": [
        "tester_ecran_tactile",
        "tester_gps",
        "tester_micro",
        "tester_haut_parleur",
        "tester_vibreur",
        "tester_camera",
        "tester_boutons",
    ],
    "performance": [
        "analyser_memoire_vive",
        "analyser_cpu",
        "analyser_applications_gourmandes",
    ],
    "securite": [
        "lister_permissions_risquees",
        "revoquer_permission",
        "verifier_securite",
        "verifier_mises_a_jour",
    ],
}


def outils_de_la_categorie(nom_categorie, outils_candidats):
    """Sous-ensemble de outils_candidats appartenant à nom_categorie.

    outils_candidats est au format outils pour LLM : chaque entrée est
    un dictionnaire qui porte function.name. Categorie inconnue ->
    liste vide, jamais un repli silencieux sur toute la liste.
    """
    noms = set(CATEGORIES_OUTILS.get(nom_categorie, []))
    return [o for o in outils_candidats if o["function"]["name"] in noms]
