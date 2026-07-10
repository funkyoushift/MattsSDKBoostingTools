# Matt Editor Embedded Path Test Report

## Scope

This pass verifies and hardens the hosted Mattmab item editor path inside the MSBT external app. It does not change SDK bridge behavior, Dev Spawner, BL4 Codes, Movement, or the classic Python Legit Builder logic.

## Launch Path

The standalone app launches the editor from the Legit Builder tab through the `Advanced Mattmab Item Editor` section.

Button:

- `Open Advanced Mattmab Item Editor`

Code path:

1. `matts_external_app_v22.py` calls `matt_editor_host.open_editor_embedded()`.
2. `matt_editor_host.py` starts a local HTTP server on `127.0.0.1` with an ephemeral port.
3. The app tries to open a pywebview window when pywebview is available.
4. If pywebview is unavailable or WebView launch fails, the editor opens in the user's browser.

## Local Host Behavior

`matt_editor_host.py` serves:

- `/` and `/index.html` from `matt_editor/index.html`
- static Matt editor files from `matt_editor/`
- `/matt_editor_adapter.js` from the external app folder
- `/api.php` for local serial serialize/deserialize calls through `external_serial_tools`
- `/LegitItems/nexus_data_proxy.php` for local Matt editor resources
- `/msbt/status` for bridge status forwarding
- `/msbt/target` for forwarding target selection to the existing bridge `set_target_player` action
- `/msbt/deliver` for final serial delivery

The HTML response injects MSBT bootstrap settings and loads `matt_editor_adapter.js` before `</body>`.

## Delivery Boundary

The browser/editor never talks to game SDK modules directly.

Delivery remains:

1. Matt editor builds or displays an item serial locally.
2. `matt_editor_adapter.js` detects possible `@U` outputs.
3. The user confirms one serial in the MSBT delivery panel.
4. The user refreshes/selects the target player in the MSBT delivery panel.
5. Target selection posts to `/msbt/target`, which updates the existing MSBT bridge target state.
6. The adapter posts to `/msbt/deliver`.
7. The local host maps delivery modes to the existing bridge actions:
   - `selected` -> `give_serial_selected`
   - `all` -> `give_serial_all`
   - `nonhost` -> `give_serial_nonhost`
8. The SDK bridge delivers through the existing live-game path.

## Serial To Send Hardening

The adapter now separates detected serials from confirmed serials.

Behavior:

- Delivery buttons are disabled until one serial is explicitly confirmed.
- `Refresh Detected Serial` scans known editor output fields.
- If one serial is detected, it is staged as pending and must be confirmed.
- If multiple serials are detected, the user must choose one and then confirm it.
- `Confirm Serial to Send` makes the pending serial the only sendable serial.
- `Copy Serial` copies only the confirmed serial.
- Editor input/change events mark the confirmed serial stale.
- Stale serials cannot be delivered until refreshed and confirmed again.
- `/msbt/deliver` also rejects missing, multiline, non-`@U`, or ambiguous serial values.

## Target Selection

The injected delivery panel now includes a target picker so `Send to Selected Player` is explicit.

Behavior:

- `Refresh` calls `/msbt/status` and displays bridge connection state, player count, and current bridge-selected target.
- The target dropdown is populated from the bridge `players` list.
- Choosing a player posts to `/msbt/target`.
- `/msbt/target` forwards to the existing bridge action `set_target_player`; it does not create a separate editor-only target state.
- `Send to Selected Player` stays disabled until both conditions are true:
  - one confirmed serial is ready
  - one target player is selected
- `Send to All Players` and `Send to Non-Host Players` still require a confirmed serial, but do not require a selected target.
- `/msbt/deliver` re-applies the selected target before selected-player delivery so the bridge target stays synchronized.

## Package Requirements

The package/build scripts already include the editor requirements:

- `requirements-external-build.txt` includes `pywebview`.
- `build_external_exe.ps1` collects pywebview and copies:
  - `matt_editor/`
  - `matt_editor_adapter.js`
  - `resources/`
- `package_external_beta.ps1` copies the built exe folder and then refreshes:
  - `resources/`
  - `matt_editor/`
  - `matt_editor_adapter.js`

This keeps the editor assets beside the exe, not hidden in a temp-only bundle.

## Automated Checks Run

Passed:

- Python compile check for:
  - `external_app/v22_parts_codes_fixed/matt_editor_host.py`
  - `external_app/v22_parts_codes_fixed/matts_external_app_v22.py`
  - `external_app/v22_parts_codes_fixed/matts_external_core_v20.py`
- Node syntax check for:
  - `external_app/v22_parts_codes_fixed/matt_editor_adapter.js`
- Local host smoke test:
  - host started
  - index page served
  - adapter injection found
  - adapter version `deliver-4-target-selector` served
- Local `/msbt/deliver` guard smoke test:
  - empty serial rejected
  - multiline/multiple serial input rejected
  - non-`@U` serial rejected
- Local target-selector smoke test with a fake bridge:
  - `/msbt/target` forwarded to `set_target_player`
  - selected-player `/msbt/deliver` re-applied the target before delivery
  - selected-player `/msbt/deliver` without a target was rejected

## Manual Test Checklist

Not run in this pass. Martin should test:

1. Launch source or packaged external app.
2. Open `Advanced Mattmab Item Editor`.
3. Confirm editor opens embedded or in browser fallback.
4. Confirm MSBT delivery panel appears.
5. With BL4 closed, click `Refresh` in the Target section.
6. Confirm it shows a clean bridge-offline message.
7. Before building/loading an item, click Send to Selected Player.
8. Confirm it refuses because no serial is confirmed.
9. Build/load one item that produces one `@U` serial.
10. Click `Refresh Detected Serial`.
11. Confirm the preview shows the exact pending serial.
12. Click `Confirm Serial to Send`.
13. Confirm `Send to Selected Player` stays disabled until a target is selected.
14. Click `Copy Serial`.
15. Confirm clipboard matches the confirmed preview.
16. Start BL4 with SDK 03 and MSBT installed.
17. Confirm external app bridge connects.
18. Click `Refresh` in the Target section.
19. Confirm the player list appears.
20. Select the intended player.
21. Confirm selected target display updates.
22. Send to Selected Player.
23. Confirm the same preview serial was sent to the chosen target.
24. If multiple serial outputs exist, confirm the UI requires choosing one.
25. Change editor inputs and confirm the preview becomes stale.
26. Confirm no console/JS errors if possible.

## Known Limitations

- The embedded WebView path depends on pywebview and the available Windows WebView runtime. Browser fallback remains supported.
- The Matt editor save encryption/decryption endpoint is intentionally not enabled in the MSBT host.
- Delivery target selection uses the same MSBT/game bridge target state as the main app. The editor panel is another view/controller for that state, not a separate targeting system.
- This pass verifies host/adapter mechanics, not in-game delivery results.
