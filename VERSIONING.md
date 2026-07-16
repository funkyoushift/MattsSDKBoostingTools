# Versioning and GitHub Releases

Matt's SDK Boosting Tools uses Semantic Versioning for public Electron releases.

## Public Version Format

- Stable: `vMAJOR.MINOR.PATCH`
- Beta: `vMAJOR.MINOR.PATCH-beta.N`
- Alpha: `vMAJOR.MINOR.PATCH-alpha.N`

Examples:

- `v1.0.0`
- `v1.1.0`
- `v1.1.1-beta.1`

Do not use dates, commit hashes, workflow run IDs, or build timestamps as the primary public release version.

## Source of Truth

The Electron app version in `electron_poc/package.json` is the authoritative version for public Electron builds.

Release scripts derive these values from that package version:

- Git tag: `v<package version>`
- Release title
- Installer filename
- Portable ZIP filename
- Electron `latest.yml` version check
- Release notes version

Build timestamps and commit SHAs may appear only as secondary build information.

## Release Titles

Use these title patterns:

- Stable: `Matt's SDK Boosting Tools v1.0.0`
- Beta: `Matt's SDK Boosting Tools v1.1.1 Beta 1`
- Alpha: `Matt's SDK Boosting Tools v1.1.1 Alpha 1`

## Asset Names

Use these Windows asset names:

- Installer: `MSBT-Installer-v1.0.0.exe`
- Portable ZIP: `MSBT-Portable-v1.0.0-win-x64.zip`
- Legacy Tkinter rollback ZIP, if included: `MattsSDKBoostingTools-Legacy-Tkinter-Portable-v1.0.0.zip`

Electron updater metadata may remain named `latest.yml`, because that filename is expected by Electron tooling, but its contained `version` must match `electron_poc/package.json`.

## Safe Release Flow

1. Update `electron_poc/package.json` and `electron_poc/package-lock.json`.
2. Commit the version change and related release notes.
3. Build the SDK mod, Electron installer, and Electron portable ZIP with `.\build_electron_beta.ps1 -Installer`.
4. Optionally build the legacy Tkinter rollback ZIP with `.\package_external_beta.ps1`.
5. Create the semantic tag, for example `v1.0.0`.
6. Push the tag.
7. Publish assets with `.\publish_github_release.ps1`.

The publisher refuses to publish when:

- The tag does not match `electron_poc/package.json`.
- The version is not valid public SemVer.
- The release title contains timestamp, run ID, or commit-hash naming.
- The installer, portable ZIP, or `latest.yml` is missing.
- `latest.yml` reports a different version.

## Existing Legacy Releases

Older releases used tags such as `beta-<commit>` and `electron-beta-v0.2.1`. Those tags should remain in place unless a deliberate updater-compatibility review says they are safe to rename or delete.

For old releases, prefer editing the visible release title and release notes instead of deleting or retagging. Keep a note explaining that the legacy tag remains for compatibility.
