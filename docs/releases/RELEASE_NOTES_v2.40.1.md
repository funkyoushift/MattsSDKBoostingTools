# MSBT 2.40.1 — Guided Linux installation

The Linux download now opens **MSBT Setup**. It installs MSBT for your account, adds **MSBT** and **MSBT Setup** to your applications menu, and offers optional Borderlands 4 integration. It includes Python and PyYAML; no Node.js or Python installation is needed.

## Downloads — six items

| Platform | Installer | Portable folder |
|---|---|---|
| Windows x64 | `MSBT-Installer-v2.40.1.exe` | `MSBT-Portable-v2.40.1-win-x64.zip` |
| Linux x64 | `MSBT-Installer-v2.40.1-linux-x64.AppImage` | `MSBT-Portable-v2.40.1-linux-x64.tar.gz` |

GitHub adds **Source code (zip)** and **Source code (tar.gz)**. Both contain the shared Windows/Linux source; they are developer archives. There are four application downloads and two source downloads. Android and the standalone Mission Selector remain at [v2.39.9](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.39.9).

## Linux: download, open, install

1. Download the Linux installer above.
2. Right-click → **Properties → Permissions → Allow executing as a program** (wording varies by desktop).
3. Open it and click **Install MSBT**. Launch MSBT from the final screen or your applications menu.

Setup checks desktop libraries before opening its window. On supported Debian/Ubuntu/Mint and Fedora/RHEL-like systems, missing recognized packages can be installed after you review and approve the package list and administrator prompt. A package-list refresh may be offered separately on APT systems. The app runs as your normal user. Unsupported distributions or incompatible system libraries show an error rather than silently changing the system.

For optional game setup, run Borderlands 4 once through Steam, then close it normally. Setup installs the bundled SDK components and configures the selected game's Proton prefix. If Microsoft's Visual C++ runtime is missing, it offers distribution `protontricks` installation and the interactive runtime setup. If the game is running, the prefix is missing/busy, or you cancel a prerequisite, MSBT still installs and reports game setup pending. Use **Finish game setup**, or reopen **MSBT Setup** from your applications menu after resolving it. Setup never stops the game.

The installed app is `~/.local/share/msbt/MSBT.AppImage`. Previous replaced files are backed up. If FUSE mounting is unavailable, launch the downloaded installer with `--appimage-extract-and-run`. The portable TAR remains available for manual folder-based use. [Linux details](https://github.com/funkyoushift/MattsSDKBoostingTools/blob/v2.40.1/docs/LINUX.md).

## Windows and updates

Run the Windows EXE installer or extract the portable ZIP. Update notifications select and verify the matching platform package. Windows uses its EXE installer; Linux preserves the installed AppImage/portable path with rollback support. Very old clients using retired updater metadata need one manual installer update. Close the game before replacing its SDK files.

## Validation

Linux: actual installer window → packaged AppImage installation into a temporary home → receipt and application-menu shortcuts → installed launcher → bundled-runtime smoke test passed. Direct AppImage, extraction fallback, relocated portable startup, packaged/source matching and dependency-repair fixtures passed. Package-manager tests use fake commands; this workstation did not need system packages installed.

Game safety fixtures cover running/unknown games, busy/missing prefixes, rejected symbolic-link destinations, malformed settings, executable identity and the selected Proton prefix. Prior Linux preview live controls were user-confirmed; this installer adds no claim of exhaustive gameplay, mission, multiplayer or guest-save qualification. The live game was not interrupted or modified during installer validation.

Windows [CI 40726950587](https://github.com/funkyoushift/MattsSDKBoostingTools/actions/runs/40726950587) passed all package/interface audits, native updater-handoff fixtures and actual silent NSIS installation with installed payload hashes and bundled-runtime smoke. Windows ASAR matches reviewed source after normalizing checkout line endings. Interactive UAC itself was not automated. The Linux app was also installed on the development workstation and its installed launcher/runtime passed; the running game and loaded SDK were preserved.

## Package SHA-256

```text
0d30fa5da6828a3a373dabf501b9af65ec85bc5579ea1e5de02797ae841eb382  MSBT-Installer-v2.40.1-linux-x64.AppImage
15d74bd0ada8a807e0f1595e2f4ab2eb5270003b87744ff21c054360385e12ff  MSBT-Installer-v2.40.1.exe
5897b0994400e3d326e684cd81971281bd5466fd8590c145350d8bcf17ba703d  MSBT-Portable-v2.40.1-linux-x64.tar.gz
e1b4e59848ab9f0f488b4c5882f488b242b16984c979336a50301b71e6c0a52c  MSBT-Portable-v2.40.1-win-x64.zip
```
