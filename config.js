/* Configuration de la page suivi en direct.
   Seul endroit où figurent le dépôt, la branche et la liste des
   documents. Le contenu des documents est lu en direct sur GitHub,
   jamais copié ici. */
window.SUIVI_CONFIG = {
  owner: "petitboura",
  repo: "class-tech",
  branch: "main",
  refreshMinutes: 60,
  sections: [
    { id: "accueil", titre: "Accueil", fichiers: ["docs/suivi/etat.md"] },
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
  ]
};
