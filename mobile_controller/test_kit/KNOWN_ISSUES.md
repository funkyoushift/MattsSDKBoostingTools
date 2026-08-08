# Known limits (open beta)

**Baseline build:** `0.1.0-beta.15` — current recommended open beta (in-app APK update check, bottom-nav clearance, live pairing + Boost/Codes/QM/Control/Spawn).

Do **not** treat these as surprise bugs unless they regressed.

## Expected

- **Camera for QR** — Scan QR needs Camera permission. Manual pairing still works without it.
- **Desktop build required** — live actions need MSBT from `mobile-controller-prototype` / `release/mobile-beta` with Mobile Gateway (+ QR). Stock public Windows releases may not include the gateway yet.
- **Same Wi‑Fi** — phone cannot reach the PC over cellular. Use LAN IPv4, not `127.0.0.1`.
- **Bridge stays local** — game bridge is `127.0.0.1:49774`. Phone talks to Electron gateway `:49775` only.
- **Dev Spawner is experimental** — can crash the game / affect lobby players. Check **I understand the risk**, then **Enable** each session.
- **Inventory reads** — best on listen host; clients often cannot see full remote inventories.
- **Quick Menu upload** — Pull From PC + tap-to-fire works; full two-way push/conflict resolve may still be incomplete. Offline edits stay on the phone.
- **In-app updates** — need network access to GitHub. First install may ask for “Install unknown apps” permission for this package. Quiet/no banner when offline.
- **Not on mobile (by design)** — Matt Editor, save editing, Legit Builder, deep item construction, desktop installer admin.

## Layout notes (tested on Pixel 10 Pro XL + CSS viewport checks)

- **7-tab bottom nav** scrolls horizontally on narrow widths (&lt; ~360dp) so labels are not clipped off-screen.
- **Codes sticky Delivery** sits above the bottom nav; on very short landscape heights the sticky bar can cover the last list row — scroll the list a bit.
- **QR scan dialog** shrinks the camera preview in landscape; cancel stays reachable.
- **Large punch-hole / cutout phones** rely on `safe-area-inset-*`; if a device ignores insets, the app bar may sit tight under the camera.
- **Ultra-narrow (&lt;320dp)** or split-screen: Control tool grid becomes single-column; some long button labels wrap.

## Fixed before beta.11 (re-open only if still broken)

- Target player missing on Control / QM / Movement / Inventory / Bookmarks / Travel / Item Pools.
- Target selection snapping back after leaving Boost (status poll overwrite).

## Fixed before beta.10 (re-open only if still broken)

- Bookmark **Pull From MSBT** returning empty while desktop has bookmarks (needs current Electron from this branch).
- Codes catalog silent empty load; Modded Select All under-count from ID collisions.
- Control panels that would not open; Send Non-Host clipped.
- Travel / Inventory / Item Pools / Dev Spawner empty shells.
- Dev Spawner Enable doing nothing (`window.confirm` on WebView).
- Quick Menu slot taps failing silently.

## Reporting tips

- Include app version from **More → About** (want `0.1.0-beta.15`+).
- Say whether desktop Gateway showed online.
- Full-screen screenshots beat cropped button shots.
- Never paste live pairing codes in public Discord.
