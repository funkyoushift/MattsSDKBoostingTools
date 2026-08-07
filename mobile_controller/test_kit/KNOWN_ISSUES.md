# Known limits (closed beta)

**Baseline build:** `0.1.0-beta.12` — current recommended closed beta (live pairing + Boost/Codes/QM/Control/Spawn verified).

Do **not** treat these as surprise bugs unless they regressed.

## Expected

- **Camera for QR** — Scan QR needs Camera permission. Manual pairing still works without it.
- **Desktop build required** — live actions need MSBT from `mobile-controller-prototype` with Mobile Gateway (+ QR). Stock public Windows releases may not include the gateway yet.
- **Same Wi‑Fi** — phone cannot reach the PC over cellular. Use LAN IPv4, not `127.0.0.1`.
- **Bridge stays local** — game bridge is `127.0.0.1:49774`. Phone talks to Electron gateway `:49775` only.
- **Dev Spawner is experimental** — can crash the game / affect lobby players. Check **I understand the risk**, then **Enable** each session.
- **Inventory reads** — best on listen host; clients often cannot see full remote inventories.
- **Quick Menu upload** — Pull From PC + tap-to-fire works; full two-way push/conflict resolve may still be incomplete. Offline edits stay on the phone.
- **Not on mobile (by design)** — Matt Editor, save editing, Legit Builder, deep item construction, desktop installer admin.

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

- Include app version from **More → About** (want `0.1.0-beta.12`+).
- Say whether desktop Gateway showed online.
- Full-screen screenshots beat cropped button shots.
- Never paste live pairing codes in public Discord.
