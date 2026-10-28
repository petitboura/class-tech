/* Configuration de la page suivi en direct.
   Seul endroit où figurent le dépôt, la branche, la liste des
   documents et les réglages. Le contenu des documents est lu en
   direct sur GitHub, jamais copié ici. */
window.SUIVI_CONFIG = {
  owner: "petitboura",
  repo: "class-tech",
  branch: "main",
  refreshMinutes: 300,
  hackathon: {
    nom: "Meta Global Hackathon 2026",
    organisateur: "Meta Superintelligence Labs",
    detail: "Mondial, en ligne, 10 jours, 1 million de dollars de prix",
    urlAnnonce: "https://dev.meta.ai/events/global-hackathon"
  },
  technique: {
    commitsNombre: 15,
    outilsFichier: "backend/core/registre_outils.py",
    testsDossier: "backend/tests"
  },
  faces: [
    { id: "normal", titre: "Normal" },
    { id: "technique", titre: "Technique" }
  ],
  sectionsNormal: [
    { id: "accueil", titre: "Accueil", fichiers: ["docs/suivi/etat.md"], hackathon: true },
    { id: "journal", titre: "Journal", fichiers: ["docs/suivi/journal.md"], progression: true },
    { id: "notes", titre: "Notes de Bourama", fichiers: ["docs/suivi/notes-bourama.md"], optionnel: true },
    { id: "bilan", titre: "Bilan", fichiers: ["docs/suivi/bilan.md"] },
    { id: "decisions", titre: "Décisions", fichiers: ["docs/suivi/decisions.md"] },
    {
      id: "etapes",
      titre: "Étapes et documents",
      fichiers: [
        "docs/README.md",
        "docs/etape-1-chantier-a.md",
        "docs/etape-1-chantier-b.md",
        "docs/etape-1-chantier-c.md",
        "docs/etape-2-decision-architecture.md",
        "docs/briefs-images.md",
        "docs/suivi/README.md"
      ]
    },
    { id: "contexte", titre: "Contexte", fichiers: ["docs/suivi/contexte.md"] }
  ],
  sectionsTechnique: [
    { id: "accueil", titre: "Accueil", fichiers: ["docs/suivi/etat.md"], hackathon: true },
    { id: "commits", titre: "Commits", type: "commits" },
    { id: "outils", titre: "Outils", type: "outils" },
    { id: "tests", titre: "Tests", type: "tests", fichiers: ["docs/suivi/journal.md"] },
    { id: "architecture", titre: "Architecture", fichiers: ["docs/etape-2-decision-architecture.md"] },
    { id: "journal", titre: "Journal", fichiers: ["docs/suivi/journal.md"], progression: true },
    {
      id: "etapes",
      titre: "Étapes et documents",
      fichiers: [
        "docs/README.md",
        "docs/etape-1-chantier-a.md",
        "docs/etape-1-chantier-b.md",
        "docs/etape-1-chantier-c.md",
        "docs/briefs-images.md",
        "docs/suivi/README.md"
      ]
    }
  ]
};
