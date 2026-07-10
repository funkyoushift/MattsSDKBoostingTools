# Matt Editor Cross-Builder Comparison

## Purpose

This report follows the Matt editor integration plan after the delivery preview and target-selector work.

Goal: compare the current MSBT Python Legit Builder path with the hosted Mattmab editor path before moving more item-making logic.

## Current Integration State

The hosted Mattmab editor is now exposed from the external app as an advanced editor entry point.

Current MSBT boundary:

- Python/Tkinter app opens and hosts the editor.
- `matt_editor_host.py` serves the editor and local API routes.
- `matt_editor_adapter.js` injects the MSBT delivery panel.
- Live delivery still goes through `give_serial_selected`, `give_serial_all`, and `give_serial_nonhost`.

Important adapter behavior:

- `window.MSBT_MATT_EDITOR_ADAPTER_VERSION = "deliver-4-target-selector"`
- The adapter scans known output fields for exactly one `@U` serial.
- The user must confirm the serial before delivery.
- Selected-player delivery requires an explicit target from the editor panel.
- `/msbt/deliver` rejects empty, stale, multi-line, or multi-serial payloads.

## Strict Python Builder Path

Primary file:

- `external_app/v22_parts_codes_fixed/external_legit_builder.py`

Important functions:

- `roots()`
- `slots(root_key)`
- `slot_counts(root_key, selected)`
- `search_parts(root_key, text, table, limit)`
- `is_part_allowed(root_key, selected, candidate, table)`
- `validate(root_key, selected)`
- `build_human(root_key, selected, level, seed, seed2)`
- `build_base85(root_key, selected, level, seed, seed2)`

The Python builder is deterministic:

1. Pick one root key.
2. Pick compact selected part lines such as `inv_comp:comp_05_legendary_zipgun`.
3. Validate selected lines against strict slot/tag rules.
4. Sort selected parts into canonical slot order.
5. Emit human serial.
6. Convert human serial to Base85 with local serial conversion.

Smoke-tested strict sample:

Root:

- `dad_ps`
- Daedalus Pistol

Selected compact parts:

```text
inv_comp:comp_05_legendary_zipgun
body:part_body
body_acc:part_body_a
barrel:part_barrel_01_zipgun
magazine:part_mag_01
scope:part_scope_ironsight
grip:part_grip_01
```

Validation:

```text
ok: true
errors: []
warnings: []
```

Human serial:

```text
2, 0, 1, 60| 2, 1534|| {54} {2} {3} {1} {13} {25} {42}|
```

Base85:

