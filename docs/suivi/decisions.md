> [English version] · [Français](./decisions.fr.md)

# Decisions

- 28/10/2026: standalone app abandoned (too limited). V1 = phone connected to PC, without root. Root postponed.
- 28/10/2026: PC software for Windows first.
- 28/10/2026: work in three phases (1 configuration, 2 tools + Classinus connection for quick testing, 3 interface).
- 28/10/2026: class-tech becomes a simple MCP tools server, not a full backend. Official Classinus integration later. Workstream B skeleton reduced (see docs/etape-2-decision-architecture.md).
- 28/10/2026: classinus-backend and classinus-frontend remain read-only (the only planned exception is future official integration, to be approved at that time).
- 28/10/2026: docs/suivi/ created, with a permanent update rule (this file + MUSE.md).
- 28/10/2026: phase 2 uses six agents (readiness on main, activation + Render deployment, three builders on outils-80/100/root branches, merger with push + redeployment). GitHub push authorized. The 80% builder merges, pushes, and deploys by itself. Tiers: simple 80%, complete 100% without root, root disabled (disponible=false).
- 28/10/2026: run ADB locally first to validate tools (no extra code), then PC relay for the product. End-to-end ping_serveur test succeeded through Clovis.
- 28/10/2026: root tools must never be executed (live tests). Three-agent security audit after merge (two parallel diagnosis-and-fix agents, one final agent to decide and permanently correct issues).