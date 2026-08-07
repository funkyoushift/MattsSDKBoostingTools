# Known limits (closed beta)

Do **not** treat these as surprise bugs unless they regressed.

## Expected

- **Desktop build required** — live actions need MSBT from `mobile-controller-prototype` with Mobile Gateway. Stock public Windows releases may not include the gateway yet.
- **Same Wi‑Fi** — phone cannot reach the PC over cellular. Use LAN IPv4, not `127.0.0.1`.
- **Bridge stays local** — game bridge is `127.0.0.1:49774`. Phone talks to Electron gateway `:49775` only.
- **Dev Spawner is experimental** — can crash the game / affect lobby players. Enable per session on purpose.
- **Inventory reads** — best on listen host; clients often cannot see full remote inventories.
- **Quick Menu upload** — Pull From PC works; full two-way push/conflict resolve may still be incomplete. Offline edits are kept on the phone.
- **Not on mobile (by design)** — Matt Editor, save editing, Legit Builder, deep item construction, desktop installer admin.

## Already fixed in recent betas (re-open only if still broken)

- Bookmark **Pull From MSBT** returning 0 while desktop has bookmarks (desktop gateway unwrap bug — needs current Electron from this branch).
- Codes catalog silent empty load; Modded Select All under-count from ID collisions.
- Control panels that would not open; Send Non-Host clipped.
- Travel / Inventory / Item Pools / Dev Spawner as empty shells (wired in beta.6–7).

## Reporting tips

- Include app version from **More → About**.
- Say whether desktop Gateway showed online.
- Full-screen screenshots beat cropped button shots.
- Never paste live pairing codes in public Discord.
