> [English version] · [Français](./README.fr.md)

# Project Tracking (Memory Between Sessions)

This directory is the project's memory. Everything important goes here, so work can resume in a new session as though nothing had happened.

## Files

- `contexte.md`: stable facts (goal, repositories, architecture, key rules).
- `etat.md`: current status, what is complete, what is in progress, and what is waiting for Bourama. Read this file first.
- `decisions.md`: decisions made, with their dates.
- `journal.md`: strict log (active, cancelled, or pending decisions with reasons; every agent with its purpose and outcome).
- `bilan.md`: Bourama's review (goal, mistakes, decisions, delegations, role), kept up to date at every phase.
- The `etape-*.md` documents at the root of `docs/` remain detailed records of each step and must not be rewritten.

## Protocol (also required by MUSE.md)

- At the start of a session: read `etat.md`, then `decisions.md` (and `contexte.md` if needed) before acting.
- After every important advance: update `etat.md` immediately, and update `decisions.md` if a decision was made.
- Never let `etat.md` contradict the repository: when in doubt, reread the actual code before writing.