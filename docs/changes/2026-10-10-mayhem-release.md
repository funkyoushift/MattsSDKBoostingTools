# Mayhem release preparation - October 10, 2026

Martin explicitly requested release before further whole-game mission research.
Isolated from v2.34.0; version 2.35.0 adds a new user-facing Mayhem capability.
Only Mayhem frontend changes and the tested SDK repair set were ported. Unrelated
navigation/AFK/item-card work remains in the active product checkout.
The target mirror reuses the tested named-selector behavior limited to Mayhem.
107 focused tests, Python compilation, and workspace/classic Mayhem checks passed.
Live candidate evidence is retained under C:/src/MSBT-Workspace/local/mayhem-2026-10-10.
Desktop live action raised host 10->20; active difficulty stayed 10; Farming OFF
restored damage. The release SDK executable source will be compared to that
candidate, allowing metadata-only version changes. Guest own-lobby save/launch
confirmation is relayed user evidence, separate from packaged artifact checks.
Android 1.6.2 remains unchanged. Packaging/publication checks pending.
Rollback uses prior published v2.34.0; never replace a loaded game archive.
Whole-game mission completion remains excluded and research-only.
