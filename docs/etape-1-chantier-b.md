> [English version] · [Français](./etape-1-chantier-b.fr.md)

# Step 1: Workstream B, LLM Pipeline in backend/

Date: 28/10/2026.

## Goal

Bring the LLM pipeline into class-tech/backend/, as a skeleton adapted to the new project (phone diagnostics first, computer diagnostics later). The skeleton follows the classinus-backend architecture (read-only, never modified): question received over HTTP, model loop, tools through an internal MCP server, exposed tool catalog. No secrets, no hardcoded values, and no database for now.

## Checks before starting

- C:\Users\dell\class-tech\backend exists with the structure from workstream A (api/, core/, connexions/, indexers/, migrations/, scripts/, tests/, each with .gitkeep, plus LISEZ-MOI.md). Requirement met.
- C:\Users\dell\class-tech\docs\etape-1-chantier-a.md was read: workstream B brings the code, and workstream C writes the root README.
- The classinus-standards-dev skill and class-tech MUSE.md were read. Rules applied: never guess (uncertainties are listed below instead of being decided unilaterally), no hardcoded values (everything comes from the environment), source repositories are never modified.

## Sources read in classinus-backend (evidence)

Read-only access only. What was reused from each file:

- api/chat.py: POST /api/chat route (envoyer_message function), Pydantic payload, conversion of the Python generator into an SSE stream (data: {...} followed by data: [DONE]) through StreamingResponse. Reused in api/diagnostic.py.
- core/main.py: chat() function, event generator (status, outil_resultat, reponse, confirmation_requise with etat_reprise, meta). Reused in a shorter version in core/diagnostic.py.
- core/boucle_agent.py: loop that calls the model, runs requested tools, and pauses on a sensitive tool. Reused in _boucle().
- core/registre_outils.py: SERVEURS_MCP (entries for name, url_builder, headers_builder, outils_autorises, prefixe_outils), REGISTRE_AFFICHAGE_OUTILS (label, icone, onglet), VERBES_ACTIONS, CATEGORIES_OUTILS, OUTILS_SENSIBLES, outils_de_la_categorie(). Reused in reduced form in core/registre_outils.py.
- core/mcp_tools.py: generic engine (list_tools on each server, conversion to LLM format, call to the correct server during execution). Reused in core/moteur_outils.py.
- core/outils_generation_commun.py: shared FastMCP object (mcp_generation = FastMCP(name=...)). Reused as mcp_diagnostic in core/outils_diagnostic_commun.py.
- core/serveur_mcp_generation.py: pattern of gathering the outils_*.py tool modules through imports. Reused in core/serveur_mcp_diagnostic.py.
- core/outils_minuteurs.py (gerer_minuteur tool): tool pattern (@mcp.tool(), typed parameters, French text returned to the model). Reused for the two example tools.
- core/serveur_mcp_public.py (ping, qui_suis_je tools): health-probe pattern without user data. Reused for verifier_chaine.
- api/outils_registre.py: GET /api/outils/registre route serializing the registry (tools, verbes_actions, prefixes_applis). Reused identically in api/outils_registre.py.
- api/main.py: FastAPI app, include_router for routes, MCP server mounts through app.mount("/mcp/...", mcp.streamable_http_app(...)). Reused in api/main.py.
- core/fournisseurs_llm.py and core/clients_outils_llm.py (role only): model call with tools. Reused in a single-provider, OpenAI-compatible version in core/fournisseur_llm.py.
- requirements.txt: reference versions (mcp==2.0.0). Reused in backend/requirements.txt.

## Files created

All in C:\Users\dell\class-tech\backend (patch: no workstream A file modified, no file modified in classinus-backend):

- requirements.txt: dependencies (fastapi, uvicorn, mcp, httpx, pytest).
- .env.example: all variables read by the skeleton, no secrets. Copy to .env (ignored by git).
- core/configuration.py: only module that reads the environment (get_secret, PORT, timeouts, limits).
- core/registre_outils.py: SERVEURS_MCP (internal diagnostic server), TYPES_APPAREILS (telephone, ordinateur), REGISTRE_AFFICHAGE_OUTILS, VERBES_ACTIONS, CATEGORIES_OUTILS, OUTILS_SENSIBLES (empty), outils_de_la_categorie(). No external dependency.
- core/outils_diagnostic_commun.py: shared FastMCP object.
- core/outils_etat_appareil.py: example tools verifier_chaine (probe) and resumer_symptome (structured record, no diagnosis).
- core/serveur_mcp_diagnostic.py: gathers the tool modules and re-exports mcp_diagnostic.
- core/moteur_outils.py: lists tools from each MCP server and executes a tool on the correct server.
- core/fournisseur_llm.py: OpenAI-compatible model call (address, key, and model from the environment). Clear error if not configured.
- core/diagnostic.py: diagnostiquer(), event generator (statut, outil_resultat, reponse, confirmation_requise, meta, erreur), with resume after confirmation and device filtering.
- api/diagnostic.py: POST /api/diagnostic route using SSE.
- api/outils_registre.py: GET /api/outils/registre route.
- api/main.py: FastAPI app, routes connected, MCP server mounted at /mcp/diagnostic. Launch from backend/: uvicorn api.main:app (port 8000).
- api/__init__.py, core/__init__.py, connexions/__init__.py, tests/__init__.py: Python packages (connexions remains empty for later, as planned in workstream A).
- tests/test_registre_outils.py: registry consistency (servers, categories, complete entries, no displayed double hyphens, known sensitive tools). Runs without external dependencies.

