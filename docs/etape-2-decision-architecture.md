> [English version] · [Français](./etape-2-decision-architecture.fr.md)

# Step 2: Architecture Decision, class-tech Becomes a Tools Server

Date: 28/10/2026. Decided by Bourama (3 answers from 28/10).

## Decisions

1. No more full backend in class-tech: no duplicated LLM pipeline (engine, loop, diagnostic routes). The brain stays in Classinus, which is already running in production.
2. class-tech contains only our diagnostic tools and their MCP server. Classinus will call it like any other tools server; `demander_outils` will discover them and `garder_outils` will retain them.
3. Official registry integration later (registry entry + SQL migration in classinus-backend, the normal tool-addition workflow), not as a custom server (confirmation required on every call, even reads, verified in code).
4. The workstream B skeleton is reduced to the tools server only (this step). The structure (A), rules (MUSE.md), and README (C) remain valid.

## Target architecture

```
Classinus (brain: disabled router, demander_outils, garder_outils,
memory tools, confirmations, display)
   | calls over HTTP MCP
class-tech/backend (MCP tools server: diagnostic tools + server)
```

## Fate of the workstream B files

- DELETE: core/moteur_outils.py, core/fournisseur_llm.py,
  core/diagnostic.py, api/diagnostic.py, api/outils_registre.py.
- REDUCE: api/main.py (minimal app mounting /mcp/diagnostic,
  `uvicorn api.main:app` remains the command), core/registre_outils.py
  (metadata only: names, labels, icons, tabs, categories, sensitive tools + outils_de_la_categorie), adapted tests,
  backend/LISEZ-MOI.md (actual roles).
- DELETE IF UNUSED: core/configuration.py, .env.example (if nothing references them anymore; otherwise reduce to what is strictly needed).
- KEEP: tools (core/outils_*.py), server (serveur_mcp_diagnostic.py),
  requirements.txt (only required dependencies), docs/etape-1-*.md
  (historical records, never rewrite), MUSE.md (updated separately).

## Restrictions for this step

- Do not touch classinus-backend or classinus-frontend (official integration will come later, once real tools exist).
- No commit or push.

## Next steps

- Update MUSE.md (backend = MCP tools server, no longer an LLM pipeline).
- Finalize the README sections marked TO BE FINALIZED against the reduced code, then generate the images.
- Build the real diagnostic tools (phone first).
- Once they exist: official Classinus integration (registry + migration).