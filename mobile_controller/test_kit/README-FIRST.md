# MSBT Mobile Controller — Closed Beta Test Kit

Welcome. This kit is for **select Discord testers** only. It is separate from the public Windows MSBT installer.

## What you need

| Item | Notes |
|------|--------|
| Android phone | Android 9+ (API 28+). Note make/model + Android version. |
| Same Wi‑Fi as your gaming PC | Phone must not be on cellular-only. |
| Desktop MSBT | Build from the `mobile-controller-prototype` branch with **Mobile Gateway**. |
| Borderlands 4 + MSBT SDK mod | In-world for live actions. |

## Download the app

**Always-current APK (bookmark on your phone):**  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk

Prerelease page:  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-beta

Install **over** previous mobile betas (same package ID) so connection settings / bookmarks / Quick Menu data survive.

## 10-minute setup

1. Install/update the APK from the link above.
2. On PC: start desktop MSBT → launch BL4 with MSBT → get in-world.
3. Desktop: **Activity → Mobile Gateway**. Note **PC address**, port **49775**, **6-digit pairing code**.
4. Phone: **More → Connection Settings** → enter address / `49775` / code → **Save Setup** → **Connect / Test**.
5. Home should show gateway + game bridge online. Pick a Boost target, then try **MAX CASH**.

If Connect fails: desktop MSBT open, Gateway online in Activity, LAN IPv4 (not `127.0.0.1`), same Wi‑Fi, Windows Firewall allowed for the app/port.

## App tabs (beta.7+)

| Tab | What it is |
|-----|------------|
| **Home** | Pairing status, recent result |
| **Boost** | Max / UVH / currency / serials / rarity / cheats |
| **Codes** | Bundled BL4 codes catalog + delivery |
| **QM** | Full F7 Quick Menu (pull from PC) |
| **Control** | Inventory, Bookmarks, Map Travel, Movement, Item Pools |
| **Spawn** | Dev Spawner (experimental — enable session first) |
| **More** | Connection, activity, feedback, about |

## What to do next

1. Work through **`CHECKLIST.md`** (portrait + landscape where noted).
2. Capture **full-screen** screenshots for anything broken or clipped.
3. Send feedback to **FunkYouSHiFT** in Discord DMs using **`FEEDBACK_TEMPLATE.txt`**.

Read **`KNOWN_ISSUES.md`** before filing “bugs” that are already expected.

## Kit contents

- `README-FIRST.md` — this file  
- `CHECKLIST.md` — what to test  
- `FEEDBACK_TEMPLATE.txt` — Discord DM template  
- `KNOWN_ISSUES.md` — expected limits  
- `VERSION.txt` — build label (filled by CI)  
- `DOWNLOAD.txt` — APK URL (filled by CI)  

The APK is published separately (not inside this zip) so updates stay a single bookmarkable link.