## How the pipeline works

1. The client sends POST /api/diagnostic with the message (and history, record, device, or a continuation).
2. The route calls diagnostiquer(), which lists tools through the MCP engine (the internal server responds at /mcp/diagnostic in the same process).
3. The loop calls the model with the tools, executes each requested tool, returns the results to the model, and repeats until the final response.
4. Each step is emitted as an SSE stream: statut, outil_resultat, reponse, then meta. A sensitive tool triggers confirmation_requise and waits for approval before continuing.
5. The future site reads GET /api/outils/registre to display tools (labels, icons) without hardcoding the list.

## Decisions made and deliberate simplifications

- Names adapted to diagnostics (diagnostiquer, resumer_symptome, fiche_id, appareil) rather than copied from the education project (chat, eleve, conversation). The exact mapping is given above.
- Package imports (from core.x import ...) instead of the source repository's sys.path approach: launch from backend/, cleaner for a new repository.
- One internal MCP server (diagnostic), one example business tool, one category per device: the minimum needed to prove the complete pipeline works.
- LLM provider uses the OpenAI-compatible format, without an SDK: address, key, and model come from the environment; no provider is hardcoded (the choice remains open, see below).
- One-block response (no word-by-word streaming), no memory, no persisted history, no multi-model cascade: these can be reused later from the source if needed.
- OUTILS_SENSIBLES is empty: no destructive tool without Bourama's validation. Confirmation plumbing already exists and awaits the first sensitive tool.
- No translation mechanism for now (reported, as requested when none exists): all text is directly in French.
- Workstream A .gitkeep files remain in place: the instruction prohibited touching workstream A files, even though its documentation expected them to be replaced. To be decided (see below).

## Open points for Bourama (to decide, not guessed)

1. LLM provider: Groq, OpenAI, Claude, Gemini, DeepSeek, or another? The skeleton accepts any OpenAI-compatible service through .env, but the official choice (and key) is missing for a first real diagnosis.
2. Should the .gitkeep files be removed now that code exists, or kept while indexers/, migrations/, and scripts/ are empty?
3. Authentication: confirm whether we remain without accounts (and therefore without user_id) until further notice.
4. Database: confirm whether the skeleton remains stateless (no Supabase) for now.
5. Future site contract: SSE and registry formats were reused from the source; validate them when the site is built.

## Checks performed

- Compilation of all files: python -m compileall across api, core, tests, and connexions, no errors.
- Registry test: python tests/test_registre_outils.py reports OK (7 checks: servers, categories, entries, double hyphens, sensitive tools, filter, devices).
- Full wiring with third-party library stubs (temporary script, deleted after use): routes connected, MCP server mounted, tools registered, paths without LLM (empty message, incomplete continuation, example tools, SSE stream, registry), no double hyphens in displayed text. Reports OK.
- Search for double hyphens in backend: found only in a shell command comment and in the test that forbids them, never in displayed text.
- Actual launch not performed here: dependencies (fastapi, mcp, httpx) are not installed on this machine, and the model requires a key. Planned command: from backend/, pip install -r requirements.txt, then uvicorn api.main:app (port 8000).

## Restrictions respected

- Root README.md: neither created nor modified (workstream C).
- LLM pipeline code: none (workstream B).
- MUSE.md: not modified.
- Workstream A files (LISEZ-MOI.md, .gitkeep, etape-1-chantier-a.md, docs/README.md, .gitignore): not modified.
- classinus-backend: read only (11 files read, see above), no changes.
- No commit or push.

## Next steps

- Workstream C: write the root README.md (repository overview).
- Bourama's answers to the 5 open points, then the first real diagnostic using the selected provider.
- Later: memory, history, accounts, word-by-word streaming, second business tool, then frontend/.