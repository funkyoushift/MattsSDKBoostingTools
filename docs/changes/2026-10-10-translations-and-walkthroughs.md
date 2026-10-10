# Translation coverage, Australian copy and task-layout walkthroughs

Martin requested the remaining translations, humorous Australian wording on every page, and walkthroughs updated for the new layout. Local source work only; no version bump, package publication or game mutation.

## Findings and changes

- The existing DOM translator supported the whole desktop/mobile interface, but newer labels and tutorial copy were absent. The embedded Matt Editor did not load the translation runtime. Added 932 supplementary translation entries, reviewed Mayhem/repair-kit/loot-roll terminology, and compiled 3,838 catalog entries for Spanish, French, Brazilian Portuguese, German, Dutch and Australian English. The five-language maintenance draft used the existing translation tool with public interface strings only; these are not native-speaker certification.
- Australian copy now has 345 authored entries, with distinct wording for all 40 task pages, categories, major controls, editor tabs and guide headings. Proper names, contributor attribution, item names, serials, user values and game data retain their spelling. App-level explicit Australian opt-in remains.
- Added the shared runtime to the embedded editor and synchronized language over a parent/frame message handshake, accepting only the expected frame/parent. Static editor options are marked as interface text; dynamically populated item/part options remain data. Editor lookups that read backpack/lost-loot/type headings now use original text. Placeholder serial examples and unknown multiline text retain their exact source formatting.
- Inline player options explicitly preserve names, including a player named `Save`; mirror selectors use original labels to avoid retaining a previous language. Sidebar group matching uses original text rather than translated labels. Added an explicit AFK Mayhem translation row.
- Replaced workspace main/layout walkthroughs with task pages, sidebar/search/Back, nearby targeting, Mayhem, AFK item handoffs, and App settings. Classic retains its panel-layout guide. Hidden Dev Spawner/layout-toolbar tour targets now point to visible workspace headings. Target preparation opens relevant pages and enclosing disclosures; Back has a language-independent ID.
- Tutorial copy carries layout revision 2 through the catalog loader. Older cached copy cannot overwrite the new workspace instructions. New overlay tour IDs use `workspace-` names, so already-released apps ignore them instead of applying the new step order to old targets. Only title/body are accepted; selectors/actions remain local. Updated the bundled tutorial manifest hash/size without publishing a data release.

## Components

Desktop language files (`ui_language_additions.json`, `ui_language_australian.json`, `ui_language_preserved.json`, generated catalog, `ui_i18n.js`, `ui_localization.js`); shared mobile/editor copies; editor HTML and three original-text lookups in `item-editor-10-yaml-save.js`; `workspace.js`, `workspace_targets.js`, new `workspace_walkthroughs.js`, renderer integration; `remote_data_catalogs.js`; tutorial JSON/manifest; compiler and focused test scripts/package test commands.

## Validation

- `npm run test:languages`: passed. Seven locales, live text changes, reload persistence, placeholders, untouched controls/serials, desktop/mobile shared catalogs, and cross-origin editor handshake/data protection.
- Page coverage: 2,703 observed strings including hidden dialogs and walkthrough text; zero unexplained missing translations. The remaining 85 inventory entries are documented contributor/product names or literal diagnostics. All 40 route headings/navigation labels checked in all seven locales. German/Australian pages checked at 360, 800 and 1,360 px without document overflow. This does not translate unknown remote errors or game-supplied content.
- `test_workspace_walkthroughs.js`: 321 target checks (107 targets in English, German and Australian), Next/Back/Skip/replay, stale-copy rejection, compatible revision-2 overlays, selector allowlist, and zero game actions passed. Classic 107-target and 12-step AFK checks also passed.
- `test_editor_language_sync.js`: loaded actual editor over a separate local origin; all seven languages propagated; names, codes, input/selection/save values unchanged; messages from an unexpected source rejected.
- `test_player_roster_refresh.js`: joins/leaves/reindexing, stable options and focus, named-target isolation, translated-name protection, offline/reconnect polling passed. Its old fixture removed the entire body and broke new workspace reconciliation; fixture now keeps app controls and uses an isolated focus surface.
- Full `npm run check` passed after restoring the missing ignored oak2 test archive from the verified 2.35.1 worktree. Initial failure was missing test setup, not an installer regression. Includes 588 responsive measurements, window/layout checks, offline installation, AFK and password checks. Log: `output/languages/final-desktop-check.log`.
- Remote catalog suite: 11/11 passed, including manifest integrity, cache refresh, title/body-only overlays and compatibility with old tour maps. Python syntax, JavaScript syntax, diff whitespace checks and five Quick Menu/bridge startup regression checks passed.
- Australian screenshots captured under `output/languages/australian-*.png`; combat layout visually checked. No live gameplay retest, installer build or physical-phone installation claimed.

## Preview, release and rollback

Stopped only the installed MSBT desktop processes and launched `npm start` from this product checkout; source preview process confirmed. Borderlands was not stopped or modified. The public v2.35.1 release is unchanged. Current product metadata remains at its prior version, and unrelated dirty work is preserved. Before a separately authorized release, integrate these UI files onto the current published baseline; do not publish this checkout wholesale. Close the source preview and reopen the installed MSBT app to return to the published UI. Translation maintenance uses `build_ui_language_catalog.py`; a new Australian key must already have the other language entries instead of silently creating English fallbacks.

## Authorized release preparation

Martin requested release. Integrated only the listed UI/editor/shared language sources onto published v2.35.1 in the isolated release worktree, on codex/translations-release-2.35.2. Windows/SDK metadata advances to 2.35.2; SDK gameplay code is unchanged. Android APK remains 1.6.2; updated mobile translation sources are not claimed as installed or published in a new APK. Physical device testing remains pending. Windows packaging and publication checks pending.
