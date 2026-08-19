# Squ1ggs → MSBT placement plan

Plan only. No Electron/SDK code, no SemVer, no release. Source: [`SQBT_FEATURE_INVENTORY.md`](./SQBT_FEATURE_INVENTORY.md), [`SQBT_INSPIRED_TEST_NOTES.md`](./SQBT_INSPIRED_TEST_NOTES.md), `electron_poc/renderer.html` tab bar + sections, `mod_extracted/MattsSDKBoostingTools/quick_menu_registry.py`.

**License:** Challenge Ticker and the bundled Squ1ggsBoostingTools SDK are **GPL-3.0** — copy *behavior*, not files. MIT packages (movement, vehicle, damage, resources, BMS, P2P, world travel) can be adapted **with credit**. Loot shapes live in the GPL bundled SDK, **not** in the MIT package list — reimplement, do not vendor.

---

## Pull Loot vs loot shapes (answer first)

**Same family, different job. Do not treat them as the same control. Do not add a Loot Shapes tab.**

| | **Pull Loot Here** (`movement_pull_ground_loot`) | **Loot shapes** (`loot_shape_*`) |
|---|---|---|
| What it does | One-shot gather: teleport nearby ground pickups to the local pawn | Layout engine: arrange those same pickups into named figures |
| Layout | Single Archimedean spiral so gear does not stack (Azzy-style pull) | Vault / circle / Firehawk / 3D house-boat / rarity lanes / type piles |
| Motion | Instant teleport | Drip vs snap, stop-drop, reapply last, Place Fully for co-op joiners |
| Clear | Sibling: Hide / Delete ground loot | Soft clear (hide shaped loot) |
| Where it lives today | Boosting **Essentials** + Player Movement **World / Utility**; F7 pin-able | Missing |

They share the actor set (`InventoryPickup`) and the teleport primitive. Pull is “bring the pile to me.” Shapes are “draw a picture with that pile.” Replacing Pull with a shape gallery would hide the daily button. Cloning Squ1ggs’ dedicated Loot Shapes tab would add a 15th top-level we do not want.

**Recommendation:** keep **Pull Loot Here** as the one-click on Boosting **Ground Loot**. Hide / Delete stay beside it. **Skip loot shapes** (gallery, drip/snap, reapply, Place Fully, shinies-land-in-shape).

---

## Verified MSBT public IA (from `renderer.html`, not guessed)

Nav, in order:

1. **Boosting** — Essentials (Max All, Drop All Backpack host, Shinies Drop/Deliver, Customs, Open/Close Golden Chest, Pull Loot, Super Dash), UVH 1–7, Challenges, Combat XP, Instant Actions + Debug Camera, Target Player, Combat & Cheats, Rarity Drop Weights, Serial Rewards, Backpack / Bank Size
2. **★ Quick Menu**
3. **Serial Tools** — convert, Serial Bookmarks, Validator
4. **Inventory** — equipped/backpack grid, **Open Bank Anywhere**
5. **BL4 Codes**
6. **Matt Editor**
7. **Item Pool Spawning**
8. **Dev Spawner** (public; Compact vs Panels) — actors, favorites, Barrel Logo, ASD spawn/clear/re-aggro
9. **Hoard Builder**
10. **Map Travel** — maps/stations, Travel Favorites, XYZ Location Bookmarks, Clear Fog of War
11. **Player Movement** — Presets / Save / Apply, Speed, Jump / Gravity, Infinite Jump, Wall / Step, Glide / Dash / Vault, World / Utility, Teleport
12. **Dev Tools** (`combat-vehicle`, hidden until Shift+click View → Development tabs) — Target Player, **Reset Skill Tree**, Streamer Chaos, Combat / Resource Tuning, Vehicle Presets / Spawn
13. **Activity Log**, **Mobile Gateway**, **Report to Dev**, **Updates**

**There is no Shinies tab.** Shinies Drop / Deliver live on Boosting Essentials. Layout docking (Fixed / Panels) is a per-tab chrome mode, not a nav item.

F7 / Electron QM already pin: Pull Loot, Hide Ground, Delete Ground, Super Dash, Open Bank, Open/Close Chest, Shinies, Complete All / Cancel Challenges, UVH, fog clear, movement presets, chaos suite, combat/vehicle apply, **Reset Skill Tree** (catalog yes; not in the compact native F7 picker).

---

## Placement rules

