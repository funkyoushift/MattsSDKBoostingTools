\# MSBT Codex Instructions



This project contains a Borderlands 4 SDK mod and an external Python control panel.



Goal:

Make BLImGui optional by moving backend/game-action logic out of blimgui\_panel.py.



Hard rules:

\- Do not delete the working BLImGui UI.

\- Do not rewrite the entire project at once.

\- Do not remove resources.

\- Do not change the external app layout unless explicitly asked.

\- external\_bridge.py must eventually avoid importing blimgui or blimgui\_panel.py.

\- BLImGui should become optional fallback only.

\- Keep changes small and commit-ready.



Important architecture:

\- blimgui\_panel.py currently mixes UI, state, and backend action wrappers.

\- Existing non-UI modules may include:

&#x20; player\_economy.py

&#x20; serial\_rewards.py

&#x20; legit\_builder\_core.py

&#x20; travel.py

&#x20; movement\_adjustments.py

&#x20; item\_pool\_spawning.py

&#x20; dev\_tools.py

&#x20; party\_helpers.py



Desired architecture:

\- backend\_actions.py contains bridge-safe non-UI action handlers.

\- external\_bridge.py calls backend\_actions.py.

\- blimgui\_panel.py may call backend\_actions.py but should not be required for the bridge.

\- External app owns static resources and UI.

\- SDK mod only handles live game interaction.



Testing:

\- Run Python syntax checks after changes.

\- Package .sdkmod only after import/syntax checks pass.

\- Do not claim BLImGui independence until bridge /status works with blimgui.zip disabled.

## Cursor Cloud specific instructions

This is a Windows-targeted project (an Electron desktop control panel plus a Borderlands 4 SDK mod). On the Linux cloud VM you can fully run the **Electron app** and the **Python syntax/test checks**. The **SDK mod**, **live bridge/game actions**, and the **Windows installer/`.sdkmod` packaging** (`build_*.ps1`) require the actual game / Windows and cannot be exercised here.

Dependencies are refreshed by the startup update script (`npm install` in `electron_poc/` + `pytest`); do not re-run those by hand.

### Run the Electron app (primary product)
- Launch on the pre-existing VNC desktop (`DISPLAY=:1`) so it is visible to screen tools, with the Chromium sandbox disabled:
  `DISPLAY=:1 MSBT_PYTHON=/usr/bin/python3 npx electron . --no-sandbox` (run from `electron_poc/`).
- **`MSBT_PYTHON=/usr/bin/python3` is required in dev mode.** The app's Python helper resolver (`pythonCandidates()` in `main.js`) otherwise tries a Windows venv path, then `python`, then `py` — none of which exist on this VM (only `python3`), so Serial Tools / Matt Editor / validator helpers fail with `spawn python ENOENT`. Setting `MSBT_PYTHON` (tried first) fixes it without any system change. (An alternative is a `python -> python3` symlink, but the env var is preferred.)
- The `dbus`/`viz GPU process` errors in the log are harmless in a headless VM.
- Local features work fully offline (no game needed): Serial Tools convert/parts breakdown, BL4 Codes catalog search/details, validation, bookmarks, item-pool/travel browsers. Anything that hits the SDK bridge (`http://127.0.0.1:49774` — Boosting deliver, Dev Spawner spawn, Map Travel, `Refresh Status`) needs BL4 + the SDK mod and will just show "no players / bridge offline" here.

### Electron checks
- `npm run check` — JS syntax check of all app entry files.
- `npm run smoke` — headless startup smoke; needs a display, so run `xvfb-run -a npm run smoke` (or set `DISPLAY=:1`). Prints a JSON status line and exits 0.

### Python checks
- Repo's documented validation is syntax/import checks: `python3 -m compileall mod_extracted/MattsSDKBoostingTools external_app/v22_parts_codes_fixed tests tools`.
- The pytest suite is **order-dependent and shares `sys.modules`/registry state across files** (not hermetic). `python3 -m pytest tests/` currently reports ~28 passed / 5 failed, and running a single test file in isolation can fail differently — these are pre-existing test-isolation artifacts, not environment breakage. Several files rely on `tests/test_quick_menu_no_blimgui.py` installing shared Unreal/`mods_base` stubs first, and `test_bridge_queue_preserve_serial.py` vs `test_quick_menu_registry.py` conflict over shared state, so there is no single invocation that turns the whole suite green without editing test code. Treat `compileall` + the targeted files that pass as the reliable signal.

