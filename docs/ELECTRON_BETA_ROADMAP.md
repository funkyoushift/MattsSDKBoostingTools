# Electron Beta Roadmap

MSBT is already a beta product. The Electron app does not need full Tkinter parity or final polish before beta release.

The Electron beta can replace the current beta when core workflows are usable, failures are visible, installation and updates work, and no known destructive or data-loss issue remains.

## Release Threshold

Release the Electron beta when:

- core workflows are usable
- no known destructive or data-loss issue remains
- failures are visible rather than silent
- the installer works
- update checks and updater flow work
- users have a practical bug report and feature request path

Do not delay the Electron beta for exhaustive Tkinter parity.

## Immediate Priority Order

Current checkpoint as of July 13, 2026:

- Serial Bookmarks are present in Electron.
- BL4 Codes are present in Electron and can deliver through the bridge.
- Boosting, Item Pool Spawning, Map Travel, Movement, Updates, Report, Activity Log, and Matt Editor shells are present.
- Installer/update foundation exists, but release/upload flow still needs a clean published Electron beta pass.
- Dev Spawner has the verified SDK 03 `ASD_spawnai` path and actor browser/favorites work, but still needs a closer source-port pass from SDK Debug Menu / ActorScriptDeployer UX.

Next priority order:

1. Dev Spawner source-port pass: use SDK Debug Menu only as UX/source reference and keep SDK 03 runtime on MSBT's verified bridge/backend path.
2. Electron tab parity pass: compare each Electron tab against BLImGui/Tkinter and close obvious missing buttons or workflows without redesigning.
3. Published Electron beta release pass: rebuild, verify, upload installer and ZIP to GitHub Releases, and keep old Tkinter beta available as rollback.
4. Update UX pass: startup update prompt, clearer installed-vs-latest app/SDK versions, download/install guidance.
5. Matt Editor integration pass: remove the awkward separate "Load Editor" feeling and make the embedded save/item editor path feel native.
6. Focused beta-readiness test.

## Beta Feature Classification

Every Electron beta feature should be classified as one of:

- included and working
- included with known beta limitation
- temporarily missing
- intentionally deferred

A missing nonessential feature is not automatically a release blocker.

## Release Blockers

Block release only for issues such as:

- app cannot install or launch
- updater cannot recover safely from failure
- app corrupts user data
- serial delivery commonly targets the wrong player
- app reports success for destructive failures
- packaged resources are missing
- SDK mod and app versions are incompatible without warning
- secrets or credentials are embedded in the build
- application cannot be removed or updated cleanly

## Stage 1: Dev Spawner My Favorites

Status: complete in source once committed.

Scope:

- Electron-owned `My Favorites`
- stored under Electron `app.getPath("userData")`
- separate from read-only Reference Quick Picks
- no writes to SDK Debug Menu, packaged catalog, repo workspace, Tkinter resources, or live `sdk_mods`
- same verified Dev Spawner spawn path

Commit:

```text
Add Electron Dev Spawner My Favorites
```

## Stage 2: Serial Bookmarks

Port the major stable workflow from the current Tkinter implementation.

Required beta scope:

- persistent bookmark list
- add
- edit
- delete
- search
- copy serial
- local validation
- confirmation invalidation when serial changes
- send to selected player
- send to all
- send to non-hosts
- visible success and failure responses
- persistence across restart

Import/export is desirable but not a blocker if it grows too large for the first beta slice.

Use Electron-owned user data. Do not write into the repo, Tkinter app folder, or SDK mod folders.

## Stage 3: BL4 Codes

Required beta scope:

- packaged local catalog
- search
- basic category/type filtering
- readable result list
- item details
- local parts breakdown
- copy code/serial
- validate locally
- add to Serial Bookmarks
- send through the existing serial-delivery path
- clear loading/error/empty states

Do not add internet scraping. Do not block this port on deep Matt save editor integration.

## Stage 4: Installer And Updater

Begin installer and updater work immediately after Serial Bookmarks and BL4 Codes. Do not wait for full Electron parity.

Required installer scope:

- Windows installer
- standard install location
- Start Menu shortcut
- optional desktop shortcut if supported cleanly
- uninstall entry
- preservation of `app.getPath("userData")` data
- bundled Electron app resources
- required local helper/runtime files
- clear beta branding and version display

Required update scope:

- app version visible in the UI
- manual Check for Updates action
- automatic lightweight check on startup or at a reasonable interval
- GitHub Releases as the likely release source
- beta channel support
- download progress
- visible update errors
- install-on-restart or another standard safe update flow
- user data preserved
- no embedded GitHub token
- no silent downgrade

## Version Compatibility

The Electron app and `MattsSDKBoostingTools.sdkmod` may update at different times.

At minimum, expose:

- Electron app version
- SDK mod version
- bridge-reported version
- compatibility status

If the installed SDK mod is too old or too new, show a clear warning.

The installer/updater should support the simplest reliable beta workflow. The likely target is a combined GitHub Release containing both the Electron app and SDK mod, with room for app-only updates later.

## Stage 5: Bug Reports And Feature Requests

Implement a secure beta-friendly first version.

Required workflow:

- choose Bug Report or Feature Request
- enter title
- enter description
- optional reproduction steps
- expected versus actual behavior for bugs
- automatically include Electron app version, SDK mod version, bridge status, Windows version, and recent filtered MSBT errors when available
- preview all information before submission
- allow removing diagnostic information
- copy/export report locally
- open a prefilled GitHub issue form or issue URL

Do not embed GitHub tokens, Discord webhooks, repository credentials, or private API keys.

## Stage 6: Focused Beta-Readiness Test

Do not perform an exhaustive parity audit. Test the workflows required for this beta:

- install
- launch
- connect to bridge
- player targeting
- basic serial delivery
- Serial Bookmarks
- BL4 Codes
- existing core boosting functions already present
- Dev Spawner
- app restart with settings preserved
- update check
- updater using a controlled test release if practical
- uninstall/reinstall without losing intended user data
- bug report generation

Document known missing features in release notes.

## Stage 7: Replace The Public Beta

Do not publish automatically.

Before replacing the current GitHub beta, report:

- installer artifact
- update artifact/feed structure
- SDK mod artifact
- exact version
- known limitations
- upgrade instructions from the Tkinter beta
- rollback instructions
- GitHub release title/tag
- assets to upload
- README download-link changes
- whether the old Tkinter beta remains available as a fallback

The release must be explicitly labeled:

```text
Electron Beta
```

Do not imply the Electron beta is stable or feature-complete.

## Working Style

- Move in larger coherent slices.
- Do not stop for minor polish unless it blocks usability.
- Do not turn every UI improvement into a separate planning task.
- Audit actual files first, implement, validate, and commit coherent features.
- Avoid guessing, mixing unrelated changes, committing generated output, touching `_inspect/` or `_install_backups/`, or publishing without explicit approval.
