# Native model to widget bindings

Steam build 25372571, Borderlands4.exe SHA256
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
This documents recovered field bindings, not a completed UI implementation.

## Reflected destination structure

Read-only SDK query `output/local-card-resume-20261003/sdk_card_structs.py`
exports `OakWidgetData_ItemCard` and its HUD derivative. Both have size 1544
(0x608). `sdk_card_structs.json` records field names, offsets, types and sizes.
This structure is distinct from the native model created by 56D3CCA.

The existing complete disassembly at
`output/card-native-recovery/stat-collection-discovery/functions/011fc6ba.asm.txt`
uses RSI for that widget, and `[R15+10]` for the native model.

| Model source | Widget destination | Name | Copy evidence |
| --- | --- | --- | --- |
| B8 | 238 | Name | 11FCAD0..11FCB3B |
| 468 | 250 | ItemType | 11FCC0B..11FCC34 |
| F0 | 268 | ItemBaseType | 11FCC46..11FCC6E |
| 120 | 2B0 | RarityIdent | 11FCB45..11FCB6C |
| 498 | 318 | RarityColor | 11FCB82..11FCC01 |
| 140 | 280 | ManufacturerName | 11FCE9D..11FCF1C |
| 170 | 298 | Manufacturer | 11FCF26..11FCFA5 |
| 4B0 | 570 | Price | 11FCFAF..11FD038 |
| 190 | 3D8 | DamageType1 | 11FDFAC..11FE006 |
| 1A8 | 3E8 | DamageType2 | 11FE010..11FE06B |
| 568 | 418 | SecondElementText | 11FE416..11FE492 |

ItemType, ItemBaseType and RarityIdent pass through 4A20B80. Its original
instructions at 4A20BD4..4A20BEF change only UTF-16 Aâ€“Z to aâ€“z; JavaScript's
general Unicode lowercase operation would not reproduce that rule.
Level uses the integer at model+44 and a separate localized LevelTextFormat
path (11FCC8F..11FCE1C). `level_raw` is explicitly not the final localized text.

## Arrays and singleton headline

Groups 0, 1 and 2 go to Primary_Stat_Entries (+338), Secondary_Stat_Entries
(+358) and Tertiary_Stat_Entries (+378). The normal owner constructor
58CF8C4..58CF9AF writes **4** to owner+2E8 at 58CF92F. Owner allocation is
0x398 (58CF890..58CF8C4). 11FD83B..11FD866 caps the already converted
secondary array using that owner value. This proves the constructor default;
it does not prove all owner instances keep that value in every context.
When `abbreviated` (+C8) is true, the secondary group is suppressed before
conversion (11FD684..11FD691). Tertiary and other groups have separate paths.

Group 7 is different: 11FDE75..11FDE79 passes its **first source row directly**
to E69D1A for Headline (+1B8). It does not use E69A30's visibility/empty-array
filter. The readers now export `first_ui_row` for this group separately.
Never derive the singleton by taking the first filtered array row.

Owner hashes and disassembly: `native-widget-owner/evidence.json`.
String conversion and array resize hashes: `native-widget-string-copy/evidence.json`.

## Price lifecycle gap and recovered completion

Construct/bind/fill alone leaves Price empty. Default card owner code separately
gets the native stat-container monetary value (+40), formats it through the
unsigned 5C4B4F8 path, and copies the FString into model+4B0. See
PRICE_ARITHMETIC.md for arithmetic, source selection, and exact instructions.

`serial_token_oracle.py --card-price` executes 5FE64DB..5FE652D including
the original temporary ownership cleanup and its 5FE667B..5FE66A4 branches.
It supplies the native container's int32 bits, without Python arithmetic or
localized string formatting. The entire containing function 5FE61C8..5FE68DD
is pinned to SHA256
`aea1feab503366ec5211d7969309c89dca2580b1f24ba43bbf7051ccdba7527b`.

`native-widget-price-selected-offline-20261004.json` replays saved runtime
pages without game process access. Its price is **533,370,848**, matching the
independent selected sniper screenshot. The earlier detached live probe did
not include this price step. Do not describe it as complete card-field parity.

`native-widget-price-ten-offline-20261004.json` completes this step for all ten
fixtures, including two native unsigned overflow displays of `2,147,483,648`.
No failures were recorded. `native-widget-price-cache-selected-20261004.json`
additionally checks that the already initialized identity+90 cached container
has the same monetary bits as the independently constructed native container.

The guarded live probe then ran with `include_price=True`. It calls the same
formatter, FString accessor and copy function, checks the returned owned text's
vtable against 9E12790, and invokes its recovered release at 4774916. It never
decrements shared reference counts in Python. The six additional function hash
gates are in `PRICE_GATES`; disassembly is saved in `native-price-lifetime/`
and `native-price-release/`.

