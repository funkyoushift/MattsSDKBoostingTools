### What's new

**v2.7.3**

- **Overlapping layouts stay put** — GridStack arrangements that overlap are no longer discarded on launch, so custom panel stacking comes back after you close the app
- **Arrange Unlocked / Locked** — freeze drag and resize from the tab toolbar; the lock is saved per tab
- **Safer layout upgrades** — Boosting min-revision bumps now migrate saved coordinates instead of wiping custom layouts
- **Regression coverage** — save/load and lock tests cover persistence, overlap restore, and coordinate migration

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.7.3.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.7.3-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

No SDK behavior changed in this patch. Existing settings and custom panel layouts are preserved.

Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
