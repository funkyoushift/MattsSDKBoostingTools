## Community folders and developer portal

- Share a saved bookmark folder, including its subfolders, through Saved Items → Community folders → Submit one of my folders.
- Submissions stay private until approved. Browse approved folders, preview their items, share links, and import a separate copy without replacing existing bookmarks.
- Imported folders can be selected in AFK Lobby. Item order, duplicates, and exact codes are preserved. Sharing supports lists up to 16 MiB; existing game-delivery rules still apply.
- The Developer portal has individual accounts, owner-assigned team roles, folder approval, item editing, deletion, and an activity log. New accounts receive no management access. Edits return a folder to the approval queue.
- Email verification and forgotten-password recovery are not configured yet. Owners assign access using a teammate's confirmed account ID; email addresses are not verified identities.

## Automatic game setup restored

- The reusable MSBT-Setup.exe now runs bundled game setup after installing or updating the desktop app: MSBT SDK mod, ActorScriptDeployer, AFK SHiFT PAK, and missing SDK/mod-manager components.
- Existing SDK/mod-manager installations, including newer/beta/custom versions, are preserved.
- Setup waits for game integration and reports failure instead of claiming success. Close Borderlands before installing; setup never closes the game. Choose game folder is available if automatic detection fails, and protected paths may require Windows permission.
- A game-setup.log receipt is saved alongside the app installation.

## Validation and scope

Hosted account, permission, submission privacy, approval, edit, deletion, and sign-out checks passed. Local bookmark regression checks, offline SDK/PAK installation, and 27 installer checks passed. In-game boost/delivery behavior is unchanged. The Android controller is unchanged.

## Download

Run **MSBT-Setup.exe** for the reusable installer, or **MSBT-Installer-v2.18.0.exe** for the versioned installer. Portable users can use **MSBT-Portable-v2.18.0-win-x64.zip**.
