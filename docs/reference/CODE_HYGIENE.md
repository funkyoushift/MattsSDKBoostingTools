# Code hygiene notes (Phase 4)

Small, evidence-based cleanups applied / deferred. Prefer `docs/reference/` or archive over deletes. Never delete BLImGui UI.

## Done this pass

| Item | Action |
| --- | --- |
| `probe_challenge_apis` | Gated behind `MSBT_DEBUG_PROBES=1` (bridge + optional console registration). Shipping default: disabled. |
| Stale Tkinter-as-replacement architecture doc | Moved to `docs/reference/docs/` |
| Version skew (`1.2.1` / `"1"` / `dev`) | Lockstep SemVer **2.1.0** with Electron / `latest.json` |

## Deferred (needs Matt / separate commits)

| Item | Why |
| --- | --- |
| `electron_poc` rename | Packaging/CI/docs churn; wait for explicit greenlight |
| `blimgui_panel` → always call `backend_actions` | Large transitional debt; chip one vertical at a time |
| `legit_builder_core` only on BLImGui path | Keep while optional panel uses it |
| Dual JSON copies mod ↔ `external_app/resources` | Need source-of-truth decision + sync script |
| Split monolithic `renderer.js` | Not anti-slop quarantine; modularization later |
| `ui-designer.css` | Still linked from `renderer.html` — verify before archive |
