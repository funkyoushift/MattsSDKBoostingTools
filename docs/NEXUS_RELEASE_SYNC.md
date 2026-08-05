# Nexus Mods Release Sync From GitHub Releases

> **Paused (Aug 2026):** Do **not** upload new MSBT builds to Nexus until Nexus responds about a static/GitHub-forward listing that avoids repeated quarantines. GitHub Releases remain the only distribution channel for now. Skip `nexus-release-sync` workflow and manual Nexus uploads until this note is removed.

MSBT publishes installer and portable ZIP assets to GitHub Releases first. Nexus Mods should be updated from that already-built release so Nexus and GitHub ship the same tested files.

Do not make GitHub release notes advertise Nexus as a mirror. GitHub Releases stay the app updater source of truth; Nexus is a second public distribution page that should be synchronized after the GitHub release is published.

MSBT Nexus page:

- https://www.nexusmods.com/borderlands4/mods/276
- https://www.nexusmods.com/borderlands4/mods/276?tab=files

## API Key Setup

Create a personal Nexus Mods API key from your Nexus Mods account settings, then store it outside the repo.

PowerShell user environment variable:

```powershell
[Environment]::SetEnvironmentVariable("NEXUSMODS_API_KEY", "paste-your-key-here", "User")
```

Open a new PowerShell window after setting it, then verify:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\check_nexus_release.ps1
```

Never commit API keys. `.env` and `.env.local` are ignored for local notes/secrets, but the release script reads `NEXUSMODS_API_KEY` from the environment.

## What Can Be Automated With The Public API

The Nexus Mods v3 API supports automated file upload. The attached v3 OpenAPI spec confirms:

- create upload sessions;
- upload file data;
- finalize uploads;
- create a new mod file from an upload;
- create a new version for an existing mod file;
- read the Nexus file list after upload.

MSBT uses the official Nexus Mods GitHub Action for normal release sync because the installer and portable ZIP are usually larger than 100 MB. Raw API uploads over 100 MB require multipart upload handling; the official action handles that workflow for us.

## GitHub Actions Setup

Create these GitHub repository settings before using `.github/workflows/nexus-release-sync.yml`:

Repository secret:

- `NEXUSMODS_API_KEY`: personal Nexus Mods API key from https://www.nexusmods.com/settings/api-keys

Repository variables:

- `NEXUSMODS_INSTALLER_FILE_ID`: Nexus file ID for the existing `MSBT Installer` main file.
- `NEXUSMODS_PORTABLE_FILE_ID`: Nexus file ID for the existing `Portable ZIP` main file.

The workflow updates existing Nexus file entries by file ID. It should not create a new installer file every release.

Run it from GitHub:

1. Open the repo Actions tab.
2. Choose **Sync Nexus from GitHub Release**.
3. Click **Run workflow**.
4. Enter the release version without `v`, for example `1.0.3`.
5. Leave `archive_existing_version` as `true` unless you intentionally want older Nexus file versions visible.

## Manual Fallback

If the Nexus action is down or Nexus quarantine review needs a manual upload, stage the exact GitHub release files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\stage_nexus_from_github_release.ps1 -OpenFolder
```

Then upload only the staged installer and portable ZIP to Nexus.

Manual Nexus file names:

- `MSBT Installer vX.Y.Z`
- `Portable ZIP - MSBT vX.Y.Z`

Manual file descriptions:

- Installer: `Recommended installer. Installs the MSBT Electron app, bundled SDK mod, ActorScriptDeployer support files, and required runtime files.`
- Portable ZIP: `Manual portable package. Use this if you do not want to run the installer. Extract the ZIP, then run the MSBT Electron app manually.`

After either automated or manual upload, verify:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\check_nexus_release.ps1
```

## Release Checklist

1. Build and publish the **GitHub** release first (installer + portable + `latest.json`; confirm download badges on the release page).
2. Sync Nexus from that same GitHub release:
   ```powershell
   # Preferred: GitHub Actions -> Sync Nexus from GitHub Release
   ```
3. Run `.\tools\check_nexus_release.ps1` after upload to confirm the Nexus file list matches the GitHub release version.
4. Spot-check Nexus file names/descriptions still match the manual fallback section below.
5. Do **not** point GitHub release notes at Nexus as a mirror; GitHub stays the updater source of truth.

## Current Release Links

The app updater still uses GitHub Releases because Electron updater expects GitHub-style `latest.yml` metadata. Nexus is a public mirror/download page, not the update feed.

Keep Nexus-only release notes on the Nexus mod page. Keep GitHub release notes focused on GitHub assets and the app updater.
