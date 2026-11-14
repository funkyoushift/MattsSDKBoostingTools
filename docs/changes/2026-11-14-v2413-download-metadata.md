# MSBT 2.41.3 download metadata — 2026-11-14

The default-branch desktop links still selected 2.41.2 after the 2.41.3 repair candidate was qualified. This change points the four desktop downloads and two GitHub source archives to 2.41.3 and records the exact verified source and package hashes. It does not merge the older default-branch runtime into the release source. Android 1.6.6 and the standalone Mission Selector retain their existing 2.39.9 asset pins.

Release source: `02ce2f6859b8d342da6eef9c45689c5431edc535`, parent `ca68ffe881ca3d0fed49bfe27a17c075757c7b12`. [Unified build 43569256755](https://github.com/funkyoushift/MattsSDKBoostingTools/actions/runs/43569256755) passed Windows, Linux and the aggregate gate. All four downloaded artifact sizes and SHA256s match both platform receipts and the aggregate. `latest.json` records the build verification time rather than retaining an obsolete build timestamp.

## Observed qualification

The Windows coordinator observed the repaired repeated-Start/Stop and editor lifecycle paths and preservation of a newer Bank menu during deferred cleanup. Existing physical controls, storage, installer/updater/recovery and preservation results remain credited; they were not replayed wholesale.

On Ubuntu 26.04.1 with Steam/Proton, two repaired production trials each acknowledged 18 fresh Starts, remained active for eight further seconds and acknowledged normal Stop. Close/reopen and Pause focus/navigation passed. Prior native Friends/profile protection and Save/edit/Save/full-game-restart/native-list-reload are retained because the repair left that UI/storage code unchanged. All 13 prescribed Linux package checks passed. Saves, original settings and security protections were preserved. The original failed lease trials remain recorded; their exact historical expiry cause remains unproven.

Both final CI packages contain the exact game-tested PAK and companion bytes. All 156 Linux SDK members match exactly; Windows SDK member differences are only CRLF/LF conversion, with no semantic differences. Outer SDK ZIP identities differ and are not presented as byte-identical. Desktop ASAR contents match the previously verified platform payloads. CI packaging and content comparison are distinct from the recorded native observations.

The earlier Ubuntu 26 CI-runner sandbox startup failure remains a separate historical limitation; successful native Ubuntu 26.04.1 qualification does not claim that runner was repaired. No exhaustive gameplay or guest-save proof is claimed.

## Publication and rollback

This metadata PR must merge only after publication through the unchanged `publish_verified_release.py` and successful public-asset verification. It does not authorize a direct release command or bypass the gate. The public release contains four application assets; GitHub supplies the two source archives. No SDK-only, APK or updater manifest asset is added here.

Offline metadata validation checks all six exact URLs, the four audited SHA256s, unchanged Android fields and unchanged README Android/selector links. Public download checks and the merge outcome are recorded by the release coordinator after publication. Reverting this metadata change restores the previous download pointers without modifying release assets, installations or user data.
