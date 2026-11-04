> [English version] · [Français](./README.fr.md)

# backend/: MCP Diagnostic Tools Server (Step 2, 80%, 100%, and Root Tiers)

There is no longer an LLM pipeline in this directory: the brain (model, tool loop, confirmations, and display) lives in Classinus, which calls this server over HTTP MCP. This directory contains only the diagnostic tools and their server (see docs/etape-2-decision-architecture.md).

Role of each file and directory:

- api/main.py: minimal FastAPI app, mounts the MCP server at /mcp/diagnostic (with explicit session-manager startup).
- core/serveur_mcp_diagnostic.py: gathers the tool modules on the shared mcp_diagnostic object.
- core/outils_diagnostic_commun.py: FastMCP object shared by all tools.
- core/outils_etat_appareil.py: example skeleton tools (health probe and symptom summary).
- core/outils_sonde.py: ping_serveur test probe (returns ok, version, and time).
- core/pont_adb.py: PC-to-phone bridge through ADB (ADB discovery, devices, execution, standard messages). No tools here, only shared transport.
- core/outils_telephone_base.py: detects the connected phone (model, Android version).
- core/outils_telephone_batterie.py: battery status and per-app consumption.
- core/outils_telephone_stockage.py: disk space, large files, cache clearing (sensitive).
- core/outils_telephone_applis.py: app list, recent crashes, unused apps.
- core/outils_telephone_systeme.py: Android version and recent errors.
- core/outils_telephone_reseau.py: network status and Wi-Fi details.
- core/outils_telephone_capteurs.py: grouped sensor test.
- core/pont_root.py: shared root transport (su commands, root check, marks the tool as untested).
- core/outils_root_acces.py: root check, su information, and modules.
- core/outils_root_systeme.py: protected system files, errors, and kernel panics.
- core/outils_root_partitions.py: partitions, mounts, and system integrity.
- core/outils_root_batterie.py: raw battery data, temperatures, and battery-stat resets.
- core/outils_root_firmware.py: firmware, bootloader, and A/B boot slot.
- core/outils_root_processus.py: resource-intensive processes and wake locks.
- core/outils_root_corrections.py: deep fixes (crashes, Dalvik, trim, reboot).
- core/registre_outils.py: tool metadata (names, French labels, icons, tabs, categories, sensitive tools). No external dependency.
- connexions/: empty; will host external connections if a tool needs one in the future.
- indexers/, migrations/, scripts/: reserved directories, empty for now.
- tests/: tests (registry and ADB bridge without external dependencies, the rest with dependencies installed).
- requirements.txt: only the required dependencies.

Root tier: 19 root tools (all sensitive, confirmation required), not tested on a rooted device (none available); every response says so.

Local launch (from backend/):

    uvicorn api.main:app --port 8000

Tests (from backend/, dependencies installed):

    pytest tests

To add a tool: follow the instructions at the top of core/registre_outils.py.