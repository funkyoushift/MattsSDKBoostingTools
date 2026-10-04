# MSBT Codex Instructions

This project is a Borderlands 4 SDK mod plus a desktop Electron control panel.

**Primary UIs**

- Electron app (`electron_poc/`) — public control panel
- Native in-game Quick Menu (`quick_menu.py`, F7) — no BLImGui required

**Runtime helpers (not the main UI)**

- `external_app/v22_parts_codes_fixed/` — resources, serial/Matt Editor Python helpers, and legacy Tkinter app layout. Electron still packages this tree. Do not rearrange it unless explicitly asked.

## Goal

Route live game actions through `backend_actions.py` for Electron, mobile, and the native Quick Menu. The legacy BLImGui panel has been retired.

## Hard rules

- Do not reintroduce the BLImGui panel or a BLImGui runtime dependency.
- Do not rewrite the entire project at once.
- Do not remove resources casually.
- Do not change the external app layout unless explicitly asked.
- `external_bridge.py` must not import `blimgui` or `blimgui_panel.py`.
- Keep changes small and commit-ready.

## Item-card generation: game evidence only

- Reproduce BL4's serial-to-item-card pipeline from the installed game's data and code. Do not invent selection, naming, arithmetic, rounding, formatting, or fallback rules to match screenshots.
- Screenshots are independent regression evidence, not the specification for an algorithm. Passing examples does not prove a recovered native implementation.
- Record the game build, source asset or executable hash, and exact definition/function location supporting each ported behavior. Label extracted data, recovered executable logic, and unresolved behavior separately.
- Generic Unreal source, other games, third-party labels, and observed outputs are research leads, not proof of BL4's implementation.
- Preserve serial case, part order, duplicates, and required item/loadout context. Do not use per-item overrides or silently replace missing values with plausible numbers.
- Audit existing inferred rules; do not extend or describe them as native-proven. Unknown behavior stays explicitly unverified and blocks an exact-parity/release claim.
- Keep extraction read-only against the game installation. Do not launch/restart the game, mutate inventory, or publish a release without the user's applicable authorization.

## Architecture

- `backend_actions.py` — bridge-safe non-UI action handlers
- `external_bridge.py` — HTTP bridge; calls `backend_actions.py` only
- `quick_menu.py` / `quick_menu_registry.py` — native UMG Quick Menu
- Electron owns the desktop UI; SDK mod handles live game interaction

Domain helpers (non-UI) include: `player_economy.py`, `serial_rewards.py`, `legit_builder_core.py`, `travel.py`, `movement_adjustments.py`, `item_pool_spawning.py`, `dev_tools.py`, `party_helpers.py`, `inventory_capacity.py`, `vault_card_boost.py`, `shinies.py`.

See [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md) and [`docs/ELECTRON_ROADMAP.md`](docs/ELECTRON_ROADMAP.md).

## Versioning

Public SemVer is lockstep across Electron (`electron_poc/package.json`), SDK `__version__` / `pyproject.toml`, and `docs/releases/latest.json` (see [`docs/VERSIONING.md`](docs/VERSIONING.md)).

### Hard rule — no release without Matt’s explicit ask

Do **not** bump SemVer, create/update GitHub Releases, upload installer/portable/`.sdkmod`/`latest.json` assets, or tag `vX.Y.Z` unless Matt clearly requests that release in the current message.

- Local builds and branch fixes for smoke-testing are fine; **publishing** is not.
- Phrases like “fix it” or “do it” (about a bug) are **not** release approval.
- If unsure, ask. Leave versions unchanged and say what is ready to ship.

Mirrored for all Cursor agents in [`.cursor/rules/no-release-without-approval.mdc`](.cursor/rules/no-release-without-approval.mdc).

### Hard rule — restart Electron before Matt looks

When you want Matt to look at the desktop panel, **restart it yourself** (`electron_poc` → `npm start` after stopping MSBT Electron only). Do not tell him to restart it. Do not kill Borderlands 4.

Mirrored in [`.cursor/rules/restart-electron-before-matt-looks.mdc`](.cursor/rules/restart-electron-before-matt-looks.mdc).

## Testing

- Run Python syntax checks after changes.
- Package `.sdkmod` only after import/syntax checks pass.
- Run `tools/tests/test_quick_menu_no_blimgui.py` for startup, Quick Menu, and bridge regression checks. Distinguish offline checks from a live bridge `/status` check with `blimgui.zip` disabled.

## Durable project change notes — read first

Before broad codebase research, read `docs/PROJECT_CHANGE_NOTES.md` and the relevant linked change entry. Verify dated findings against the current checkout/install/runtime, then inspect only the gaps.

Every meaningful fix/change must update durable notes covering symptoms, evidenced root cause, files/components changed, exact behavioral change, validation/results, useful failed/rejected approaches, deployment/rollback and unresolved follow-ups. Link entries from the index; separate offline checks, live execution and guest-save proof. Never record passwords/tokens or invent measured credit savings. Keep later validation/deployment status current.

Mirrored for Cursor agents in `.cursor/rules/project-change-notes.mdc`.
