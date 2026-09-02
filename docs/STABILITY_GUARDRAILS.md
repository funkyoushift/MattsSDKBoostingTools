# MSBT stability guardrails (do not regress)

Short checklist for agents and reviewers. Run the cited tests before merging spawn or hoard changes.

## Dev Spawner default spawn path

**Contract:** `dev_spawner_spawnai` → `_run_actor_script_deployer_spawnai_like_debug_menu` → ActorScriptDeployer `_cmd_spawnai`. Hybrid `spawn_live` is **opt-in only** via `use_hybrid` / `dev_ai_hybrid` in the payload.

**Do not:**

- Call `_asd_hybrid.spawn_live` on the default Dev Spawner or hoard spawn path.
- Fail-closed on ASD `queued_unverified` (empty `GetAliveActors` peek is normal).
- Run `ASD_clear` disable-and-destroy on every clear (breaks the next ASD spawn Class template).

**Do:**

- After ASD spawn, call `asd_hybrid.note_after_asd_spawn` for census / verification uplift.
- On clear, use `_clear_spawned_actors_hybrid` → `asd_hybrid.clear_world` (despawn pawns, seal throwaways).
- Keep `spawn_live` for explicit tests / future memory-edit work only.

**Tests:** `tools/tests/test_asd_spawn_restore.py`, `tools/tests/test_asd_hybrid.py` (`test_backend_spawnai_defaults_to_asd_console`).

## Hoard Builder

**Contract:** `hoard_runner._spawn_next_job` calls `_run_actor_script_deployer_spawnai_like_debug_menu` **without** `use_hybrid=True`. Wave advance arms only on `verified_spawned` / `spawn_verified`, not bare ASD acceptance.

**Do not:**

- `K2_DestroyActor` on wave spawners in the death frame.
- Auto-call `hide_ground_loot` at wave transitions.
- Use `GetNumAliveActors` on throwaway spawners for alive count (use `asd_hybrid.count_alive`).

**Tests:** `tools/tests/test_hoard_spawn_staging.py`.

## Built-in Python (Electron panel)

**Contract:** Serial tools, validator, and Matt Editor host run `external_app/v22_parts_codes_fixed` via `pythonCandidates()` — bundled `resources/python/python.exe` when packaged, else `.venv` if present, else `python` / `py` on PATH. Skip missing exe paths (do not block on a absent `.venv`).

**Tests:** `electron_poc/test_python_worker.js`, `npm run check` (node --check).

## In-game proof (manual, BL4 open)

```
pyexec C:\Users\mwenn\Desktop\MSBT_Codex_Work\working\tools\asd_spawn_restore_probe.py
```

Expect ASD_spawnai acceptance and optional hybrid census note — not `spawn_live` / `no_pawn` for every catalog row.

## Explicitly deferred (not this pass)

- ASD memory hybrid as default spawn engine
- Hoard map-spawner hijack / CoS pad takeover
- Catalog 951 pump / item-card memory
- SemVer bump or GitHub release without Matt's ask
