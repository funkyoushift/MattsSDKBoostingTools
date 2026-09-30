# Interface languages

The desktop and Android controller bundle English, Spanish, French, Brazilian Portuguese, German, and Dutch. The selected language is kept in localStorage under `msbt.ui.language.v1`. No translation requests run inside the app.

`ui_i18n.js` retains the explicit AFK translations. `ui_language_catalog.js` covers the wider interface. `ui_localization.js` translates text nodes and accessible attributes without replacing controls or modifying values. It tracks English originals for app logic and restores English when selected. New interface nodes are translated by a mutation observer. User-folder lists, player selectors, item cards, serial fields, and logs are excluded. Game-provided text and embedded third-party pages are not translated.

Translations are automatically generated, with manually reviewed navigation terminology in `ui_language_overrides.json`; the complete catalog has not been reviewed by native speakers. Keep variables and product identifiers unchanged. Add new user-data regions to the exclusion list before rendering them.

## Validate

Run `npm run test:languages` in electron_poc. It covers six languages on both UIs, dynamic text and numeric templates, original-text access, controls and callbacks, user data, 360/800/1920 widths, and reload persistence. Desktop and mobile copies must match byte-for-byte.

Desktop/mobile AFK tests pass separately. The existing `test_bookmark_folders.js` fails at `move` in both the release baseline and this branch; this was reproduced independently of localization.

## Maintain the catalog

From the repository root:

1. `npm install --prefix output/languages/tooling acorn --no-audit --no-fund`
2. `node tools/extract_ui_language_strings.cjs`
3. `python tools/generate_ui_translations.py` (explicit online maintenance step; public UI strings only, cached under output/languages).
4. Review important wording in `electron_poc/ui_language_overrides.json`.
5. `python tools/build_ui_language_catalog.py` validates variable placeholders and synchronizes desktop/mobile assets.
6. Run language and relevant UI tests.

Do not ship output caches. New APK packaging is required to deliver these files to Android users. No native in-game menu translations or gameplay changes are included.
