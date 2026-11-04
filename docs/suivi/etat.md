> [English version] · [Français](./etat.fr.md)

# Status as of the Evening of 28/10/2026

## Phases (3, decided by Bourama)

1. Configuration: COMPLETE (structure, skeleton then reduction to a tools server, README, architecture decision).
2. Build tools + connect them to Classinus: IN PROGRESS (readiness OK. Probe activation by me: registry + migration + SQL + push completed; Render service creation and testing remain. Builders for 80, 100, and root finished and merged into main (50 tools, branches deleted, Render redeployed). Root security audit launched (two parallel agents, then one final agent: diagnose + fix, NEVER run root tools live).
   Render live (17 tools listed). End-to-end ping test succeeded through Clovis. Decision: validate locally first, then PC relay.
   Local 80% validation OK on a real phone (Samsung SM-A055F, Android 13: real detection + battery data). Remaining: validate 100% after merge, then design PC relay.
   Public live tracking site + comments (optional name, no login) live and verified at 08:36; three test rows must be deleted from the Supabase dashboard (table suivi_commentaires).
   PC relay completed and verified at 10:55 (relais-pc branch, main unchanged): health + real battery data through relay; no cloud tunnel; merge into main after final audit.
   B16 fixed at 11:12 and verified on phone at 11:23 (8 MT6768 cores, targeted test + 202 passing); pushed. Relay installer completed at 15:46 (one-click executable + automatic ADB, tested with real data) and verified by me at 16:01 (rebuild + real test); relais-pc and relais-install merged into main and pushed. B17 closed (observed at 19:15). PC version investigation completed at 19:33 (A21): one-click Electron, automatic updates, proposed embedded relay or second button, pending decision.
   D29: five sensitive tools confirmed, four tested live at 19:35 (beep, vibration, photo: awaiting Bourama's observations; B18 suspected camera listing issue); removal pending target OK. D30: relay integrated into Classinus PC, cable first. D34: ten deep tools first (A24 network failure, work recovered and finished directly), sixteen later. D35: iOS (A25 network failure, to restart).
3. Build the interface: later.

## What is in place (verified on disk)

- `backend/`: MCP tools server only. `api/main.py` mounts `/mcp/diagnostic` (`uvicorn api.main:app` from backend/). Two example tools: probe `verifier_chaine` and `resumer_symptome`. Registry reduced to metadata, adapted test passes, `LISEZ-MOI.md` updated, MUSE.md updated.
- `docs/`: workstream 1 records (A, B, C), step 2 decision, and this tracking directory.
- `README.md`: showcase draft written; briefs for the three images are ready.

## Known remaining items (not forgotten)

- README: sections marked TO BE FINALIZED against the reduced code; license to be chosen by Bourama; architecture diagram brief needs adjustment (no Supabase for now).
- Three small approximate texts (`api/__init__.py`, `core/__init__.py`, server docstring: words "pipeline", "same process").
- A real uvicorn launch has never been performed (dependencies not installed).

## Waiting for Bourama

- Tiers decided: simple 80% (12 to 15 tools), complete 100% without root (25 to 35 total), root (45 to 60 total). Starter buttons postponed to phase 3 (D17, 20:03): the user goes through the LLM.
- Validate the 100% tier locally after merge (phone connected, same procedure as the 80% tier).
- Label decided at 20:03: keep "Détecter le phone".
- First phone tool categories to build.
- Choose the license.