- No new top-level tab unless a feature has nowhere to sit. Squ1ggs’ ~15-tab bar (Home, Player, Challenges, Loot, Serials, Mobility, Vehicle, Damage, Resources, World, Mob/IO, Loot Shapes, FAAFO, Keybinds, Activity) is **not** the target IA.
- Prefer: extend an existing button → new subsection on an existing public tab → Dev Tools gate.
- If a Dev Tools control is already fully functional, or this work would make it so, **promote it** and say so here.
- Keep Hoard Builder as our wave system. Do not clone BMS mix-groups as a second wave UI.
- Keep Matt Editor / BL4 Codes / Inventory as-is; do not flatten them into a one-page “forge.”

**P0 already done:** Complete All Challenges (full catalog amount, chunk fallback, skip-and-continue, host gate, confirm, progress strip, Boosting placement). Remaining work is P1–P3.

---

## Promote out of Dev Tools

| Control | Destination | Why | Priority |
|---|---|---|---|
| **Reset Skill Tree** (`reset_skills`) | Boosting → **Combat & Cheats** (also keep QM pin; add to native F7 picker) | Already fully functional and pin-able; the only public-quality control trapped behind the WIP gate. Inventory lists us **Ahead**. Users never find a respec on a hidden tab. | **P1** — promote even if no other SQBT work ships |
| **Combat / Resource Tuning** (curated sliders today) | Boosting → new subsection **Combat Tuning** under Combat & Cheats | Completing MIT `bdam` / `brc` (elemental, melee, Second Wind, kits/shields, ammo regen **x5**, sticky re-apply) makes this a real boosting cheat, not a probe. **Policy hold:** test notes still say do not publish until Squ1ggs credit conversation is cleared. Promote *when* complete + credited; do not leave a half slider set on a public tab. | **P2** (promote with completeness) |
| **Vehicle Presets / Spawn** | Player Movement → new subsection **Vehicle** | Handling is mobility. Completing MIT BVM (full sliders, repeat-jump, unlimited jumps, catalog refresh, spawn unlock) makes this public-grade. mattmab presets already credited. Do **not** invent a Vehicle tab. | **P2** (promote with completeness) |

Do **not** promote Streamer Chaos, Target Player (duplicate), or the Dev Tools tab itself.

---

## Extend an existing public control

