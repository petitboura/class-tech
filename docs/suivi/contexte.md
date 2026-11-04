> [English version] · [Français](./contexte.fr.md)

# Stable Context

## Goal

Class-Tech: use AI to diagnose phones first (Android), then PCs, then expand further. The user describes the problem in their own words; the AI guides the diagnosis, proposes fixes, and nothing runs without approval.

## Repositories (C:\Users\dell)

- `class-tech`: the new repository (GitHub petitboura/class-tech, public). This is where work happens.
- `classinus-backend`, `classinus-frontend`: reference repositories, read-only. They must never be modified unless explicitly decided (future official integration of the diagnostic server would be such an exception).

## Target architecture (decided 28/10/2026)

- The brain stays in Classinus: `demander_outils`, `garder_outils`, memory tools, confirmations, and display. It is already running in production.
- `class-tech/backend` is only an MCP diagnostic tools server, which Classinus calls over HTTP.
- Integration is planned through the official registry (registry entry + SQL migration), not as a custom server (confirmation is required for every call, including reads; verified in code).

## Classinus production, verified facts (do not rely on old comments)

- The tool router is disabled (`ROUTEUR_OUTILS_AUTO_DESACTIVE = True`).
- The frontend still sends `outil_force: []` (the Tools menu was removed).
- Actual flow: initial packet (context + retained tools + memory), then the model selects its tools with `demander_outils` and retains them with `garder_outils` (stored in the database, table `outils_retenus_conversation`).

## Phone tiers (decided, details to refine)

- Standalone phone app: abandoned, too limited.
- Phone connected to a PC (cable + developer mode): V1 approach, no root, no risk.
- Root: later, higher risk.
- Scope: Android first through a PC bridge (Windows first), then PC, then scale.

## Bourama's key rules (details in MUSE.md and the skills)

- Never assume or guess; always ask before acting.
- Follow the request strictly; do not add anything by extrapolation.
- No commit or push without explicit instruction.
- Never hardcode values; never display text containing "--".
- Explain in simple French, without jargon.

## Muse sessions

- Morning session on 28/10 (`01a17fdc...`, interrupted before completion): product framing, connectors, workstreams A/B/C launched (A finished, B and C not delivered).
- Current session (`01a1807a...`): resumed, B and C restarted and delivered, tools-server decision, reduction, tracking created.
- Logs are stored under `.local/share/muse/sessions/YYYY/MM/DD/<id>/`.

## V1 tools plan (approved on the morning of 28/10, previous session)

- Order: 80% without root first (PC + cable), 100% with root later. Standalone app abandoned.
- Interface: regular chatbot, simple language, configurable quick buttons (not hardcoded). LLM through API, never fully automatic, tool calls only. Read access allowed; fixes require approval.
- Counts: simple V1 80% = 12 to 15 tools; complete 80% without root = 25 to 35; 100% with root = 45 to 60.
- Steps: 1) PC-phone connection baseline (detection, basic information), 2) chat + 4 buttons (battery, storage, slowness, crashing apps), 3) V1 tools (battery, storage, apps, system, network, one grouped sensor test), 4) complete 80% tier (individual hardware tests, memory/CPU/RAM, permissions, security, updates), 5) root (deep system inspection and deep fixes with warnings).
- Main risk: stable cable connection, to be validated first on 2 to 3 phones. Privacy: only summarized text is sent to the API.
- Evolution since then: the interface moves to the last phase (phase 3), and the brain stays in Classinus (tools-server decision).
- Open question: were the four buttons approved?