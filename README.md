> [English version] · [Français](./README.fr.md)

# Class-Tech

Intelligent technical diagnostics, starting with phones and then expanding to PCs, powered by an AI model (LLM).

![Class-Tech banner](docs/img/banniere.png)

Class-Tech helps users understand what is wrong with a device: users describe the problem in their own words, and the AI guides them through the diagnosis step by step. The project starts with phones and will later expand to PCs.

> Note: this repository is under construction. The AI pipeline (the `backend/` directory) is planned for workstream B, and the interface (the `frontend/` directory) will come in a later phase.

## Prerequisites

> ⏳ TO BE FINALIZED after workstream B (draft below, to be checked against the actual code).

Draft, inspired by the classinus-backend source repository:

- A recent version of Python with `pip`
- An API key for at least one AI model provider
- A Supabase database (project URL and key)

## Quick start

> ⏳ TO BE FINALIZED after workstream B (draft below, to be checked against the actual code).

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Then open the interactive API documentation in your browser.

![Startup diagram](docs/img/schema-demarrage.png)

## Essential environment variables

> ⏳ TO BE FINALIZED after workstream B (draft below, to be checked against the actual code).

| Variable | Purpose |
| --- | --- |
| AI model API key | Allows the backend to call the model |
| Supabase project URL | Database address |
| Supabase key | Database access |

The exact names will be confirmed once the workstream B code is in place.

## Production at a glance

> ⏳ TO BE FINALIZED after workstream B.

Planned approach: the same backend runs in production with production keys, behind HTTPS. Deployment details (platform and commands) will be documented here once workstream B provides its deployment method, if applicable.

![Architecture diagram](docs/img/schema-architecture.png)

## Repository structure

> ⏳ TO BE FINALIZED after workstreams A and B. Draft based on the empty structure verified on 28/10/2026:

```text
class-tech/
├── backend/      AI pipeline: api/, core/, connexions/, indexers/, migrations/, scripts/, tests/
├── frontend/     interface (later phase, empty for now)
├── docs/         one file per project step, plus visuals in docs/img/
├── MUSE.md       working rules for this repository
└── README.md     this file
```

## Contributing

The project is new, and contribution rules have not yet been written. For now: read `MUSE.md` before making any change, touch only what has been requested, and never guess when in doubt.

## License

⏳ To be specified by Bourama: no license has been chosen for this repository yet.