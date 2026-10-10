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

## AFK addition requested before publication

Added optional AFK Mayhem (default off), target rank 1-20, capability guard for
older SDKs, and a per-character queue step using backend_actions.mayhem_boost_target.
The helper checks the expected PlayerState before any mutation; no panel selection
lookup occurs during AFK processing. Mayhem is not shared-completion work: every
guest receives their own saved rank write/check. Existing higher ranks and current
difficulty are retained by the previously tested progression action.
Touched afk_lobby.py, backend_actions.py, afk_lobby.js, renderer.html and regression
tests. 93 focused AFK/Mayhem/startup tests and the AFK Electron UI test passed.
Live AFK validation pending: current lobby was running, so no hot reload or archive
replacement was attempted. Martin was asked to stop AFK and quit normally.
The first release packaging run was interrupted before publication to add this.
