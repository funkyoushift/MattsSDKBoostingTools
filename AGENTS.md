# MSBT Codex Instructions

This project is a Borderlands 4 SDK mod plus a desktop Electron control panel.

**Primary UIs**

- Electron app (`electron_poc/`) — public control panel
- Native in-game Quick Menu (`quick_menu.py`, F7) — no BLImGui required

**Optional fallback**

- BLImGui panel (`blimgui_panel.py`) — keep working; do not delete

**Runtime helpers (not the main UI)**

- `external_app/v22_parts_codes_fixed/` — resources, serial/Matt Editor Python helpers, and legacy Tkinter app layout. Electron still packages this tree. Do not rearrange it unless explicitly asked.

## Goal

Keep BLImGui optional by routing live game actions through `backend_actions.py` so the bridge and Quick Menu do not need the ImGui panel.

## Hard rules

- Do not delete the working BLImGui UI.
- Do not rewrite the entire project at once.
- Do not remove resources casually.
- Do not change the external app layout unless explicitly asked.
- `external_bridge.py` must not import `blimgui` or `blimgui_panel.py`.
- BLImGui is optional fallback only.
- Keep changes small and commit-ready.

## Architecture

- `backend_actions.py` — bridge-safe non-UI action handlers
- `external_bridge.py` — HTTP bridge; calls `backend_actions.py` only
- `quick_menu.py` / `quick_menu_registry.py` — native UMG Quick Menu
- `blimgui_panel.py` — optional UI; may call helpers/`backend_actions`, but must not be required for bridge or Quick Menu
- Electron owns the desktop UI; SDK mod handles live game interaction

Domain helpers (non-UI) include: `player_economy.py`, `serial_rewards.py`, `legit_builder_core.py` (BLImGui path), `travel.py`, `movement_adjustments.py`, `item_pool_spawning.py`, `dev_tools.py`, `party_helpers.py`, `inventory_capacity.py`, `vault_card_boost.py`, `shinies.py`.

See [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md) and [`docs/ELECTRON_ROADMAP.md`](docs/ELECTRON_ROADMAP.md).

## Versioning

Public SemVer is lockstep across Electron (`electron_poc/package.json`), SDK `__version__` / `pyproject.toml`, and `releases/latest.json`. Bump them together for a release. See [`VERSIONING.md`](VERSIONING.md).

## Testing

- Run Python syntax checks after changes.
- Package `.sdkmod` only after import/syntax checks pass.
- Do not claim BLImGui independence until bridge `/status` works with `blimgui.zip` disabled (see `tests/test_quick_menu_no_blimgui.py`).
