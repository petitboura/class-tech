> [English version] · [Français](./OVERVIEW.fr.md)

# The Class-Tech PC Relay

Date: 28/10/2026. Branch: relais-pc.

## The problem

The Class-Tech server runs in the cloud. The cloud cannot see a phone connected by USB to the user's PC. Without a relay, only the PC hosting the server can diagnose a phone.

## The relay's exact role

The relay is a small server running on the user's PC, next to the connected phone. It reuses the repository's existing ADB bridge and tools as they are. It receives diagnostic requests and executes them locally, where the phone is visible.

## Where it runs

On the user's PC, inside the repository directory (relais-pc branch). It is a single program to launch. It listens on a local address, with a port configurable in relais/reglages.json.

## How the connected phone becomes reachable

1. The user connects the phone over USB, with USB debugging enabled, and approves the request on the phone screen.
2. The relay runs on that same PC, so the existing ADB bridge finds the phone over the cable, without changing the tools' code.
3. The requested diagnosis runs locally, and the response is sent back to the requester.

## Diagram

```text
Target product:
[Phone over USB] connected to [Relay on PC] connected to [Classinus Brain]
The relay executes next to the phone. The brain guides the process from the cloud.

What works today:
[Phone over USB] connected to [Relay on PC]
The local diagnostic returns real data from the phone.
```

## What the relay exposes

- The existing MCP tools server at /mcp/diagnostic, for future integration with the brain.
- Two simple routes for local diagnostics: /relais/sante (status and whether a phone is detected) and /relais/outil/name (runs a read-only tool and returns its text).
- Read operations (including the 10 deep tools without root) and the 5 sensitive tools (confirmed first by the user in Classinus). All root tools are rejected by design.

## Deliberate simplifications

- One program, one port, no service to install.
- Port, address, timeout, and ADB path are configurable, never hardcoded.
- No cloud tunnel in this version. Local diagnostics work. The connection to the brain will come later, through an outbound connection from the relay, without opening a port on the PC.

## Known limitations

- The PC must stay on, with the relay running and the phone connected during diagnosis.
- Windows first. The ADB bridge can search on other systems, but only Windows has been tested.
- One phone at a time. If several are connected, the first ready device is used.