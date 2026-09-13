# Native item cards: local implementation and remaining validation

The requirement remains game-style cards, names, details and calculations with BL4 closed. Gun models are out of scope. This is not yet a claim of complete card parity.

## Implemented locally

- Inventory weapon cards now host the original extracted Cohtml item-card HTML, CSS, scripts, fonts and art in isolated Chromium frames. The adapter supports the game bindings, rarity components, elemental components and color matrices. Chromium text outlines still use a compatibility approximation.
- Local assets are copied by `tools/game_ui_extract/package_card_assets.py`; their hashes are recorded in `electron_poc/native_card_ui/manifest.json`. No runtime game process or network request is needed to render a resolved card.
- Typed foreign parts and repeated parts remain ordered. Item roots follow only the host inheritance chain; compositions inherit their actual rarity.
- The calculator reads extracted Unreal table-struct defaults and float column types, native rarity scales and native attribute modifiers. Default modifiers are ScaleAdd, as confirmed by the extracted enum. Repeated ScaleAdd contributions are summed. Rarity stat scaling uses the native stat-to-attribute mappings, including inverted and additive stats.
- Native naming thresholds now produce Zealous Regulated Bubbles, Zealous Regulated Draupner, Zealous Extolled Ichor, Zealous Extolled Roulette, Debauched Vibrating Kitty and Accelerated Nadir Conflux. Missing core inputs and ambiguous licensed prefixes retain partial status.
- Pricing retains every repeated part and uses the host weapon price type. Very large prices cap at the native signed-integer limit represented as a float.
- Primary elemental damage uses the extracted status defaults and damage interval. Shock Bubbles matches the screenshot's 654 DMG/s and 10% chance; secondary elements and the other mixed-weapon elemental discrepancies remain unresolved.
- Max All's earlier scoped action and click fixes remain in place. No gameplay mutation was used in this validation.
- Successful Inventory reads now save raw serials and observed labels in the app's local data folder. Startup resolves the saved serials offline and labels the original player and capture time. Failed reads preserve the saved inventory; restore cannot overwrite a newer read or change the selected player.
- Inventory-wide and use-mode stat points are converted separately. The exact Shock Ichor serial was captured on 2026-09-13 at 19:23 UTC; its primary damage, radius, fire rate and accuracy impulse validate this distinction. Damage differs by less than one float ULP; radius matches the screenshot's 4,153 cm and DPS rounds to 6,569M. Exact large-number text formatting remains under validation.

## Evidence

`fixtures/item_cards/roulette_native_reference.json` contains only the serial and scalar BaseValue reference from the user's read-only game capture. Runtime current values contain player modifiers and are not silently substituted for offline item values.

The offline calculator matches captured Roulette base damage within 0.01, and fire rate, reload, charge, critical damage, accuracy impulse, spread and captured sway scales within 0.00001. Screenshot checks cover Bubbles/Draupner damage, fire rate, reload, critical damage, magazine abbreviation, splash radius and DPS abbreviation. Price rounding remains about 0.0003% off those screenshot prices.

Checks:

- `npm run test:native-card-inputs`
- `npm run test:native-card-render`
- `npm run test:item-cards`
- `npm run test:max-all`
- `npm run test:inventory-snapshot`
- Python syntax checks for the extraction and reference-capture scripts

The real renderer test loads the original card resources, checks the computed name and damage, validates frame sizing, and verifies that imported text cannot inject HTML. A visual inspection caught and fixed a zero-height frame-body clipping issue. It does not certify all displayed data.

## Still open

- Native selection, ordering and limits for mixed-part perk rows, red text, and elemental details. The current native layout still receives the previous resolver's provisional detail lists and shows an explicit validation notice outside the card.
- Draupner accuracy versus the screenshots. Ichor's new native reference resolves its damage/radius/DPS mismatch without serial-specific overrides.
- Full generic weapon behavior initialization, licensed-prefix conflicts, and exact price floating-point accumulation.
- Non-weapon numeric parity: shield augment values and grenade modifier-display semantics still need native references. Non-weapon names retain the existing resolver; ambiguous prefixes and missing rarity metadata remain unresolved.
- Full packaged-app and actual inventory validation. No version, release, tag or installer was published.

The extracted `OakWidgetData_ItemCard` struct confirms the original data-model fields, but `OakUIDataCollector_ItemCard` has no reflected data properties. Reading an equipped weapon's properties is therefore a useful calculation reference, not a capture of the game's finished card model.

## Equipment cards added after the 19:43 UTC capture

Inventory now uses the original layouts for shields, ordnance, repkits, enhancements and class mods, as well as guns. `native_equipment_card.js` follows the extracted UI-stat groups, labels, conditions, icons and argument maps, including full colored descriptions. Repeated class-mod tier parts add their points to native progress-graph nodes; the skill-tree data supplies original icons and hover names. A Chromium compatibility rule wraps more than three passive bonuses for modded items instead of clipping them off the sides. The game resources remain unmodified.

`native_equipment_defaults.json` contains scalar class-default values from the user's 2026-09-13T19:43:26Z read-only capture, with its source SHA-256. These initialize the non-weapon property contexts offline. They are not finished item-stat references. The resource bundle now contains 1,534 original files, with hashes and no missing bundle inputs.

The equipment calculation path displays capacity, segments, damage reduction, grenade damage/radius/charges/cooldown, healing, enhancement percentages and prices when available. Repkit total healing uses the sum of separately resolved initial and timed healing; the generic BalanceFormula evaluator's nonzero-offset semantics still require validation. No serial-specific numerical overrides were introduced.

Unresolved fields display an em dash and remain in `stats_blocked`: the supplied shield's Armor Segment/Missile Swarm augment values, and grenade UI-stat requests for native modifier accumulators. Those modifier displays must not use final damage as a percentage. Mixed-part row selection, names, rarity and red-text selection are still provisional; this is not complete game parity. The supplied repkit fixture has no explicit rarity source, for example. No gun calculation was changed by this equipment patch.

Validation: `test:native-equipment-cards` resolves all five supplied fixtures with no running-game dependency, checks healing aggregation, enhancement argument substitution, repeated class-mod ranks and unresolved-value handling, and paints each through the real Inventory renderer. It verifies native resources, visible pixels, no unresolved text arguments and no sideways clipping of skill ranks. Screenshots were visually reviewed under `_tmp_native_card_preview/equipment-*.png`. Existing native gun inputs/rendering, item-card naming/rendering and saved-inventory tests passed. Python reference/extraction script syntax passed. Live item numeric comparisons and packaged-installer validation remain open.
