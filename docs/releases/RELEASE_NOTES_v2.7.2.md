### What's new

**v2.7.2**

- **Reliable window memory** — MSBT now preserves the exact windowed size and position when maximizing, entering fullscreen, or restoring a Windows Aero-snapped window
- **Safer multi-display restore** — saved bounds are validated against the display they belong to instead of being trimmed to the primary work area
- **Regression coverage** — simulated and real Electron tests now exercise fullscreen, maximize, unmaximize, and snapped-window round trips

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.7.2.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.7.2-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

No SDK behavior changed in this patch. Existing settings and saved data are preserved.

Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