`live-sdk-widget-price-verification-20261004.json` records exact equality with
offline strings, display groups (including singleton headline), and all twelve
widget source fields. Price text release, model destruction and identity
destruction completed. The recorded 43.6 ms includes repeated journal writes
and export; it is not a pure native-engine benchmark. All seven equipped and
63 backpack serials retain exact multiset equality. AFK was restored from its
saved configuration (`afk-restored-after-widget-price-20261004.json`).

## Remaining boundaries

The new `widget_sources` export retains original string case and empty values.
It is not a renderer-ready object. Primary element text composition, firmware
count/transferred-state/loadout behavior, localized level text, banners and all
context-dependent row limits still need their complete native consumer paths.
No missing field may be filled using the old inferred renderer as a fallback.


## Full final-widget execution, 2026-10-04

Steam build 25372571, executable SHA256
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
The pipeline now executes the original final consumer instead of manually
reimplementing its display bindings. The SDK creates and releases reflected
OakWidgetData_ItemCard storage (0x608 bytes); captured default bytes are all zero.
The native owner occupies 0x398 bytes. Its constructor is 58CF8C4..58CF9AF,
consumer 11FC6BA..120184B, and inner destructor 575204C(owner, 0). Exact hashes
are in WIDGET_GATES in native_sdk_widget_probe.py; function disassembly and
receipts live under output/local-card-resume-20261003/native-widget-*.

A separate initialization method, 167376E..1673F0E, is essential: it populates
type-label and skill-tree maps used by 16193F4..1619A12. Passing a null UI object
is supported by the early return in base initializer 10C71FE..10C7B09. Omitting
this initialization caused missingicon and unresolved class-mod skill names.
Executing it resolved both tested class mods, including the 102-entry Ruinous
Assimilator. This is recovered executable behavior, not an item-specific fix.
The returned skill display name is in the row ident field, while label remains
the native progression reference. The extracted HTML consumes the fields as-is.

The no-comparison path uses an independently initialized empty native identity
(B95EC6..B95F28, tail B95F28..B95FE1) rather than changing comparison markers
in Python or JavaScript. Both ranges are hash-gated for live calls. All ten
full final-widget payloads match offline versus live, joined by exact original
serial (fixture ordering differs). Owners, SDK widgets, comparison identities,
models and item identities were released. Timings 65.1-122.1 ms include diagnostic
export and journal writes, not just engine execution. Inventory exact multisets
remain 7 equipped and 63 backpack. Receipts:
- native-widget-no-comparison-ten-20261004.json (saved-page replay)
- live-sdk-standalone-0..9-20261004.json
- live-sdk-standalone-verification-20261004.json
- afk-restored-after-standalone-widget-20261004.json

Firmware: the first raw group-4 row is converted independently; model+4D0 is
FirmwareTransfered. The model+580 map supplies native loadout counts. The current
standalone pipeline intentionally supplies no player loadout, so its counts are
not an equipped-loadout preview. Player-context recovery remains unresolved.

The new native_widget_card_model.js is transport only: it copies native strings,
flags and row order into extracted template properties and maps asset paths.
It never calls the previous naming/stat resolver. Missing assets, missing fields,
and unsupported visible glyphs fail explicitly. The card image still uses
Chromium compatibility code for the extracted Cohtml layout. Native model equality
does not establish pixel-perfect rendering, every language, input glyph support,
multiplayer safety, or general lifetime safety.


## Chromium layout boundary verified against game UI, 2026-10-04

The installed extracted item_card.html SHA256 is
34232b1538d0199ac27e1c2ce3a7e2bd6509f190dc9ed778b6e4b3260649846a;
item_card.css SHA256 is
00ad72dce1288d3bc83d765f143f9724b82d4b372ec89dcde39355e0c5710b59.
Both still match native_card_ui/manifest.json. Primary row value binding is
plain text (HTML line 248), with coh-font-fit-mode: shrink (CSS line 219).
BL4 Weapon Slot 2, Sent Poor Man's Divided Focus, independently showed the same
modded enhancement descriptions in the primary stat cells at 119k DPS; the game
shrinks their plain bracket text. Chromium does not implement this property,
so exact font-fit behavior remains unresolved. Do not change native rows or
expand markup in data-bind-value to conceal the engine difference.

The installed Release cohtml.WindowsDesktop.dll SHA256 is
6b2a7ae5724511301418a347288795d11fbb48bd844b387aa5f574697f5e676b.
Development SHA256 is
7a9af094b0d62c792ee66ad8e7f3e0e428ac1650a84ef791dfa80858943e0cf6.
Read-only export inventory (295 exports each) is in the research receipt
cohtml-installed-exports-20261004.json. Export inspection alone does not establish
an ABI, prove the loaded variant, recover font-fit logic, or authorize a guessed
DLL call. No DLL initialization or fabricated layout rule was introduced.
