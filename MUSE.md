> [English version] · [Français](./MUSE.fr.md)

# Permanent Instructions for Muse in This Repository

This file replaces the former Classinus CLAUDE.md files (renamed for Muse).
It applies to the entire class-tech repository: backend/ today, frontend/ later.

## The repository and its workstreams

- class-tech has two parts: backend/ (an MCP diagnostic tools server; the brain remains in Classinus) and frontend/ (the interface, in a later phase).
- The classinus-backend and classinus-frontend source repositories served as references. They are read-only and must never be modified from this repository.
- Step 1 is complete: workstream A (structure), workstream B (skeleton, see docs/etape-1-chantier-b.md), and workstream C (README.md). Step 2 (see docs/etape-2-decision-architecture.md): backend reduced to the tools server only, with no LLM pipeline here.
- The root README.md contains sections marked TO BE FINALIZED against the reduced codebase (see docs/etape-1-chantier-c.md). Rewrite it only after an explicit instruction.
- No commit or push without Bourama's explicit instruction.
- When in doubt, the code is authoritative, not old documents.

## Never use double hyphens ("--") in displayed text

Bourama strongly dislikes double hyphens ("--") used as a substitute for an em dash in any text a user sees. Specifically, never use them in:
- error messages returned by the API;
- text returned by tools to the AI for relay in chat;
- any label, name, or description generated and stored for display;
- later, in the frontend: labels, titles, placeholders, error messages, JSX button text, and any dynamically injected text.

They are fully acceptable in:
- code itself (comments, docstrings);
- intentional Markdown separators such as horizontal rules.

Use a comma, period, parentheses, or rephrase instead.
Check all text intended for display before delivery, without making Bourama repeat this rule.

## All new user-related data must be purged when an account is deleted

Adapted from classinus-backend (issue observed on 12/10/2026: account deletion removed only some data because almost no tables had cascading deletion to the account).

Rule, to apply without Bourama having to repeat it: whenever a table, column, or storage file containing a user's data is created (user_id, owner_id, proprietaire_id, etudiant_id, auteur_id, etc.), in the same delivery:
1. add it to account-deletion cleanup (equivalent to core/purge_compte.py);
2. add it to personal-data export;
3. prefer ON DELETE CASCADE toward auth.users, and never create a foreign key without cascading deletion to an account (it would block deletion);
4. verify the actual database schema, not just the code;
5. if data is intentionally retained (security log), state that in the privacy policy.

No account-linked table may be delivered without passing these checks.

## Frontend rules (inactive until the frontend phase)

Adapted from classinus-frontend. Apply them as soon as frontend/ is built:

- FAQ/AEO baseline: whenever a feature, behavior, or display changes, update the corresponding public documentation in the same change.
- Top layer reserved for the agent (z-index): agent elements stay above everything (fullscreen views, popups, menus). Use one source of truth for these values. No other element may exceed them, and never hardcode the values elsewhere.
- STAGING: the indexing block for the test copy must NEVER go into main or production. Never copy it, merge it, or relax it, and check every merge from staging to main.
- Anchored menus, lists, and bubbles: always use the shared anchoring component, never case-by-case positioning.
- Lists and checkboxes: never use native select or checkbox elements; always use the custom components. Language selection belongs in settings, not in a floating pill.

## Working method

- Never assume or guess. When in doubt, ask Bourama before acting.
- Before adding anything, read the actual code and verify the repository's actual state (it may have changed outside this conversation).
- Follow the explicit request strictly. Do not add anything by extrapolation.
- After every change, verify its real impact on behavior, not just that it compiles.
- Explain in simple language, without unnecessary jargon. Bourama has no coding background.
- Keep docs/suivi/ up to date (status, decisions, context) after every important advance, so work can resume in a new session as though nothing had happened.

## Documentation rules

- Keep all project and component documentation in `docs/`, organized into clear topic folders.
- Only `README.md`, `README.fr.md`, `MUSE.md`, and `MUSE.fr.md` stay at the repository root.
- Do not put guides beside implementation folders such as `backend/`, `frontend/`, or `relais/`.
- The default document is English (`.md`); its French companion is `.fr.md`. Keep the language switch links and both documentation indexes in sync.
- Add every document to both `docs/README.md` and `docs/README.fr.md`.
