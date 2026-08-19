# Squ1ggs Boosting Tools vs MSBT — feature inventory

Source of truth for **his** desktop app: Squ1ggs Boosting Tools **v1.1.0** portable (`sqbt-v1.1.0`, 2026-08-18), bundled SDK `panel_manifest.py` + README. Standalone MIT packages in [Squ1ggs/Bl4SDKmods](https://github.com/Squ1ggs/Bl4SDKmods) were also read. Matt’s fork: [funkyoushift/Bl4SDKmods](https://github.com/funkyoushift/Bl4SDKmods).

**License:** Challenge Ticker and the bundled Squ1ggsBoostingTools SDK are **GPL-3.0**. MSBT may copy *behavior*, not files. MIT packages (player movement, vehicle, damage, resources, BMS, P2P, world travel) can be adapted with attribution.

Status key:

- **Missing** — MSBT cannot do this
- **Weaker** — we have a version; his is more complete or easier
- **Parity** — same job, close enough
- **Ahead** — we have it; he does not

MSBT paths: `mod_extracted/MattsSDKBoostingTools/`, `electron_poc/renderer.html`.

---

## Layout / shell (not a game action, but it is why his app feels easier)

| Capability | His action / UI | Status | Notes |
|---|---|---|---|
| Always-on connection + mod version + session + target | Header status strip | **Weaker** | We show connection on Boosting; not sticky on every tab |
| Clickable party roster on every tab | Roster list | **Weaker** | Target Player lives on Boosting / Dev Tools |
| Spawn-near anchor (me / selected / nearest NPC) | `set_spawn_anchor` | **Parity** | Boosting Connection & Scope + Dev Spawner; item pools spawn at the anchor |
| Icon tab bar, ~15 tabs, short labels | Home, Player, Challenges, … | **Weaker** | We have more tabs, laundry-list labels |
| Manifest-driven buttons (SDK lists UI) | `getManifest` | **Missing** | Hardcoded HTML |
| Start-here card that hides when Online | Home featured | **Weaker** | We have oak2/update modals, not a first-run checklist that collapses |
| Setup: set install folder, Install SDK + mod, auto-copy mod on EXE launch | app Setup | **Weaker** | We install oak2 + sdkmod; he auto-syncs the bundled mod every launch |
| Quiet GitHub EXE update notice | in-app banner | **Parity** | We have Updates tab + modal |
| Themes (Default, Scooters, Tina, …) | `data-theme` | **Missing** | |
| i18n | `i18n.js` | **Missing** | |
| Global progress strip for bulk jobs | `#sqbt-progress-panel` | **Weaker** | Serial delivery + challenge bulk panels; not one sticky strip on every tab |
| Custom in-game keybinds tab | `user_keybinds` | **Weaker** | oak2 keybinds + QM hotkeys; no in-app keybind editor |
| Discord / Ko-fi Support tab | Support | **Ahead** (different) | We have Report to Dev + Mobile Gateway |

---

## Home / Player / economy

| Capability | His action | Status | MSBT |
|---|---|---|---|
| MAX ALL | `max_all` | **Parity** | `max_all` (includes vault cards) |
| Max cash / eridium | `max_cash`, `max_eridium` | **Parity** | `max_currency`, `max_eridium` |
| Give currency (kind, amount, delta/absolute) | `give_currency` | **Parity** | Boosting cheats + `give_currency` |
| Player 60 / spec 701 | `give_experience` | **Parity** | `max_player_level`, `max_spec_level` |
| Max SDU | `max_sdu` | **Parity** | `max_sdu` |
| Set backpack/bank sizes | `inventory_set_sizes` | **Parity** | Boosting inventory size + auto |
| Unlock all cosmetics | `devperk_activate` 4 | **Parity** | `devperk_4` All Customs + Hovers |
| God mode toggle | `devperk_activate` 6 | **Parity** | `devperk_6` Demigod |
| Infinite ammo toggle | `devperk_activate` 5 | **Parity** | `devperk_5` |
| Kill all enemies | `kill_all_enemies` | **Parity** | `devperk_3` |
| Spawn legendary/epic loot | `devperk_activate` 7 | **Parity** | `devperk_7` |
| Give 1M cash / 100k eridium / XP (devperk) | perks 1/2/0 | **Parity** | Combat & Cheats |
| Open / close golden chest | `golden_chest` | **Parity** | same |
| **Spawn** golden chest (IO) | `spawn_ios` `Lootable_GoldenChest` | **Missing** | We only open/close existing |
| Reward all shinies (mail) target / lobby | `shiny_mail_all` | **Parity** | Shinies: Deliver (scope) |
| Drop all shinies (ground, level, land shape) | `shiny_drop_all` + loot-shape fields | **Weaker** | Drop exists; no land-in-shape |
| Drop backpack | `faafo_drop_backpack` | **Parity** | Drop All Backpack (host-only public + chaos targeted) |
| Open pending rewards for **everyone** | `rewards_open_everyone` | **Missing** | Serial delivery can open rewards per send, not “everyone’s Reward Center” |
| Party kick + reason | `party_kick` | **Weaker** | `kick_player` exists; less UI |
| Refresh roster | `party_refresh` | **Parity** | Refresh Status |
| Skill tree reset | — | **Ahead** | `reset_skills` |
| Vault card max | via `max_all` / vault_cards | **Parity / Ahead** | bundled in `max_all` |
| Open bank anywhere | — | **Ahead** | `open_bank` |
| Combat XP multiplier | — | **Ahead** | Boosting Combat XP |

---

## Progression (challenges + UVHM)

Phase 1 (2026-08-18) landed Complete All completeness + Boosting placement. Remaining gaps are UX (multi-tick) and UVHM resume.

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Complete ALL non-UVHM | `challenge_bulk_start` category All non-UVHM | **Parity** | `complete_challenges_all` — full catalog amount, 250-chunk fallback so the sum still hits the goal, skip-and-continue, host/listen gate |
| Complete category | same + category select | **Parity** | `complete_challenges` + category (same grant path) |
| Complete selected / multi-tick list | `challenge_complete_selected` + `tokens[]` | **Parity** | Boosting Challenges `<select multiple>`; `complete_challenges` accepts `challenge_ids` |
| Cancel bulk | `challenge_bulk_cancel` | **Parity** | `complete_challenges_cancel` + F7 pin |
| Progress bar + ok/fail counts | `challenge_bulk_status` | **Parity** | `#challengeBulkPanel` (`done/total`, ok, fail) cloned from serial delivery |
| Confirm dialog (save warning) | manifest `confirm=` | **Parity** | `window.confirm` on Complete All / category / selected; 10s double-press removed |
| Host/listen refusal | runtime | **Parity** | Join client gets a clear host-only error |
| Full catalog **amount** + ChallengeObjectiveStates | increment + reconcile | **Parity** | Grant catalog amount; after queue, max `PlayerState.ChallengeObjectiveStates` for **granted** tokens only (`challenge_objective_complete.py`, MIT-original) |
| UVHM start target | `uvhm_start` + max rank field | **Weaker** | Per-tier buttons 1–7 + run all; no “up to rank N” slider, weaker wait/poll |
| UVHM entire lobby | `uvhm_start_all` | **Weaker** | Run All 1–7 hits live lobby; less staged wait |
| UVHM cancel / status | `uvhm_cancel`, `uvhm_status` | **Parity** | `uvh_boost_cancel`, `uvh_boost_status` |
| UVHM **resume** | `uvhm_resume` | **Missing** | |
| Challenges on a public tab next to UVHM | Challenges tab | **Parity** | Boosting Essentials, under UVH 1–7; “(WIP)” dropped |

Standalone **challenge_ticker** (GPL, Ctrl+F7 BLImGui) is the same job as his Progression tab. Do not vendor it.

---

## Loot / serials / forge

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Item pool spawn (searchable catalog) | `spawn_item_pool` | **Parity** | Item Pool Spawning tab |
| Spawn **all filtered** pools + progress | `spawn_item_pool_all` + status/cancel | **Parity** | Item Pool Spawning Spawn All Filtered + cancel/status |
| Delay / items-per-tick / spit directions | pool spawn fields | **Parity** | Item Pool delay, items/tick, spit; spawns use Spawn Near |
| Mix spawn groups | `spawn_mix` | **Missing** | |
| Legit Item Forge (root/parts, unlock rules, give) | forge actions | **Weaker** | Matt Editor is deeper; not a one-page forge in Boosting |
| GZO catalog deliver | Serials tab + save-editor.be API | **Weaker** | BL4 Codes tab (Ynot/Mattmab data) |
| Lootlemon catalog | Serials | **Weaker** | We ship lootlemon JSON; UX is different |
| Paste/deliver serials, count, rewrite level | `deliver_serials` | **Parity** | Serial Tools + delivery |
| Serial convert | convert | **Parity** | Serial Tools |
| Serial **store** (save/duplicate/delete entries in SDK) | `serial_store_*` | **Weaker** | Electron Serial Bookmarks (local), not SDK store |
| Delivery status | `serial_delivery_status` | **Parity** | Serial delivery progress panel |
| Rarity weights legendary / pearl / reset | `rarity_weights_set` | **Parity** | Boosting rarity panel |
| Black market **spawn machine** | `black_market` spawn | **Missing** | |
| Black market **clear purchase cooldown** | `black_market` cooldown | **Missing** | |
| Black market status | `black_market` status | **Missing** | |
| Pearl-pool companion **pak** | `companion_pak` / assets | **Missing** | He ships a `.pak` for pearl pools |
| Loot **shapes** (circle, vault, firehawk, 3D house/boat/…, rarity lanes, type piles, drip/snap) | `loot_shape_*` | **Skip** | Too much work for the payoff; Pull Loot spiral stays |
| Re-apply last loot layout | `loot_shape_reapply` | **Skip** | Dropped with shapes |
| Stop drop / snap to slots | `loot_shape_stop_drop` | **Skip** | Dropped with shapes |
| Soft clear (hide shaped loot) | `loot_shape_clear` | **Skip** | Hide Ground Loot already covers soft clear |
| Place Fully (co-op joiners) | `loot_shape_place_fully` | **Skip** | Dropped with shapes |
| Item validator | — | **Ahead** | Serial Tools Validator |
| Live inventory grid (filter, multi-select, give) | — | **Ahead** | Inventory tab |
| Matt Editor / save convert | — | **Ahead** | Matt Editor tab |

---

## Mobility

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Fast / moon / wall-walk / reset presets | `mobility_preset_apply`, `tuning_preset` bpm | **Parity** | Player Movement presets |
| Save / load current preset | `mobility_save_preset`, `mobility_load_preset` | **Weaker** | We save presets; UX differs |
| Auto-apply mobility on load | `mobility_auto_apply` | **Parity** | Saved movement preset auto-applies when connected |
| On-foot sliders (walk, jump, gravity, step, floor, glide, dash) + apply | `tuning_apply` module `bpm` | **Weaker** | Full slider tab exists; his embedded BPM is the MIT movement engine |
| Zero vault costs | `mobility_zero_vault` | **Parity** | `movement_zero_vault` |
| Time dilation set/reset | `mobility_time` | **Parity** | `movement_set_time` / reset |
| Noclip | `mobility_*` noclip toggle | **Parity** | `movement_toggle_noclip` |
| No-target | `pawn_no_target` / `mobility_toggle_no_target` | **Parity** | `movement_toggle_no_target` |
| Players-only | `mobility_players_only` | **Parity** | `movement_players_only` |
| Infinite jump sticky toggle | `mobility_infinite_jump` | **Parity** | IJ on/off/toggle + QM |
| **Force fly** + fly speed | `mobility_force_fly` | **Missing** | |
| Low / normal gravity buttons | `pawn_gravity` | **Weaker** | Gravity slider, no one-click low-g |
| Delete / hide ground loot | `mobility_delete_ground` + hide toggle | **Parity** | Clear Ground / Hide |
| Super dash | — | **Ahead** | MSBT + Azzy super dash |
| Pull loot here | — | **Ahead** | `movement_pull_ground_loot` |
| Scope Local / All / Others | tuning + movement | **Parity** | Movement scope |
| Slot teleports P1–P4 | mobility slot | **Parity** | `movement_teleport_to_slot` |

---

## Vehicle

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Apply / reset vehicle handling (embedded BVM) | `tuning_apply` `bvm` | **Weaker** | Presets only in Dev Tools; not full slider set |
| Boost / drift presets | `tuning_preset` bvm | **Weaker** | `vehicle_preset_apply` boost (and catalog) |
| Vehicle movement status | `tuning_status` bvm | **Weaker** | |
| Repeat-jump cooldown | BVM field | **Missing** | |
| Unlimited vehicle jumps / test jump | `bvm_vehicle_jump` | **Missing** | |
| Reload vehicle catalog | `vehicle_spawn_catalog_reload` | **Weaker** | Catalog refresh exists; not a dedicated button |
| Spawn personal vehicle from catalog | `vehicle_spawn` | **Weaker** | Dev Tools catalog; unlock less complete |
| Vehicle lock (disable vehicle actions) | `vehicle_actions_locked` | **Missing** | |
| Allow personal vehicle (world setting) | `world_personal_vehicle` | **Missing** | |

---

## Damage & kits / resources

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Full damage sliders (dealt/taken, elemental, melee, Second Wind, …) | `tuning_apply` `bdam` | **Weaker** | Curated sliders in hidden Dev Tools |
| Sticky re-apply during combat | bdam sticky | **Weaker** | Apply Once default; Reapply After Travel |
| Kits & shields (repair charges/CD, overshield, lifesteal, ammo regen) | `tuning_apply` `brc` | **Weaker** | Partial ammo regen / repair in combat tuning |
| Ammo regen **x5 toggle** (player tab) | `ammo_regen` | **Weaker** | Infinite ammo perk; no x5 regen toggle |
| Weapons restricted toggle | `weapons_restricted` | **Missing** | |

---

## World / travel / fog

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Travel to map (searchable) | `travel_map` | **Parity** | Map Travel |
| Travel to station (map + station) | `travel_station` | **Parity** | Map Travel |
| Named XYZ bookmarks | world_travel MIT / his world tab | **Parity** | XYZ Location Bookmarks |
| Tuba Boss Arena preset | `travel_preset` tuba | **Parity** | Map Travel button → `Tuba_P.BossFightExit` |
| Dev Testing Map preset | `travel_preset` bespoke_visionquest | **Parity** | Map Travel button → `Bespoke_VisionQuest.LT_DGN_VisionQuest_Start` |
| Temp hide map fog (session FogMesh) | `map_fog_hide` | **Parity** | Map Travel Hide/Show/Toggle + QM `fog_of_war_*` |
| **Clear fog / unlock exploration** | — | **Ahead** | `fog_of_war_clear` |
| Disallow local travel | `oak_travel` disallow_local | **Missing** | |
| Cancel travel countdown | `oak_travel` cancel_countdown | **Missing** | |
| World text / barrel logo (3 lines, actor picker, scale) | `barrel_logo` | **Weaker** | Dev Spawner Barrel Logo; fewer actor/IO options |
| Clear world text props | `barrel_logo_clear` | **Weaker** | |

---

## Mob / IO / BMS

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Char_* enemy spawn from big catalog | `spawn_mobs` / BMS | **Weaker** | Dev Spawner ASD_spawnai; Compact/Panels UX |
| IO / world-prop spawn catalog | `spawn_ios` | **Missing** | Explicitly skipped in SQBT-inspired notes |
| Aggro modes | BMS aggro | **Weaker** | Thin SetEnemy; not full wake matrix |
| Re-aggro tracked mobs | `bms_reaggro` | **Missing** | |
| Clear tracked BMS spawns | `bms_clear` | **Weaker** | Hoard Emergency Clear / ASD clear — different model |
| Mix groups + wave packs (start/stop/next) | `bms_group_*` | **Missing** | Hoard builder is our wave system, different |
| Save/load named spawn packs | BMS pack save | **Missing** | Favorites exist; not named wave packs |
| Encounter presets | `spawn_encounter` | **Missing** | |
| Activate last IO spawn | `bms_activate_io` | **Parity** | Dev Spawner Interactive Objects fold + Activate Last |
| Disable world AI spawn budget | BMS default | **Missing** | |
| Hoard (persistent enemy field, pacing, no destroy spawners) | — | **Ahead** | Hoard Builder |
| Boss chip / favorites | BMS UI | **Parity** | Dev Spawner |

---

## P2P / freecam / chaos

| Capability | His action | Status | MSBT |
|---|---|---|---|
| Me → selected / selected → me | `teleport_party` | **Parity** | Movement teleport |
| All → me | (P2P MIT `bcst_*` / party) | **Parity** | `movement_teleport_all_to_me` |
| Toggle freecam | `freecam_toggle` | **Parity** | `toggle_debug_cam` |
| Freecam OFF if stuck | `freecam_disable` | **Parity** | `disable_debug_cam` |
| Pull target to cam | `freecam_pull_target` | **Parity** | `debug_cam_to_target` (cam→pawn). `teleport_debug_cam` remains pawn→cam |
| Copy cam location | `freecam_copy_location` | **Parity** | `debug_cam_copy_location` (Electron clipboard; BLImGui logs XYZ) |
| Freecam speed 1x/5x/10x + custom | `freecam_set_speed` | **Parity** | `debug_cam_set_speed` (0.05–50x) |
| Freecam distance | `freecam_set_distance` | **Weaker** | `debug_cam_set_distance` best-effort fields; 0 = game default |
| Inspect / destroy / damage looked-at | `freecam_*_target` | **Missing** | |
| Launch skyward (Z impulse) | `faafo_launch` | **Parity** | `chaos_launch` |
| Empty backpack (delete) | `faafo_empty_backpack` | **Parity** | `chaos_empty_backpack` (Dev Tools). Snapshots `@U` serials per target, **Undo Empty Backpack** restores to that same player, **Clear Deleted Backpack Memory** drops the snapshot |
| Force FFYL / kill | `faafo_ffyl`, `faafo_kill` | **Parity** | chaos FFYL / Kill |
| Invert/lock look/move with **duration** | `faafo_*` seconds | **Weaker** | Chaos toggles without timed auto-unlock |
| Timed chaos auto-unlock | FAAFO seconds | **Missing** | `chaos_unlock` is manual |

---

## Installer

| Capability | His | Status | MSBT |
|---|---|---|---|
| Install official oak2 when missing | Setup | **Parity** | Updates / startup modal |
| Update base SDK | Setup | **Parity** | |
| Auto-copy **his** mod when EXE version changes | AUTO MOD SYNC | **Weaker** | We install `.sdkmod` from Updates; not silent every launch |
| Point at game folder on another drive | Set install folder | **Parity** | |

---

## What MSBT has that he does not (Ahead)

Keep these; do not flatten them away in Phase 2.

- Native **F7 Quick Menu** + pin/repeat + per-slot hotkeys
- **Matt Editor** (save/profile convert, legit parts, YAML)
- **BL4 Codes** as a first-class tab
- **Inventory** backpack/equipped grid, filters, multi-select, give
- **Hoard Builder** (persistent spawns, pacing, emergency clear)
- **Mobile Gateway** + Android companion
- **Instant Drops / Instant Holds** (oak2 keybinds + QM)
- **Combat XP multiplier**
- **Drop All Backpack** called out host-only on Boosting
- **Open Bank Anywhere**
- **Skill reset**
- **Clear Fog of War** (discovery unlock, not just hide mesh)
- **Super Dash** (MSBT + Azzy)
- **Pull Loot Here**
- **Serial validator**, bookmarks, breakdown
- **Layout docking** (Fixed/Panels, snap, Arrange Locked, viewport-keyed saves)
- **Walkthroughs**, text size, Select Multiple
- **Report to Dev**
- Optional **BLImGui** fallback panel
- Streamer chaos suite on Dev Tools (also overlapping FAAFO)

---

## Top 15 Missing (his yes, ours no)

1. **Loot shapes** — arrange ground loot into vault/circle/3D/rarity lanes + drip/snap
2. **IO / world-prop spawner** (`spawn_ios`, BMS IO catalog)
3. **Spawn-all-filtered item pools** with progress/cancel
4. **Black market spawn + purchase cooldown clear**
5. **Spawn golden chest** as an IO
6. **Force fly**
7. **Open pending Reward Center for everyone** (`rewards_open_everyone`)
8. **UVHM resume**
9. **Freecam speed/distance/inspect/destroy/damage looked-at**
10. **Weapons restricted** + **vehicle lock**
11. **World travel presets** (Tuba Boss Arena, Dev Testing Map)
12. **Disallow local travel / cancel travel countdown / allow personal vehicle world flag**
13. **BMS mix groups, wave packs, encounter presets, re-aggro, activate last IO**
14. **Pearl-pool companion pak**
15. **Manifest-driven UI + sticky roster + spawn-near + themes** (shell; not one action)

Phase 1 in this repo does **not** implement that Missing list. It only makes Complete All actually complete and moves Challenges next to UVHM.

---

## Source files read (2026-08-18)

Do not treat this as memory. Truth sources:

- Squ1ggs portable v1.1.0 renderer: `%TEMP%\sqbt-index.html`, `%TEMP%\sqbt-app.js`
- Bundled SDK: `%TEMP%\sqbt-sdk\panel_manifest.py` (15 tabs: Home, Player, Progression, Loot, Serials, Mobility, Vehicle, Damage, Resources, World, Mob/IO, Loot Shapes, FAAFO, Keybinds, Activity; 175 `_action` + 23 `_toggle` labels)
- Bundled README / CHANGELOG under `%TEMP%\sqbt-sdk\`
- Challenge Ticker unpacked for behavior notes only (GPL — not vendored)
- MSBT: `electron_poc/renderer.html`, `electron_poc/renderer.js`, `mod_extracted/MattsSDKBoostingTools/backend_actions.py`, `external_bridge.py`, `quick_menu_registry.py`
