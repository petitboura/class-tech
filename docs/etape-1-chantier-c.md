> [English version] · [Français](./etape-1-chantier-c.fr.md)

# Step 1: Workstream C, class-tech README Showcase

Date: 28/10/2026.

## Goal

Write the root README.md (repository showcase) and the visual briefs, without touching any other file. No commit or push.

## Checks before starting

- C:\Users\dell\class-tech exists (repository present).
- Root README.md: absent (expected, reserved for this workstream, confirmed in docs/etape-1-chantier-a.md).
- Actual repository state reread on 28/10/2026: MUSE.md, .gitignore, backend/LISEZ-MOI.md, frontend/LISEZ-MOI.md, docs/README.md, docs/etape-1-chantier-a.md. No backend code, no requirements.txt, no example environment variables: workstream B had not happened yet (docs/etape-1-chantier-b.md absent).
- classinus-backend read in read-only mode (requirements.txt: FastAPI, uvicorn, supabase, LLM providers). No example environment file found in classinus-backend. Sources not modified.
- classinus-standards-dev skill and MUSE.md were read and applied: do not assume; list uncertainties below instead of deciding them unilaterally.
- Displayed text checked: no "--" in the README (MUSE.md rule).

## Files created

- README.md: title, short description (phone diagnostics first, then PC, using an LLM), prerequisites, quick start, essential variables, production overview, repository structure, contribution, license. Planned visual locations: docs/img/banniere.png, docs/img/schema-demarrage.png, docs/img/schema-architecture.png.
- docs/briefs-images.md: three detailed briefs (content, style, filename) for the banner and two diagrams. The images themselves will be generated in another workstream.
- docs/etape-1-chantier-c.md: this file.

## Decisions made

- Technical sections (prerequisites, quick start, variables, production) written as drafts marked "TO BE FINALIZED after workstream B", inspired by classinus-backend but without claiming anything: there was no code to verify in class-tech yet, and the code is authoritative when in doubt.
- Structure section contains 7 lines, marked "TO BE FINALIZED after workstreams A and B", as a draft based on the empty structure verified in workstream A.
- README written in simple French, consistent with the rest of the repository.

## Open questions (for Bourama to decide, not assumed)

1. README commands, versions, and variable names: must be checked against the actual code after workstream B is delivered.
2. Repository license: none has been chosen; pending Bourama's decision.
3. Architecture diagram: the draft assumes FastAPI plus Supabase plus LLM (borrowed from classinus-backend). If workstream B chooses something else, revise the brief before generating the image.

## Restrictions respected

- No other file touched. No commit or push.

## Next steps

- Workstream B: bring the AI pipeline into backend/.
- After workstream B: finalize README sections marked ⏳ against the reduced code, then generate the images.
- Another workstream: generate the three images in docs/img/ following docs/briefs-images.md.
- Bourama: choose the license.