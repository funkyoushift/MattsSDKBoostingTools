# Release Metadata

This folder stores small release metadata tracked in source control.

- `latest.json` is the tiny version manifest uploaded to GitHub Releases and checked by the external app's Update button/banner.
- Release ZIP/EXE assets should be uploaded to GitHub Releases, not committed to the repository.
- Source code is available from GitHub's built-in source ZIP on the main repository page.
- Current MSBT builds require SDK 03 / oak2-mod-manager v0.3: <https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3>
- Latest downloads: <https://github.com/funkyoushift/MattsSDKBoostingTools/releases>

## Quick Menu tester pack (branch artifact)

Phone-friendly zip for Quick Menu preview testers (includes `.sdkmod` + install/smoke instructions). No BLImGui required.

- File: [`MSBT-QuickMenu-TesterPack.zip`](./MSBT-QuickMenu-TesterPack.zip)
- Branch download link:
  <https://github.com/funkyoushift/MattsSDKBoostingTools/raw/cursor/quick-menu-native-umg-0b18/releases/MSBT-QuickMenu-TesterPack.zip>

Electron release assets should use clear names:

- `MSBT-Installer-v...exe`
- `MSBT-Portable-v...-win-x64.zip`

For install instructions, start with the top of the main [README](../README.md).