| Gap | Status | Extend this | Why | Priority |
|---|---|---|---|---|
| Loot shapes + reapply + drip/snap + Place Fully + soft clear | **Skip** | Too much work; Ground Loot keeps Pull / Hide / Delete only | — | skip |
| Shinies Drop land-in-shape | **Skip** | Needed the shapes engine | — | skip |
| Hide Ground Loot | **Parity** | Boosting **Ground Loot** | Sibling of Pull / Delete | **P1** |
| Spawn golden chest IO | Missing | Boosting Essentials next to Open / Close Golden Chest | Same chest verb; one extra spawn button, not an IO browser | **P1** |
| Black market spawn + cooldown clear + status | Missing | Boosting Essentials (farm row with chest / Pull) | Daily farm QoL, not a catalog tab | **P1** |
| Open pending Reward Center for everyone | Missing | Boosting **Serial Rewards** | Already the “give loot to the lobby” panel | **P1** |
| UVHM resume + “up to rank N” + staged lobby wait | Weaker / Missing | Boosting **UVH 1–7** (slider / Resume / keep per-tier buttons) | Same job as existing UVH strip | **P1** |
| Challenge multi-tick selected list | **Parity** | Boosting **Challenges** (`<select multiple>`) | Same list, multi-complete | **P2 done** |
| Spawn all filtered pools + progress/cancel | **Parity** | Item Pool Spawning (Spawn Selected already multi; add All Filtered + strip) | Same catalog, bulk verb | **P1** |
| Pool delay / items-per-tick / spit directions | **Parity** | Item Pool Spawning knobs | Tune the existing spawn | **P2 done** |
| Mix spawn groups | Missing | Item Pool Spawning | Combine filtered rows; not a new tab | **P2** |
| Force fly + fly speed | Missing | Player Movement World / Utility next to Noclip | Same cheat-mobility cluster | **P1** |
| Low / normal gravity one-click | Weaker | Player Movement **Jump / Gravity** (presets next to Moon) | Slider exists; missing one-click | **P2** |
| Movement preset UX | Weaker | Player Movement **Presets / Save / Apply** | Same panel, clearer save/load | **P3** |
| Fog hide on/off (session mesh) | **Parity** | Map Travel next to **Clear Fog of War** | Clear is discovery unlock; hide is session mesh — both fog | **P2** |
| Tuba Boss Arena + Dev Testing Map presets | **Parity** | Map Travel (preset buttons above the map list) | Named teleports, not a World tab | **P2** |
| Disallow local travel / cancel countdown | Missing | Map Travel utility row | Travel policy, same tab | **P2** |
| Freecam OFF / copy loc / speed / distance | **Parity** / Weaker (distance) | Boosting **Debug Camera** | Toggle, Disable, copy XYZ, 1x/5x/10x, distance 0=default | **P2 done** |
| Pull target to cam | **Parity** | Boosting Debug Camera (`debug_cam_to_target` cam→pawn; `teleport_debug_cam` stays pawn→cam) | Same strip | **P2 done** |
| Party kick UI | Weaker | Boosting **Target Player** (Kick already exists; add reason field) | Roster already lives here | **P3** |
| GZO / Lootlemon catalog UX | Weaker | **BL4 Codes** (already merged catalogs) | Do not add a Serials tab | **P3** |
| Serial SDK store | Weaker | **Serial Bookmarks** (Electron-local is our store) | Do not dual-write an SDK store | skip / **P3** |
| Legit Item Forge one-pager | Weaker | **Matt Editor** (deeper than his forge) | Do not clone a Boosting forge | skip |
| On-foot slider completeness vs embedded BPM | Weaker | Player Movement sliders (already the full tab) | Parity polish, not a new Mobility tab | **P3** |
| Vehicle boost/drift / status / catalog reload | Weaker | Player Movement **Vehicle** (after promote) | Same subsection | **P2** |
| Barrel logo actor/IO options + clear props | Weaker | Dev Spawner **Barrel Logo** | Already public | **P3** |
| Dev Spawner catalog / aggro UX | Weaker | Dev Spawner Compact + existing Re-Aggro | Do not add Mob/IO tab | **P3** |
| Hoard named packs vs BMS save/load | Weaker / Missing | Hoard Builder **Favorites** (named plans already exist) | Our wave model, not BMS packs | **P3** |
| Auto-copy mod on EXE launch | Weaker | **Updates** (install `.sdkmod` already; optional sync-on-launch) | Setup lives here | **P3** |
| Connection strip / start-here card / progress strip | Weaker | Boosting header / existing bulk panels | Sticky-everywhere is his shell; we keep Boosting as home | **P3** |
| In-app keybind editor | Weaker | **★ Quick Menu** slot hotkeys + oak2 | No Keybinds tab | **P3** |

---

## New subsection on an existing public tab (not a new top-level)

| Subsection | Tab | What goes in it | Why not a new tab | Priority |
|---|---|---|---|---|
| **Ground Loot** | Player Movement (expand World / Utility) | Pull, Hide, Delete | Family of Pull Loot; Boosting keeps the one-click | **P1** |
| **Combat Tuning** | Boosting (under Combat & Cheats) | Full MIT damage/kits/ammo x5 + sticky; **promoted from Dev Tools** | Cheats already live on Boosting | **P2** |
| **Vehicle** | Player Movement | BVM sliders, presets, spawn catalog, jumps, allow-personal-vehicle world flag | Handling is mobility | **P2** |
| **World flags** (small) | Map Travel | Allow personal vehicle *or* keep that on Vehicle; disallow local travel | Two or three toggles, not a World tab | **P2** |
| **IO / world props** | Dev Spawner (Interactive Objects fold) | `spawn_ios` catalog via Show Interactive Objects + Activate Last IO; golden-chest is *also* a one-click on Boosting | Dev Spawner is already the actor/IO home | **P2 done** |
| **Spawn near** | Boosting **Connection & Scope** | Anchor: me / named player / other party / nearest NPC for pools and Dev Spawner | Session-wide, like target scope; not a shell tab | **P2 done** |

**Do not create:** Loot Shapes, Vehicle, Damage, Resources, Challenges, Progression, Mob/IO, FAAFO, Keybinds, Home, World, or Serials as top-level tabs.

---

## Keep gated in Dev Tools (dangerous / chaos / WIP)

