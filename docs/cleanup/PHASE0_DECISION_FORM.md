# Phase 0 decision form

Fill this out and send it back (paste here or attach the file).

**How to mark:** put `X` in **one** of Keep / Reference / Archive for each row.  
Use **Notes** for anything special (“keep ActorScriptDeployer only”, “delete forever”, etc.).

**Legend**

- **Keep** — stays in `working` (main project)
- **Reference** — small in-repo `_reference/` (handy later, not day-to-day)
- **Archive** — move to sibling `_msbt_archive/` (out of main)

---

## Your global notes

```
(write anything here)



```

---

## A. Product core


| #   | Path                                                                                              | Keep | Reference | Archive | Notes                        |
| --- | ------------------------------------------------------------------------------------------------- | ---- | --------- | ------- | ---------------------------- |
| A1  | `mod_extracted/`                                                                                  | X    |           |         | SDK mod source               |
| A2  | `electron_poc/`                                                                                   | X    |           |         | Desktop app                  |
| A3  | `external_app/`                                                                                   | X    |           |         | Electron helpers + resources |
| A4  | `docs/`                                                                                           | X    |           |         | Product docs                 |
| A5  | `releases/`                                                                                       | X    |           |         | Notes + latest.json          |
| A6  | `tests/`                                                                                          | X    |           |         |                              |
| A7  | `tools/`                                                                                          | X    |           |         |                              |
| A8  | `third_party/sdk_mods/ActorScriptDeployer/`                                                       | X    |           |         | Installer dependency         |
| A9  | `.github/`                                                                                        | X    |           |         | CI                           |
| A10 | `README.md` / `AGENTS.md` / `LICENSE` / `VERSIONING.md` / `THIRD_PARTY_NOTICES.md` / `.gitignore` | X    |           |         |                              |


---



## B. LOV / loot probe (default = Archive)


| #   | Path                                       | Keep | Reference | Archive | Notes |
| --- | ------------------------------------------ | ---- | --------- | ------- | ----- |
| B1  | `_loot_probe_dumps/`                       |      |           | X       |       |
| B2  | `_lov_peek/`                               |      |           | X       |       |
| B3  | `lov_agent_client/`                        |      |           | X       |       |
| B4  | `third_party/sdk_mods/DedicatedLootProbe/` |      |           | X       |       |
| B5  | `third_party/sdk_mods/LOVAgentBridge/`     |      |           | X       |       |


---



## C. Scratch / builds (default = Archive)


| #   | Path                                           | Keep | Reference | Archive | Notes |
| --- | ---------------------------------------------- | ---- | --------- | ------- | ----- |
| C1  | `dist/`                                        |      |           | X       |       |
| C2  | `dist_electron/`                               |      |           | X       |       |
| C3  | `build/`                                       |      |           | X       |       |
| C4  | `MSBT_External_Beta/`                          |      |           | X       |       |
| C5  | `MSBT_External_Beta_FINAL_TEST/`               |      |           | X       |       |
| C6  | `_nexus_upload/`                               |      |           | X       |       |
| C7  | `_release_check/`                              |      |           | X       |       |
| C8  | `_install_stage/`                              |      |           | X       |       |
| C9  | `_pack_stage_qm/`                              |      |           | X       |       |
| C10 | `_install_backups/`                            |      |           | X       |       |
| C11 | `_sdkmod_compare_working_vs_installed_backup/` |      |           | X       |       |
| C12 | Root `*.sdkmod` + `*_headless_*` packages      |      |           | X       |       |
| C13 | Root Legacy Tkinter portable `*.zip`           |      |           | X       |       |


---



## D. Reference candidates (please confirm)


| #   | Path                                                          | Keep | Reference | Archive | Notes                |
| --- | ------------------------------------------------------------- | ---- | --------- | ------- | -------------------- |
| D1  | `_explore_ui_showcase/`                                       |      | X         |         | UMG / QM inspiration |
| D2  | `_inspect/`                                                   |      | X         |         | Azzy / debug peeks   |
| D3  | Root `MATT_*` / `DEV_SPAWNER_*` / `SDK03_*` audit `.md` files |      | X         |         | Agent planning dumps |


---



## E. Decisions that need your call

Put `X` on one choice, or write your own in Notes.

### E1 — Legacy Tkinter packaging at repo root


| Choice                                                                                                                                  | X   | Notes                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------- | --- | -------------------------------------------------------------------------------------------------------------------- |
| Keep at root (`build_external_exe.ps1`, `package_external_beta.ps1`, `Launch_MSBT_External_App.bat`, `requirements-external-build.txt`) |     |                                                                                                                      |
| Move to `_reference/legacy_tkinter/`                                                                                                    | X   | ASSUMING WE DON'T NEED THIS UNLESS WE ARE LOOKING AT IT FOR REFERENCE THEN IT CAN PROBABLY GO INTO ARCHIVE/REFERENCE |
| Archive off-repo                                                                                                                        |     |                                                                                                                      |




### E2 — `_explore_ui_showcase/` + `_inspect/`


| Choice              | X   | Notes |
| ------------------- | --- | ----- |
| Reference (default) |     |       |
| Archive with probes | X   |       |




### E3 — Root audit markdown files (`MATT_*`, etc.)


| Choice                                        | X   | Notes                                                                                                    |
| --------------------------------------------- | --- | -------------------------------------------------------------------------------------------------------- |
| Move to `_reference/audits/` and commit       |     |                                                                                                          |
| Archive off-repo only (remove from main tree) | X   | UNLESS WE REALLY DON'T NEED THEM. i WOULD THINK YOU COULD STILL USE THEM FOR LOOKING BACK AT WHAT WE DID |
| Delete (I don’t need them)                    |     |                                                                                                          |




### E4 — `releases/` tester packs / Discord media


| Choice                                              | X   | Notes |
| --------------------------------------------------- | --- | ----- |
| Keep under `releases/`                              |     |       |
| Archive old tester zips; keep notes + `latest.json` | X   |       |




### E5 — Anything else to add / protect / nuke?

```
(write here)



```

---



## Sign-off

- Your name / date: _______________
- Ready for Phase 1 moves? `Yes` / `No` / `Yes, but wait on: _______________`

