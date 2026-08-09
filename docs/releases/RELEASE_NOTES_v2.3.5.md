### What's new

**v2.3.5** - Detect and install oak2-mod-manager v0.3 from the MSBT Updates tab.

#### oak2 SDK Manager
- Updates tab detects whether oak2-mod-manager v0.3 is present in the Borderlands 4 game folder
- **Install SDK Manager** downloads the official unmodified `oak2-sdk.zip` (LGPL-3.0) and installs it; the zip is cached under Electron `userData`, not vendored in git
- Startup notice when oak2 is missing (dismissible; rest of the app still works offline)
- **Install / Update SDK Mod** auto-enables MSBT + ActorScriptDeployer via `sdk_mods/settings/<module>.json`
- LGPL / third-party notices documented in `docs/THIRD_PARTY_NOTICES.md`

#### Updates tab
- Restored **Check for Updates** button
- Recheck SDK stack control for oak2 + MSBT status

#### Upgrade notes

1. Install `MSBT-Installer-v2.3.5.exe` (or extract the portable ZIP).
2. Open the Updates tab. If oak2 is missing, use **Install SDK Manager** (or the startup prompt).
3. Run **Install / Update SDK Mod** so MSBT + ActorScriptDeployer are installed and enabled.
4. **Fully restart Borderlands 4** so the SDK and bridge load.
5. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3) (installable from MSBT).

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.3.5.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.3.5-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap
