> [English version] · [Français](./etape-1-chantier-a.fr.md)

# Step 1: Workstream A, class-tech Repository Structure

Date: 28/10/2026.

## Goal

Create the empty structure of the new class-tech repository, ready to receive the LLM pipeline (workstream B) and then the README (workstream C). Do not code or publish anything.

## Checks before starting

- C:\Users\dell\class-tech exists and contains only .git (fresh, empty clone). Requirement met; workstream started.
- Clone origin: https://github.com/petitboura/class-tech.git (read from .git/config).
- Source repositories reviewed in read-only mode and never modified:
  - C:\Users\dell\classinus-backend: README.md (core/, api/, connexions/, indexers/, migrations/, scripts/, etc. structure), CLAUDE.md (2 rules), .gitignore, requirements.txt.
  - C:\Users\dell\classinus-frontend: README.md (Next.js app/, components/, lib/, etc. structure), CLAUDE.md (6 rules), .gitignore, .env.local.example, package.json.

## Files created

- MUSE.md: merged the two CLAUDE.md files, adapted to class-tech (backend today, frontend rules inactive, workstreams A/B/C, source repositories read-only).
- .gitignore: merged both .gitignore files (Python + Next.js), with frontend paths prefixed by frontend/.
- backend/LISEZ-MOI.md: role of each directory (api/, core/, connexions/, indexers/, migrations/, scripts/, tests/).
- backend/api/.gitkeep, backend/core/.gitkeep, backend/connexions/.gitkeep, backend/indexers/.gitkeep, backend/migrations/.gitkeep, backend/scripts/.gitkeep, backend/tests/.gitkeep: empty directories kept in git.
- frontend/LISEZ-MOI.md: note that this is a later phase; nothing to build yet.
- docs/README.md: documentation baseline (one file per step).
- docs/etape-1-chantier-a.md: this file.

## Decisions made

- Backend structure mirrors classinus-backend (same directory names), without disabled directories or deployment files (Dockerfile, Procfile, railpack): workstream B will bring the code and its deployment setup if needed.
- No __init__.py or code: all backend code belongs to workstream B.
- LISEZ-MOI.md files in subdirectories rather than README.md, to avoid confusing them with the root README.md for workstream C.
- Frontend rules kept in MUSE.md but marked "inactive": they apply when frontend/ is built.
- .gitignore includes .venv/ and .pytest_cache/ in addition to source patterns, for a clean Python environment.

## Restrictions respected

- Root README.md: neither created nor modified (workstream C).
- LLM pipeline code: none (workstream B).
- No commit or push.
- classinus-backend and classinus-frontend sources: read only, no changes.

## Next steps

- Workstream B: bring the LLM pipeline into backend/ (replacing the .gitkeep files).
- Workstream C: write the root README.md.
- Later phase: build frontend/.