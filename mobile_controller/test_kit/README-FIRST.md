# MSBT Mobile Controller — Open Beta Test Kit

**Current recommended build: `0.1.0-beta.15`** (verified working for live pairing + core tabs).

Welcome. This kit is for the **open Android beta**. It is separate from the public Windows MSBT stable installer (`v2.2.x`).

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

Confirm **More → About** shows **`0.1.0-beta.15`** (or newer). Install **over** older mobile betas so local data survives.

Prerelease page:  
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-beta

## 10-minute setup

1. Install/update the APK from the link above.
2. On PC: start desktop MSBT → launch BL4 with MSBT → get in-world.
3. Desktop: **Mobile Gateway tab** — leave the **QR** visible (or note address / `49775` / code for manual).
4. Phone: **More → Connection Settings** → **Scan QR to pair** (allow Camera). Manual entry still works under **Manual setup**.
5. Home should show gateway + game bridge online. Pick a Boost target, then try **MAX CASH**.
6. Optional: **QM → Pull From PC**, then tap a filled slot. **Spawn**: check risk box → Enable → fire a spawn.

If Connect fails: desktop MSBT open, Gateway online in Activity, LAN IPv4 (not `127.0.0.1`), same Wi‑Fi, Windows Firewall allowed for the app/port.

## App tabs

| Tab | What it is |
|-----|------------|
| **Home** | Pairing status, recent result |
| **Boost** | Max / UVH / currency / serials / rarity / cheats |
| **Codes** | Bundled BL4 codes catalog + delivery |
| **QM** | Full F7 Quick Menu (Pull From PC, then tap slots) |
| **Control** | Inventory, Bookmarks, Map Travel, Movement, Item Pools |
| **Spawn** | Dev Spawner (check risk → Enable; experimental) |
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
- `DISCORD_INVITE_BLURB.txt` — paste for inviting testers  
- `VERSION.txt` — build label  
- `DOWNLOAD.txt` — APK URL  

The APK is published separately (not inside this zip) so updates stay a single bookmarkable link.
