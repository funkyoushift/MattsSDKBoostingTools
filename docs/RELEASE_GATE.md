# Required Windows and Linux release gate

Linux support is mandatory for every desktop release. This policy applies to future
releases; it does not retroactively claim complete Linux/Proton live qualification
for published 2.41.2. Passing a gate does not itself authorize publication.

## Build and platform verification

Run `unified-build.yml` on the exact candidate source with its lockstep public
version. Both OS jobs must succeed. Cancelled, skipped, failed or missing jobs fail
the aggregate `Required Windows and Linux release gate` job.

- Windows: actual NSIS installation in a disposable destination, every installed
  payload hash, portable ZIP parity, bundled Python/PyYAML, installed desktop smoke,
  and installed updater ASAR checks.
- Linux: native non-root x86-64 execution, AppImage extraction and relocated TAR
  content/mode/symlink checks, source/SDK/PAK/companion identity, bundled Python,
  actual packaged desktop smoke, actual per-user installation in a temporary HOME,
  Proton/discovery/setup fixtures, and native updater/rollback tests.
- Both receipts must match the exact commit/version and contain their two package
  filenames, sizes and SHA256 values. Four application assets are published;
  GitHub supplies the two source archives. SDK-only, APK and extra updater metadata
  files are not additional assets in this desktop release.

CI uploads platform receipts and `release-verification.json`. A packaging PASS has
`publication_ready: false` without native live-game evidence. Fixture checks and
headless desktop tests never establish live BL4/Proton compatibility.

## Native game qualification on both platforms

Before publication, exercise the candidate with BL4 on Windows and with its
Windows SDK under Linux Steam/Proton. Record game/SDK/Proton versions, installation
type, exact package hashes and observed results in a durable report. Cover:

- Installation, upgrade and recovery while the game is closed; preservation of
  existing SDK, settings, protected names, saves and launch configuration. Busy
  game/prefix states must defer changes. Include failed setup and retry cases.
- Companion connection and same-game-process authorization; first protected-list
  Save, edit, restart reload, missing/stale components and failed writes. Do not
  weaken authorization to make Proton pass.
- Desktop/in-game Start, Stop and Show; repeated toggles, sustained acceptance,
  normal keyboard/mouse/gamepad controls, Escape/Tab entry and exit, long menu
  dwell, travel/disconnect cleanup and normal control restoration.
- Actual social effects only with applicable user authorization; distinguish
  observed effects from fixtures and status transitions. Do not invent guest-save
  proof or mutate unrelated progression to fill a report.

Required live evidence is a human-authored attestation to actual test reports,
not automated proof that gameplay happened. Do not fabricate PASS entries. A
missing Linux machine, BL4/Proton installation, controller or test permission is
a concrete qualification gap: continue independent checks, but keep publication
blocked until the required evidence is available.

The JSON evidence shape is:

```json
{
  "schema_version": 1,
  "version": "X.Y.Z",
  "source_commit": "FULL_40_CHARACTER_CANDIDATE_SHA",
  "platforms": {
    "win32": {
      "status": "PASS", "kind": "live",
      "tested_at": "YYYY-MM-DDTHH:MM:SS+00:00",
      "evidence": "path or URL to actual Windows native test report",
      "artifact_sha256": {
        "MSBT-Installer-vX.Y.Z.exe": "SHA256",
        "MSBT-Portable-vX.Y.Z-win-x64.zip": "SHA256"
      }
    },
    "linux": {
      "status": "PASS", "kind": "live",
      "tested_at": "YYYY-MM-DDTHH:MM:SS+00:00",
      "evidence": "path or URL to actual Linux/Proton native test report",
      "artifact_sha256": {
        "MSBT-Installer-vX.Y.Z-linux-x64.AppImage": "SHA256",
        "MSBT-Portable-vX.Y.Z-linux-x64.tar.gz": "SHA256"
      }
    }
  }
}
```

## Publication

After explicit user release authorization, download both verified CI artifact
sets into one directory. Use `tools/publish_verified_release.py`, starting without
`--publish`. Supply version, source commit, artifact directory, Windows/Linux
receipts, live evidence, release notes and the successful unified build run ID.
See `--help` for exact arguments.

The publisher checks CI provenance, tag identity, both platform receipts and
native evidence, then stages exactly four assets in a draft. Only after remote
SHA256/size verification does it publish/latest. Failed uploads leave an inspectable
draft. It never overwrites an existing release. Do not bypass this entry point with
manual `gh release create/edit`, a Windows-only release or the legacy publisher.

After publication, verify all four complete public downloads, the latest-release
API and six public links; promote README/default-branch metadata without reverting
unrelated work. Preserve Android/selector pins and branch protection.

Enforcement consists of supported tooling, CI and repository instructions. A repo
owner can still operate GitHub directly; this does not claim a server-side ban on
all owner actions or change repository access permissions.
