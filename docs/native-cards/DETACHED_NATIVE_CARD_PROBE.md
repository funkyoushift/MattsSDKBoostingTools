# Detached native item-card probe

Status on 2026-10-04: native model construction, binding, group filling, UI row
conversion and destruction run offline on ten captured serials. This is research, not a finished
SDK preview API, replacement renderer, or release claim.

## Installed-game evidence

Steam build 25372571, Borderlands4.exe SHA256
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.

Executed original functions:

| Function RVA | Purpose | Function SHA256 |
| --- | --- | --- |
| BB157C | Detached item identity to ordered evaluated groups | 5f4e6c144fbfafab8cf3a6a78a243e4e6ddfa58bd83b2aa8bcba9556ddd9d357 |
| BB299E | Stat evaluation, including 3D9E604 callback | ba72b9bc63d35c990bde1d9083349755b65b38c2773f88151cddc324a8ae7f4b |
| 3DAC149 | Static initializer containing cache span 3DAC4D7..3DAC505 | 4d714bad7f3746a562d262b992540b86c16c3d22cbeaee2dce355f24b445a749 |
| BB0AC0..BB0EFB | Display-row projection, completed with fresh pages | 1dde1dba26c1290d69e4e5cf26bb75a35fc0350928287919632aaf622ac264f9 |

`serial_token_oracle.py --card-groups --cold-card-cache` constructs a detached
identity and calls BB157C with R8=0. The cold-cache option executes the original
initializer span in emulator memory only, with its established live-in registers.
It does not clear the game's cache. Game logic hooks remain empty. Allocations
and bounded CRT operations are serviced locally; actual Windows CRT functions
and their library hash are recorded in each report.

The ten-category run recovered 408 rows and 533 evaluated fields: 408 Value,
108 label, 17 Description. Categories include pistol, sniper, shotgun, assault
rifle, SMG, heavy ordnance, grenade, shield, repkit, and class mod. Names are native
fragments, not proof of the final localized joined name. The reader preserves
FName bytes, decoded names, flags, definition identities, and native ordering.

Fresh captures came from process 60916, thread 60768. The later named-field run
uses saved pages with `process_access: none`. Runtime pages from another PID are
rejected when the saved thread context identifies a different process.

Reports in research `output/local-card-resume-20261003/`:

- `native-detached-categories-20261004.json`: original ten-category success.
- `native-detached-named-keys-20261004.json`: offline replay, zero item failures.
- `native-row-comparison-20261004.json`: 345 matching, 13 different, 158 missing
  Value/label fields against the current local resolver. Missing includes groups
  the weapon resolver does not expose, not necessarily visible missing UI.
- `native-display-one-20261004.json`: explicit further-projection failure at
  RVA 5EC89, requiring uncaptured page 4F48F000. No invented page or fallback.

## Display binding and remaining work

BAFCD3..BAFCE9 zeroes an E0-byte destination then calls BB0AC0 with the source
96-byte stat row. The optional `--card-display-rows` probe reproduces that call.
BB0AC0 copies evaluated fields into +8, +38, +68 according to runtime FNames at
CBCD860/868/870, then applies definition-dependent description composition.
It also copies priority, flags, and asset references. Source is the extracted
`card-display-row-binding/00bb0ac0.asm.txt`, with the hash above.

The missing-page failure above is historical. Fresh read-only capture from
process 42580/thread 40096 resolves it. `native-ui-ten-20261004.json` completes
all ten model builds: 510 display rows, 462 converted UI rows and ten destructors.
See [native UI projection](NATIVE_UI_ROW_PROJECTION.md) for further function
receipts, original-instruction boundary tests and the exact-zero presentation
fix. The ten-item model fixture contains two SMGs; do not describe that run as
ten distinct categories.

Before live SDK integration, establish final owner-context group selection,
asset-reference ownership and thread/lifetime boundaries. Native construction,
joined names and destruction now execute offline, but that does not prove live
safety or independent selected-card parity.
Do not insert a preview item into inventory or run an unproven function in the
game. An SDK adapter should ultimately feed immutable card data to the existing
desktop renderer and cache by original serial plus relevant build/context;
this proposed adapter is not implemented or performance-tested yet.

The preceding paragraph describes the earlier offline checkpoint. Subsequent
guarded live research now completes twelve detached previews, one including
the separately recovered price path. See NATIVE_UI_ROW_PROJECTION.md and
NATIVE_WIDGET_FIELD_BINDINGS.md for exact evidence and remaining limitations.
This does not implement the production adapter or prove sustained live safety.

The standalone micro-game idea remains unnecessary to test this path: the
original installed-game builder already yields evaluated card strings. The
offline harness is a research instrument and its speed is not an estimate of
SDK latency, nor is it a distributable replacement for the installed game.
