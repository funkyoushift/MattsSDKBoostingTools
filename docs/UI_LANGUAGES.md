# Interface languages

The desktop and Android controller bundle English, Spanish, French, Brazilian Portuguese, German, and Dutch, plus an optional **Australian slang (explicit)** English variant. The selected language is kept in localStorage under `msbt.ui.language.v1`. No translation requests run inside the app. Australian slang is never selected automatically by the device's region.

`ui_i18n.js` retains the explicit AFK translations. `ui_language_catalog.js` covers the wider interface. `ui_localization.js` translates text nodes and accessible attributes without replacing controls or modifying values. It tracks English originals for app logic and restores English when selected. New interface nodes are translated by a mutation observer. User-folder lists, player selectors, item cards, serial fields, and logs are excluded. Game-provided text and embedded third-party pages are not translated.

Translations started as an automatic pass. Navigation corrections live in `ui_language_overrides.json`; the game-context wording review lives in `ui_language_context.json`. The complete catalog has not been reviewed by native speakers. Keep variables and product identifiers unchanged. Add new user-data regions to the exclusion list before rendering them.

## Context review

The review corrects 391 exact English phrases across all five translations. Each record supplies complete translated phrases, with exact aliases where their meaning is identical. Do not do runtime word replacement: the same English word can mean different things in different controls.

Examples verified against the UI/action wiring:

- Max All is an action to maximize values; Max Step Height is a numeric upper limit. Max Spec means specialization, not a hardware specification.
- Party is a player group. Kick removes a player from the lobby. Free For All means everyone fights everyone, not that something is free of charge.
- Serial means an item code. A loot pool is a collection of possible items, not a swimming pool. Community drop lists are item collections, not dropdown menus.
- Spawn creates a game entity. Actor means a game object/entity, not a performer. Leg/Epic expands to legendary/epic. Hoard is the enemy-wave tool, not storage of possessions.
- Instant Drops and Instant Holds remove hold-to-confirm delays (`instant_click_holds.py`). They do not create loot or lock anything.
- The mobile Toggle Selected button calls `movement_infinite_jump_toggle_selected`; it toggles infinite jumping for the selected players, not checkbox selection.
- Zero Vault Cooldown calls `zero_vault_power_costs_all_players` in `movement_adjustments.py`. The translated description refers to obstacle-traversal costs, not a bank vault or a promise about an unrelated cooldown.
- Stagger in the wave editor is the delay between spawn batches. Pin saves an action to Quick Menu. Apply activates settings; it is not a job application.

`ui_language_australian.json` is deliberately profane, user-requested comic wording (154 exact phrases), not a claim about how all Australians speak. Unlisted labels, technical errors, and detailed warnings retain English. Max All becomes “Boost these cunts”; neither the action identifier nor its behavior changes. Codes, custom names, player identities, logs, and user data remain excluded. Switching away restores regular language text. The explicit AFK labels use the same reviewed catalog entries to avoid terminology drift.

## Validate

Run `npm run test:languages` in electron_poc. It covers all seven choices on both UIs, dynamic text and numeric templates, original-text access, controls and callbacks, user data, 360/800/1920 widths, and reload persistence, including Australian slang. Context regressions check Max All, Apply, Kick, Free For All, and Leg/Epic. Desktop and mobile copies must match byte-for-byte. These are offline UI checks; they do not claim live game or APK verification.

Desktop/mobile AFK tests pass separately. The existing `test_bookmark_folders.js` fails at `move` in both the release baseline and this branch; this was reproduced independently of localization.

## Maintain the catalog

From the repository root:

1. `npm install --prefix output/languages/tooling acorn --no-audit --no-fund`
2. `node tools/extract_ui_language_strings.cjs`
3. `python tools/generate_ui_translations.py` (explicit online maintenance step; public UI strings only, cached under output/languages).
4. Review wording in `electron_poc/ui_language_overrides.json` and `electron_poc/ui_language_context.json`.
5. `python tools/build_ui_language_catalog.py --from-cache` validates variable placeholders and synchronizes desktop/mobile assets. For wording-only edits, omit `--from-cache` to reuse the committed base catalog entirely offline; no output caches or translation service are needed.
6. Run language and relevant UI tests.

Do not ship output caches. New APK packaging is required to deliver these files to Android users. No native in-game menu translations or gameplay changes are included.
