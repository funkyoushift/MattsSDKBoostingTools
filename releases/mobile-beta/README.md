# MSBT Mobile Controller — Open Beta Release

Open Android beta for **MSBT Mobile Controller**, paired with desktop **Matt's SDK Boosting Tools v2.3.0+** (Mobile Gateway + QR).

Desktop **v2.3.0** is the current GitHub **Latest** Windows release and includes Mobile Gateway.

## What you get

| Piece | What it is |
|-------|------------|
| **Android APK** | MSBT Mobile Controller (`0.1.0-beta.15+`) |
| **Desktop MSBT v2.3.0+** | Electron app with **Mobile Gateway** + **QR pairing** + home APK QR |
| **Test kit** | Checklist, known issues, Discord feedback template |

## Downloads (always current)

**Phone APK (bookmark this):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk

**Desktop installer (Latest — Mobile Gateway):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/v2.3.0/MSBT-Installer-v2.3.0.exe

**Desktop Latest release page:**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest

**Phone open-beta release (APK + test kit):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-beta

## Requirements

- Android 9+ phone (API 28+)
- Same Wi‑Fi as the gaming PC (not cellular-only)
- Desktop MSBT **v2.3.0 or newer** (Check Updates in the app, or install from Latest)
- Borderlands 4 + MSBT SDK mod for live in-game actions
- Windows Firewall: allow Electron/Node on port **49775** if prompted

## 10-minute setup

### 1. Install / update desktop MSBT

1. Download `MSBT-Installer-v2.3.0.exe` from [Latest](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest) (or use **Check Updates** in an older install).
2. Install / update over your existing MSBT (user data is kept).
3. Launch **Matt's SDK Boosting Tools** — you should see a **Mobile App** announcement with an install QR.
4. Start Borderlands 4 with the MSBT SDK mod and get in-world.

### 2. Install the phone app

1. Scan the desktop home QR, or download `MSBT-Mobile-Controller.apk` (link above).
2. Install **over** older mobile betas (same package ID) so bookmarks / connection survive.
3. Confirm **More → About** shows **`0.1.0-beta.15`** or newer.

### 3. Pair with QR (recommended)

1. Desktop: open **Activity → Mobile Gateway**.
2. Leave the **QR code** visible (gateway should show online on port `49775`).
3. Phone: **More → Connection Settings → Scan QR to pair** (allow Camera).
4. Home should show gateway online (and game bridge online while in-world).

Manual fallback: enter PC LAN IP, port `49775`, and the 6-digit pairing code → Save → Connect / Test.

## Feedback

Send feedback + full-screen screenshots to **FunkYouSHiFT** in Discord DMs. Do not post live pairing codes publicly.

See `mobile_controller/test_kit/` for checklist and templates.
