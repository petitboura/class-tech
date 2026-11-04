> [English version] · [Français](./README.fr.md)

# Class-Tech PC Relay

The relay is a small server running on your PC, next to the phone connected over USB. It runs diagnostics locally, where the phone is visible, using the actual Class-Tech tools.

## Step 1: Prepare the phone and PC

On the phone:

- Enable developer mode and USB debugging.
- Connect the phone to the PC with a USB cable.
- Approve the permission request on the phone screen.

On the PC:

- Install Python 3.12 or later.
- Install Google's platform-tools (the ADB program).

## Step 2: Get the relay and install it

- Get the relais-pc branch of the class-tech repository on your PC.
- From the repository root, install the dependencies:

  `python -m pip install -r backend/requirements.txt`

## Step 3: Start and verify

- Double-click `Lancer-Relais.bat` in the relais folder. A window shows the address where the relay is listening.
- Open the health page in a browser, at the address shown in the window, followed by `/relais/sante`.
- Proof: `python relais/verifier_relais.py` displays the real data from the connected phone.

## Settings

Everything is in `relais/reglages.json`: host (listening address), port, `delai_lancement_s` (maximum wait for a response), and `chemin_adb` (empty means automatic discovery; otherwise, the full path to adb). Each value can also be overridden by an environment variable: `RELAIS_PC_HOTE`, `RELAIS_PC_PORT`, `RELAIS_PC_DELAI`, `RELAIS_PC_ADB`. No port, path, or address is hardcoded in the code.

## Troubleshooting

- Phone not detected: change cable or USB port, check USB debugging, and approve the request again on the phone.
- ADB not found: set `chemin_adb` in `relais/reglages.json` to the full path to adb.
- Port busy: change the port in `relais/reglages.json` and restart.
- Relay unreachable: make sure the relay window is still open.

## Sensitive tools and root

The relay runs read operations (including the 10 deep tools without root) and the five sensitive tools (clear caches, speaker, vibration, camera, revoke a permission). These five tools really affect the phone: Classinus asks the user for confirmation before sending them to the relay. All root tools are rejected by design.