| Control | Why it stays gated |
|---|---|
| **Streamer Chaos** (launch, empty bag, FFYL, kill, invert/lock) | Intentional streamer grief suite. Timed FAAFO duration + auto-unlock **extends this panel**, does not promote it. |
| Inspect / destroy / damage looked-at (freecam) | Grief / grief-adjacent. Add under Chaos or leave off. |
| Weapons restricted | Lobby grief, not boosting. |
| Vehicle lock (disable vehicle actions) | Same. |
| Disable world AI spawn budget | Easy to brick a session; prove it on Dev Spawner first. |
| Pearl-pool companion **`.pak`** | Game asset, not a UI control. If we ever ship one: Updates / Item Pool data, still not a tab. Legal/packaging review first. |
| Manifest-driven UI, i18n, full theme pack, icon 15-tab bar | Shell clone. Skip. QM already has themes. |
| BMS mix groups / wave packs / encounter presets as a second runner | Hoard Builder is the public wave UI. Re-aggro / clear stay on Dev Spawner. |

---

## Every Missing / Weaker item (one line each)

P0 Complete = Challenges Complete All (done). Only Missing + Weaker rows.

### Layout / shell

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Sticky connection + version on every tab | Boosting header is enough; optional chrome later | public polish | Our home is Boosting, not a global strip | P3 |
| Roster on every tab | Boosting **Target Player** (keep) | public | Do not duplicate roster 16 times | skip |
| Spawn-near anchor | Boosting Target Player | new subsection | Session spawn origin | P2 |
| Icon 15-tab bar | — | skip | Would be the clone we refused | skip |
| Manifest-driven buttons | — | skip | Hardcoded HTML is our app | skip |
| Start-here card that hides when Online | Boosting (collapse existing oak2/update notices) | public polish | We already have first-run modals | P3 |
| Auto-copy mod every launch | Updates | public | Setup, not a game action | P3 |
| Themes | View / QM themes already exist | skip / P3 | Electron `data-theme` pack is optional chrome | P3 |
| i18n | — | skip | Not a boosting feature | skip |
| Global progress strip | Keep per-job strips (serial + challenges) | public | One sticky bar is his shell | P3 |
| Custom keybinds tab | ★ Quick Menu + oak2 | public | No Keybinds tab | P3 |

### Home / player / economy

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Spawn golden chest | Boosting Essentials | extend Open/Close | Same chest | P1 |
| Shinies drop land-in-shape | Boosting Essentials | skip | Needed shapes engine | skip |
| `rewards_open_everyone` | Boosting Serial Rewards | extend | Lobby reward-center open | P1 |
| Party kick + reason | Boosting Target Player | extend Kick | Roster already here | P3 |

### Progression

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Multi-tick challenge list | Boosting Challenges | extend | Same list | P2 |
| UVHM up to rank N + staged wait | Boosting UVH 1–7 | extend | Same strip | P1 |
| UVHM resume | Boosting UVH 1–7 | extend | Missing verb on existing job | P1 |

### Loot / serials / forge

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Spawn all filtered pools + cancel | Item Pool | extend | Bulk of current spawn | P1 |
| Delay / tick / spit | Item Pool | extend | Spawn knobs | P2 |
| Mix spawn groups | Item Pool | extend | Combine filters | P2 |
| One-page Legit Forge | Matt Editor | keep | We are already deeper | skip |
| GZO / Lootlemon UX | BL4 Codes | keep | Already the catalog tab | P3 |
| SDK serial store | Serial Bookmarks | keep | Electron is the store | skip |
| Black market spawn / cooldown / status | Boosting Essentials | extend farm row | Chest-class QoL | P1 |
| Pearl companion pak | Item Pool / Updates (asset) | gated until review | Not a tab | P3 |
| Loot shapes + reapply + stop/snap + clear + Place Fully | — | **skip** | Dropped; Pull Loot spiral stays | skip |

### Mobility

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Save/load preset UX | Player Movement Presets | extend | Same panel | P3 |
| Embedded BPM slider parity | Player Movement sliders | extend | Full tab already | P3 |
| Force fly | Player Movement World / Utility | extend Noclip row | Mobility cheat | P1 |
| Low / normal gravity buttons | Player Movement Jump / Gravity | extend | One-click on existing slider | P2 |

