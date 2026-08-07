# MSBT Mobile Controller — Open Android Beta

**Recommended build: `0.1.0-beta.15`** — current working open beta.

Open beta layout + **live LAN pairing**. Use desktop **MSBT v2.3.0+** ([Latest](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest)) for Mobile Gateway / QR.

## Tester package

Ship testers:

1. **APK** — always-current link (bookmark on phone):  
   https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk  
   Testers should confirm **More → About** shows **`0.1.0-beta.15`** (or newer).
2. **Test kit zip** — `MSBT-Mobile-Beta-Test-Kit-0.1.0-beta.15.zip` from the same [mobile-beta](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-beta) prerelease.

Kit source lives in `mobile_controller/test_kit/`:

| File | Purpose |
|------|---------|
| `README-FIRST.md` | Setup + tab map |
| `CHECKLIST.md` | What to test |
| `FEEDBACK_TEMPLATE.txt` | Discord DM template |
| `KNOWN_ISSUES.md` | Expected limits |
| `DISCORD_INVITE_BLURB.txt` | Paste for inviting testers |
| `VERSION.txt` / `DOWNLOAD.txt` | Filled by CI |

## Fast path

1. Install/update the APK from the static link.
2. PC: desktop **MSBT v2.3.0+** ([Latest](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest)) + BL4 in-world with MSBT.
3. PC: **Activity → Mobile Gateway** (QR + address / `49775` / pairing code).
4. Phone: **More → Connection Settings** → **Scan QR to pair** (or manual Save → Connect).
5. Try Boost → **MAX CASH**, QM → **Pull From PC** + tap a slot, then work through `CHECKLIST.md`.

## Feedback

Direct Discord DMs to **FunkYouSHiFT** using `FEEDBACK_TEMPLATE.txt`. Full-screen screenshots preferred. Do not post pairing codes publicly.

## Maintainer build

CI: `.github/workflows/mobile-beta-build.yml` on `mobile-controller-prototype` (or **workflow_dispatch**).