```text
@Uga`vnFnkbU{4Y>DRG/(vs7=j5)j/L
```

## Hosted Matt Editor Path

Primary files:

- `external_app/v22_parts_codes_fixed/matt_editor/index.html`
- `external_app/v22_parts_codes_fixed/matt_editor/js/legit-builder/legit-builder.js`
- `external_app/v22_parts_codes_fixed/matt_editor_host.py`
- `external_app/v22_parts_codes_fixed/matt_editor_adapter.js`

Important editor output fields:

- `mi_finalOutputString`
- `mi_finalOutputBase85`
- `finalOutputBase85`
- `serializedOutput`
- `bulkSerialOutput`

Important Matt editor implementation points:

- The advanced/modded builder is browser-state driven.
- It has separate Modded Item Builder and Legit Item Builder surfaces.
- It preserves parsed/deserialized token order for modded rebuild workflows.
- It tracks selected parts in browser state and DOM slot rows.
- It can serialize human output through the local `/api.php` shim served by `matt_editor_host.py`.
- It includes relaxed modded tooling such as missing/raw token preservation, cross-manufacturer sections, and passive quantity expansion.

Notable functions/logic in `legit-builder.js`:

- `formatDeserializedPartToken(...)`
- `updateFinalOutput()`
- `serializeToBase85(...)`
- `copyBase85Output(...)`
- `copyModdedSerializedOutput(...)`
- `expandModdedMiLineToPartKeys(...)`
- `mergeConsecutiveRootPairTokensToArrayTokens(...)`
- `normalizeConsecutiveRootPairTokensInModdedHumanLine(...)`
- `buildMiCrossManufacturerSectionHTML(...)`
- `miInitOpenModdedPickers(...)`

## Key Differences

### 1. Input Model

Python builder:

- Starts from a known root key.
- Uses compact selected part rows.
- Requires slot legality before normal build output.

Matt editor:

- Can start from a pasted existing Base85/human serial.
- Can rebuild from token streams.
- Can preserve unknown or missing tokens that are not in the dataset.

### 2. Ordering

Python builder:

- Canonicalizes part order by root slot order, dependency index, serial, and key.
- Good for strict predictable builds.

Matt editor:

- Preserves modded/deserialized token order where possible.
- This is better for experimental/modded item editing, where token order can matter.

### 3. Legality Meaning

Python builder:

- Strict mode means "this matches MSBT local legit rules."
- Unlocked mode loosens constraints, but it is still organized through the strict builder model.

Matt editor:

- Has a richer relaxed editing model.
- Better for "known working but not strictly legit" item construction.
- Better place for experienced item makers who want cross-root/cross-manufacturer or imported-token workflows.

### 4. Serialization Boundary

Both paths now use local serial conversion.

Python builder:

- Calls local Python conversion directly.

Matt editor:

- Calls browser-side API routes.
- MSBT host rewrites those calls to local `matt_editor_host.py`.
- `matt_editor_host.py` calls the same local serial conversion helpers.

### 5. Delivery Boundary

Both paths should converge only at final confirmed `@U` serial delivery.

Python builder:

- Sends generated Base85 through the existing bridge actions.

Matt editor:

- Adapter confirms exactly one final `@U` serial, then sends it through the same bridge actions.

## What We Should Not Do

Do not copy large Matt editor browser systems into the Python Legit Builder yet.

Reasons:

- The Matt editor logic depends heavily on DOM state.
- Its modded builder behavior is more than a list of allowed parts.
- Pulling isolated functions into Python could lose ordering, missing-token, and UI-state assumptions.

Do not make the strict Python builder mean "anything that might work in game."

The strict builder and advanced modded editor should stay separate:

- Python Legit Builder: strict, predictable, rules-driven.
- Matt Editor: advanced, imported/modded/experimental, token-aware.

## Next Recommended Step

Add a real cross-builder fixture/test harness before porting more item logic.

Current harness:

```powershell
C:\tmp\msbt-python-3.12\python.exe .\tools\matt_editor_cross_builder_check.py
```

This checks the strict Python builder output, starts the local Matt editor host, verifies the editor bootstrap/adapter injection, and confirms the hosted `/api.php` route serializes/deserializes the same fixture.

Recommended fixture:

1. Keep the Python `dad_ps` sample above as the strict baseline.
2. Open the hosted Matt editor.
3. Build or paste the same human serial:

```text
2, 0, 1, 60| 2, 1534|| {54} {2} {3} {1} {13} {25} {42}|
```

4. Confirm the editor serializes it to:

```text
@Uga`vnFnkbU{4Y>DRG/(vs7=j5)j/L
```

5. Confirm the MSBT delivery panel detects that exact serial.
6. Confirm changing editor inputs marks the confirmed serial stale.
7. Repeat with one class mod and one known Crayons/modded item.

After those fixtures exist, the safest feature work is:

- improve the Matt editor entry point and wording if users still miss it,
- add "Import to Serial Bookmarks" from the Matt editor adapter,
- then add observed-working part data to the advanced editor path, not the strict Python builder.

## Current Conclusion

The current integration boundary is correct.

Use the Matt editor as the advanced modded item-making surface. Keep Python Legit Builder strict. Share only final confirmed serial delivery and carefully chosen resource/fixture knowledge between them.