### Vehicle

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Full BVM sliders + status | Player Movement **Vehicle** | **promote from Dev Tools** when complete | Mobility | P2 |
| Boost/drift presets | same | promote | mattmab already credited | P2 |
| Repeat-jump / unlimited jumps | same | promote | BVM fields | P2 |
| Catalog reload + spawn unlock | same | promote | Catalog already in Dev Tools | P2 |
| Vehicle lock | Dev Tools Chaos | **keep gated** | Grief | gated |
| Allow personal vehicle world flag | Map Travel world flags *or* Vehicle subsection | public | World setting | P2 |

### Damage / kits / resources

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Full damage sliders | Boosting **Combat Tuning** | **promote** when MIT+credit complete | Combat & Cheats family | P2 |
| Sticky re-apply in combat | same (opt-in; keep Apply Once default) | promote | Already have Reapply After Travel | P2 |
| Kits / shields / lifesteal | same | promote | `brc` MIT | P2 |
| Ammo regen x5 toggle | same + optional Combat & Cheats next to Infinite Ammo | promote | Distinct from inf ammo perk | P2 |
| Weapons restricted | Dev Tools Chaos | **keep gated** | Grief | gated |

### World / travel / fog

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Tuba / Dev Testing Map presets | Map Travel | extend | Named jumps | P2 |
| Hide fog (session) | Map Travel next to Clear | extend | QM-only today | P2 |
| Disallow local travel / cancel countdown | Map Travel | extend | Travel policy | P2 |
| Barrel logo options / clear | Dev Spawner Barrel Logo | extend | Already public | P3 |

### Mob / IO / BMS

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| IO / world-prop catalog | Dev Spawner | new fold (skipped last pass) | Actor home | P2 |
| Aggro matrix | Dev Spawner | extend thin SetEnemy | Not a Mob tab | P3 |
| Re-aggro tracked | Dev Spawner (button exists) | extend | Already pin-able | P3 |
| BMS clear vs Hoard Emergency Clear | Hoard + Dev Spawner Clear | keep both | Different models | skip |
| Mix groups / wave packs / encounter presets | Hoard Builder Favorites | keep Hoard | Do not clone BMS | skip / P3 |
| Activate last IO | Dev Spawner (we have Activate Last Spawn) | extend | Same verb, IO filter | P2 |
| Disable world AI spawn budget | Dev Tools or Dev Spawner advanced | **keep gated** | Session brick | gated |

### P2P / freecam / chaos

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Freecam force-off, copy loc, speed, distance | Boosting Debug Camera | extend | Strip already there | P2 |
| Inspect / destroy / damage look-at | Dev Tools Chaos | **keep gated** | Grief | gated |
| Chaos invert/lock **duration** + timed unlock | Dev Tools Streamer Chaos | **keep gated**, extend | Same suite | P2 gated |

### Installer

| Item | Dest | Gate | Why | Pri |
|---|---|---|---|---|
| Silent mod sync on launch | Updates | public polish | Not a game tab | P3 |

---

## Suggested build order (still plan-only)

1. **P1 promote:** Reset Skill Tree → Boosting Combat & Cheats (no new engine).
2. **P1 Ground Loot:** Hide button beside Pull. **Skip loot shapes.**
3. **P1 farm QoL:** golden chest spawn, black market spawn/cooldown, `rewards_open_everyone`, UVHM resume / up-to-N, spawn-all-filtered pools.
4. **P1 mobility:** Force fly next to Noclip.
5. **P2 promote:** Combat Tuning + Vehicle subsections after MIT adapt + credit; only then leave Dev Tools.
6. **P2:** spawn-near, Item Pool knobs, Challenges multi-tick, Dev Spawner IO fold, backpack empty snapshot/undo/clear. **Map Travel presets/fog hide done. Debug Camera extras done.**
7. **P3 / skip:** shell clone, themes/i18n/manifest, BMS wave clone, pearl pak, grief toggles.

---

## Quick Menu (when implementing)

Pin the daily verbs, not the galleries: Pull Loot (already), Force fly, Reset Skills (add to **native** F7 picker), Open rewards everyone, UVHM resume, Spawn black market, Spawn golden chest, Fog hide toggle, Disable Debug Cam. Chaos stays assignable from the full editor, not the compact native list.

---

## Approval ask

Matt: confirm (1) Ground Loot lives next to Pull on **Player Movement**, not a new tab, (2) Reset Skill Tree promotes now, (3) Combat Tuning + Vehicle promote only after completeness + credit, (4) Chaos / weapons-restricted / look-at destroy stay gated. After that, implementation can start without inventing Squ1ggs’ 15-tab bar.
