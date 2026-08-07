# MSBT Mobile Controller — Closed Beta Release

This branch (`release/mobile-beta`) is the **closed Android + desktop Mobile Gateway** release line for select Discord testers.

It is **not** the public Windows MSBT stable channel (`main` / `v2.2.x` Latest).

## What you get

| Piece | What it is |
|-------|------------|
| **Android APK** | MSBT Mobile Controller (`0.1.0-beta.12+`) |
| **Desktop MSBT (this branch)** | Electron app with **Mobile Gateway** + **QR pairing** |
| **Test kit** | Checklist, known issues, Discord feedback template |

## Downloads (always current)

**Phone APK (bookmark this):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk

**Desktop installer (Mobile Gateway build):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-msbt-closed-beta/MSBT-Installer-mobile-controller-beta.exe

**Release page (APK + desktop + test kit):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-msbt-closed-beta

Also mirrored on the rolling APK tag:  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-beta

## Requirements

- Android 9+ phone (API 28+)
- Same Wi‑Fi as the gaming PC (not cellular-only)
- Desktop MSBT from this closed-beta package / `release/mobile-beta` branch (stock public `v2.2.1` may lack Mobile Gateway / QR)
- Borderlands 4 + MSBT SDK mod for live in-game actions
- Windows Firewall: allow Electron/Node on port **49775** if prompted

## 10-minute setup

### 1. Install desktop MSBT (Mobile Gateway build)

1. Download `MSBT-Installer-mobile-controller-beta.exe` from the release above.
2. Install / update over your existing MSBT (user data is kept).
3. Launch **Matt's SDK Boosting Tools**.
4. Start Borderlands 4 with the MSBT SDK mod and get in-world.

### 2. Install the phone app

1. Download `MSBT-Mobile-Controller.apk` on the phone (link above).
2. Install **over** older mobile betas (same package ID) so bookmarks / connection survive.
3. Confirm **More → About** shows **`0.1.0-beta.12`** or newer.

### 3. Pair with QR (recommended)

1. Desktop: open **Activity → Mobile Gateway**.
2. Leave the **QR code** visible (gateway should show online on port `49775`).
3. Phone: **More → Connection Settings → Scan QR to pair**.
4. Allow **Camera** when prompted; point at the desktop QR.
5. Phone should save settings and connect automatically (badge **ONLINE**).

### 4. Manual pairing (fallback)

1. Desktop: **Activity → Mobile Gateway** — note PC address, port **49775**, 6-digit pairing code.
2. Phone: **More → Connection Settings → Manual setup**.
3. Enter name / address / port / code → **Save Setup** → **Connect / Test**.

## Quick smoke checks

After ONLINE + game bridge online:

1. **Boost** — pick a target → **MAX CASH** (or similar).
2. **Codes** — catalog loads with a large nonzero count.
3. **QM** — **Pull From PC**, tap a filled slot.
4. **Control** — Inventory / Bookmarks / Travel / Movement / Item Pools have a shared **Target**.
5. **Spawn** — check risk → **Enable** → one experimental spawn (optional).

## Feedback

Send Discord DMs to **FunkYouSHiFT** using the template in the test kit zip (`FEEDBACK_TEMPLATE.txt`).

Include:

- Phone make/model + Android version
- MSBT Mobile version (**More → About**)
- Desktop build (Mobile Gateway closed beta)
- Full-screen screenshots
- What you expected vs what happened

**Do not** post live pairing codes in public Discord.

## Source / development

| Branch | Purpose |
|--------|---------|
| `release/mobile-beta` | Closed-beta release docs + packaging pointer (this README) |
| `mobile-controller-prototype` | Active development for mobile + gateway |
| `main` | Public stable Windows MSBT (no merge of mobile beta without approval) |

APK CI: `.github/workflows/mobile-beta-build.yml` on `mobile-controller-prototype` (publishes the rolling `mobile-beta` APK tag).

## Known limits

See `mobile_controller/test_kit/KNOWN_ISSUES.md` in this repo (also inside the test kit zip).

Highlights:

- Dev Spawner is experimental
- Inventory reads work best on listen host
- Quick Menu full two-way sync may still be incomplete
- Not on mobile: Matt Editor, save editing, Legit Builder
