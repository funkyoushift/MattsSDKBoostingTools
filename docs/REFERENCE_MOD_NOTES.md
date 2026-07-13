# Reference Mod Notes

This file records local reference mods reviewed for useful MSBT ideas. It is not
a code-import record. Unless a later commit says otherwise, MSBT has not copied
implementation code from these mods.

Public catalog reference:

- https://bl-sdk.github.io/oak2-mod-db/

## Summary

| Mod | Author | Local license | Useful to MSBT | Current decision |
| --- | --- | --- | --- | --- |
| BL4 Player Movement | Squ1ggs | MIT | Movement component lookup, scoped player targeting, reset/default handling, vault cost helpers | Safe candidate for future adaptation with attribution |
| obj_dump | apple1417 | GPL3 | Object property dump diagnostics | Reference only unless GPL compatibility is explicitly accepted |
| Dump Ping | Yeti | GPL3 | Ping-to-object discovery workflow | Reference only unless GPL compatibility is explicitly accepted |
| Trash Seller | FreepDryer | GPL3 | Inventory iteration and sell-junk workflow | Reference only; destructive inventory actions are out of current scope |
| Falling Menus | Yeti | GPL3 | Menu-open workaround while falling/gliding | Reference only; not relevant to current MSBT scope |
| Grapple Anywhere | Yeti | GPL3 | Grapple hooks and movement ideas | Reference only; also includes pak-side assets |

## BL4 Player Movement

Local file reviewed:

- `bl4_player_movement/__init__.py`
- `bl4_player_movement/pyproject.toml`
- `bl4_player_movement/LICENSE`

Metadata found:

- Author: Squ1ggs
- Version: 1.0.5
- License: MIT

Useful patterns:

- Runtime player/controller discovery and scope handling:
  - `_iter_pcs`
  - `_try_pawn`
  - `_get_local_pc`
  - `_is_local_pc`
  - `_iter_pawns_for_bpm_scope`
- Character movement component resolution:
  - `_resolve_character_movement_on_pawn`
  - `_iter_bpm_movement_hits`
- Path-based property access:
  - `_pawn_set_path`
  - `_pawn_get_path`
- Float read/write helpers:
  - `_read_float`
  - `_write_float`
  - `_apply_field`
- Reset/default and preset behavior:
  - `_reset_all`
  - `_apply_preset`
- Vault movement helper ideas:
  - `_vault_show`
  - `_vault_zero`
  - `_vault_set_uniform`

Potential MSBT use:

- Improve or verify Movement tab reset behavior.
- Harden player scope handling for local/all/others style movement operations.
- Compare movement field names against MSBT's SDK 03 backend before changing
  the live implementation.

Because this mod is MIT, code can be adapted if needed, but attribution and the
license notice must remain.

## obj_dump

Local files reviewed:

- `obj_dump/__init__.py`
- `obj_dump/pyproject.toml`
- `obj_dump/LICENSE`

Metadata found:

- Author: apple1417
- Version: 3 / `3 (86bdfa06)`
- License: GPL3

Useful patterns:

- Console command for dumping UObject properties.
- `dump_object(obj, file=None)` as a diagnostic workflow.

Potential MSBT use:

- Good inspiration for future Dev Spawner / actor inspection diagnostics.
- Do not copy GPL implementation into MSBT unless we explicitly accept GPL
  compatibility for that portion.

Credit note:

- apple1417 should be credited for BL4 SDK ecosystem work and obj-dump style
  diagnostic inspiration if MSBT gains a similar diagnostic feature.

## Dump Ping

Local files reviewed:

- `dump_ping/__init__.py`
- `dump_ping/pyproject.toml`

Metadata found:

- Author: Yeti
- License: GPL3
- Depends conceptually on obj_dump.

Useful patterns:

- Hooks `OakPlayerController:ClientCreatePing`.
- Dumps the pinged actor.

Potential MSBT use:

- Future actor discovery idea: ping an object in game, then inspect or bookmark
  its actor data for Dev Spawner.
- Reference only unless GPL compatibility is explicitly accepted.

## Trash Seller

Local files reviewed:

- `trashSeller/__init__.py`
- `trashSeller/pyproject.toml`

Metadata found:

- Author: FreepDryer
- License: GPL3

Useful patterns:

- Inventory iteration.
- Junk-item selection/sell workflow.
- Hook around `OakPlayerController:ServerUseJunkObject`.

Potential MSBT use:

- Reference only. This is a destructive inventory workflow and should not be
  folded into MSBT without a separate safety design.

## Falling Menus

Local files reviewed:

- `FallingMenus/__init__.py`
- `FallingMenus/pyproject.toml`

Metadata found:

- Author: Yeti
- License: GPL3

Useful patterns:

- Temporarily adjusts movement/menu state to open a menu while falling or
  gliding.

Potential MSBT use:

- Low priority. Reference only.

## Grapple Anywhere

Local files reviewed:

- `GrappleAnywhere/README.txt`
- nested `GrappleAnywhere.sdkmod`
- `GrappleAnywhere/__init__.py`
- `GrappleAnywhere/pyproject.toml`

Metadata found:

- Author: Yeti
- License: GPL3
- Includes pak-side assets in addition to SDK code.

Useful patterns:

- Grapple input/keybind ideas.
- Grapple actor hooks and runtime deployment.

Potential MSBT use:

- Reference only. The pak requirement and GPL license make it a poor fit for
  direct MSBT integration right now.

