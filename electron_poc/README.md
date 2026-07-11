# MSBT Electron Milestone Shell

This folder is an isolated Electron test shell. It does not replace the current Tkinter app.

The first goals are:

1. Can Electron talk to the existing SDK bridge over HTTP?
2. Can Electron show player/target state without importing SDK/game modules?
3. Can Electron check the current GitHub release manifest?
4. Can Electron render the vendored Mattmab editor assets inside the app shell?
5. Can Electron send one confirmed `@U` serial through the existing bridge actions?

## Run

From this folder:

```powershell
npm.cmd install
.\node_modules\electron\dist\electron.exe . --smoke
npm.cmd start
```

If PowerShell blocks `npm`, use `npm.cmd` exactly as shown.

If Electron says it failed to install correctly, approve its install script and rebuild it:

```powershell
npm.cmd approve-scripts electron
npm.cmd rebuild electron
```

## What This POC Tests

- `GET /status`
- `POST /action` with `set_target_player`
- `POST /action` with `give_serial_selected`
- `POST /action` with `give_serial_all`
- `POST /action` with `give_serial_nonhost`
- GitHub release manifest check through `releases/latest.json`
- local Matt editor iframe loading from `external_app/v22_parts_codes_fixed/matt_editor/index.html`

## Manual Test Flow

1. Launch BL4 with the current MSBT SDK mod.
2. Run `npm.cmd start`.
3. Confirm Bridge Status shows online players.
4. Pick a Target Player and click Set Target, or click Use First Player.
5. Click Check Updates and confirm it reads GitHub release metadata.
6. Click Load Editor and confirm the Matt editor appears inside Electron.
7. Build or load an item in the editor.
8. Click Detect Serial From Editor.
9. If a serial is found, click Confirm Serial.
10. Test delivery only with a small known-safe serial and a selected target.

## What This POC Does Not Do Yet

- It does not replace Tkinter.
- It does not package an Electron installer.
- It does not auto-update; it only reports update availability.
- It does not use the Python Matt editor host or adapter injection.
- It does not yet provide the full MSBT tab set.
- It does not change the SDK mod or bridge.
