# MSBT Mobile Controller — Closed Android Beta

Closed layout + **live LAN pairing** beta for MSBT Mobile Controller. Separate from the Windows MSBT installer.

## Fast path (select beta)

**Phone install / update (bookmark this):**
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk

1. Open that link on your Android phone and install/update the APK.
2. On the PC: run desktop MSBT from this branch (with **Mobile Gateway**), launch Borderlands 4 with the MSBT SDK mod, get in-world.
3. In desktop MSBT open **Activity → Mobile Gateway**. Note **PC address**, port **49775**, and the **6-digit pairing code**.
4. Phone and PC on the **same Wi‑Fi**. Allow Windows Firewall for the app/port if prompted.
5. On the phone: **More → Connection Settings** → enter address / `49775` / pairing code → **Save Setup** → **Connect / Test**.
6. Home should show gateway/bridge online. Try one live action (e.g. Boost → **MAX CASH**).

If Connect fails: confirm desktop MSBT is open, the Activity tab shows Gateway online, you used the LAN IPv4 (not `127.0.0.1`), and the phone is not on cellular-only data.

## What testers receive

- `MSBT-Mobile-Controller-0.1.0-beta.7.apk` — Android app.
- `MSBT-Mobile-Beta-Test-Kit-0.1.0-beta.7.zip` — this guide/checklist.

Do **not** package the APK inside the Windows MSBT installer.

Desktop note: live phone actions need a desktop MSBT build that includes the **Mobile Gateway** (this `mobile-controller-prototype` branch). The SDK bridge itself stays bound to `127.0.0.1`; Electron proxies LAN requests.

## Before installing

1. Confirm your phone make and model in Discord.
2. Note your Android version: **Settings → About phone → Android version**.
3. Keep your current desktop MSBT installation; for live pairing use a build from this branch.

## Install the APK

1. On your phone, open the static beta link:
   https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk
2. Android may ask permission for your browser to install unknown apps. Allow it.
3. Install/update **MSBT Mobile Controller** (same package ID as prior betas — local data should survive).
4. Open it and confirm the Home screen loads without crashing.

If Android refuses to install an update over an older mobile beta, report the exact message before uninstalling anything.

## Pair phone ↔ PC (live actions)

1. PC: desktop MSBT running + Borderlands 4 in-world with MSBT loaded.
2. PC: **Activity → Mobile Gateway** → copy address / port / pairing code (**Copy Pairing Details**).
3. Phone: **More → Connection Settings** → paste values → **Save Setup** → **Connect / Test**.
4. Badge should move to **ONLINE**. Boost / serial send / rarity / movement Apply become enabled.
5. Pick a target player when the party list loads, then fire one action.

**Disconnect** keeps the saved setup on the phone.

## What to test first

Test both **portrait** and **landscape** where it makes sense.

### 1. Home / navigation

- Home, Boost, Codes, Control, and More tabs are visible.
- Text is readable and not clipped.
- Bottom navigation is reachable above Android gesture controls.
- Rotate the phone and confirm the layout remains usable.

Take a full-screen screenshot in portrait.

### 2. BL4 Codes

- Bundled catalog loads with a **nonzero** count (expect roughly thousands total: GZO + Lootlemon + MSBT).
- Status line shows Total · GZO · Lootlemon · MSBT counts (or an explicit `Bundled catalog unavailable: …` error — never silent zero).
- Search / filters / multi-select / Select All Filtered / Clear Selection work.
- With Wi‑Fi off, relaunch and confirm the bundled catalog still loads.
- Item images that are available online display; missing images should not break the list.

### 3. Boost (live when paired)

- Target player dropdown populates after Connect while in-game.
- Quick Max / currency / XP / serial send / rarity buttons fire through the gateway.
- Offline (not connected): live buttons stay disabled or clearly refuse to send.

### 4. Serial Bookmarks / Quick Menu / Movement

- Bookmarks and movement presets persist offline.
- Quick Menu offline edits persist; sync conflict dialog remains for later full PC sync.
- Movement **Apply to Target** works when paired.

### 5. Connection Setup

- Save address / port / pairing code; reopen app and confirm it remains.
- **Connect / Test** reaches the PC gateway.
- Wrong pairing code fails clearly without wiping the saved setup.

## Screenshots we need

Please send **full-screen** screenshots rather than cropping to one button whenever possible.

1. Home — connected (or clear offline state)
2. Connection Settings with saved PC
3. Boost after a successful live action (or the error if it failed)
4. BL4 Codes — multi-select
5. Quick Menu — portrait
6. Any broken/clipped screen

## How to give useful feedback

For this closed beta, send feedback **directly to FunkYouSHiFT in Discord DMs**.

```text
MSBT MOBILE BETA FEEDBACK

Phone make/model:
Android version:
MSBT Mobile version: 0.1.0-beta.7
Desktop MSBT version (if connected):

Screen/feature:
What I expected:
What happened:
Steps to reproduce:
Does it happen every time? Yes / No / Sometimes

Screenshots attached: Yes / No
Anything else:
```

## Known beta limitations

- Travel / Dev Spawner / Item Pool / inventory browsers are shells — pairing + Boost/serial/rarity/movement Apply are the live focus.
- Quick Menu full PC sync upload is not finished; offline edits are kept safely on the phone.
- Matt Editor, save editing, Legit Builder are intentionally not on mobile.
- Phone and PC must share a LAN/Wi‑Fi path; the game bridge is never exposed directly to the network.
- Expect rough edges; screenshots help.

## Build / install (maintainers)

GitHub Actions: `.github/workflows/mobile-beta-build.yml` on `mobile-controller-prototype` (or **workflow_dispatch**).

Artifacts:

- `MSBT-Mobile-Controller-0.1.0-beta.7.apk`
- `MSBT-Mobile-Beta-Test-Kit-0.1.0-beta.7.zip`

Local APK (optional):

```bash
# decode keystore once if needed
base64 -d mobile_controller/debug-signing/msbt-mobile-debug.keystore.b64 > mobile_controller/debug-signing/msbt-mobile-debug.keystore
gradle -p mobile_controller :app:assembleDebug
```

Desktop gateway for local testing: run Electron from `electron_poc` on this branch; Activity → Mobile Gateway.
