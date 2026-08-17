const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(path.join(__dirname, "panel_layout.js"), "utf8");

assert.match(source, /const WIP_NAV_UNLOCK_KEY = "msbt\.navTabs\.wipUnlocked\.v3"/);
assert.match(source, /localStorage\.getItem\(WIP_NAV_UNLOCK_KEY\)/);
assert.match(source, /localStorage\.setItem\(WIP_NAV_UNLOCK_KEY/);
assert.doesNotMatch(source, /localStorage\.removeItem\(WIP_NAV_UNLOCK_KEY\)/);
assert.match(source, /loadWipUnlockedNavTabs\(\);\s*const state = loadNavTabsState\(\)/);
assert.match(source, /const COLS = LEGACY_COLS \* GRID_SCALE/);
assert.match(source, /const CELL_HEIGHT = LEGACY_CELL_HEIGHT \/ GRID_SCALE/);
assert.match(source, /migrateSavedGridResolution\(parsed\)/);
assert.match(source, /gridColumns: COLS/);
assert.match(source, /cellHeight: CELL_HEIGHT/);

// Panel tiles are authored in legacy 12-column units, so the scaled grid must
// stay a whole multiple of them or default placements shift on screen.
const scaleMatch = source.match(/const GRID_SCALE = (\d+)/);
assert.ok(scaleMatch, "GRID_SCALE must be a literal integer");
const gridScale = Number(scaleMatch[1]);
assert.ok(gridScale >= 1 && Number.isInteger(gridScale), "GRID_SCALE must be a positive integer");
assert.strictEqual(72 % gridScale, 0, "legacy 72px row must divide evenly into the snap step");

// GridStack only ships 12/1-column CSS; anything else needs generated geometry.
assert.match(source, /function ensureColumnCss\(columns\)/);
assert.match(source, /ensureColumnCss\(COLS\);/);
assert.match(source, /gs-\$\{cols\} > \.grid-stack-item\[gs-w="/);
assert.match(source, /gs-\$\{cols\} > \.grid-stack-item\[gs-x="/);

const styles = fs.readFileSync(path.join(__dirname, "styles.css"), "utf8");
assert.match(styles, /--msbt-grid-cell-height/);
assert.match(styles, /--msbt-grid-major-cell-height/);
assert.match(styles, /msbt-grid-snap-visible/);

function cssRuleBody(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches = Array.from(styles.matchAll(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`, "g")));
  assert.ok(matches.length, `missing CSS rule for ${selector}`);
  return matches[matches.length - 1][1];
}

// Dev Spawner's fixed page and the fixed-page tabs render outside .msbt-panel-body,
// so they must share the scaled --ui-* sizes or View -> Text size skips them.
const scalingScope = styles.match(
  /\.msbt-panel-body,\s*\.dev-spawner-fixed,\s*\.fixed-page-tab\s*\{([^}]*)\}/
);
assert.ok(scalingScope, "content text-scale scope must cover fixed shells");
assert.match(scalingScope[1], /--ui-body-size:\s*calc\(12px \* var\(--msbt-text-scale/);
assert.match(scalingScope[1], /--ui-small-size:\s*calc\(10px \* var\(--msbt-text-scale/);

assert.match(styles, /\.dev-spawn-button,\s*\.dev-actor-label,\s*\.dev-row-actions button\s*\{\s*font-size:\s*var\(--ui-body-size/);
assert.match(cssRuleBody(".dev-actor-key"), /font-size:\s*\.86em/);
assert.match(cssRuleBody(".dev-actor-meta"), /font-size:\s*\.82em/);
assert.match(cssRuleBody(".inv-item-name"), /font-size:\s*var\(--ui-body-size/);
assert.match(cssRuleBody(".inv-item-meta"), /font-size:\s*var\(--ui-small-size/);

// Every multi-select list shares the loud --select highlight so a picked row is
// obvious, and the token stays separate from --red used by destructive controls.
assert.match(styles, /--select:\s*var\(--ui-select/);
[
  ".inv-item-card.selected",
  ".dev-actor-row.selected",
  ".bookmark-row.checked",
  ".bl4-code-card.checked",
  ".hoard-actor-pick.selected"
].forEach((selector) => {
  assert.match(cssRuleBody(selector), /var\(--select/, `${selector} must use the shared selection accent`);
});
// Check badges keep the selection readable when rows are dense.
assert.match(cssRuleBody(".inv-item-card.selected::after"), /content:\s*"✓"/);
assert.match(cssRuleBody(".hoard-actor-pick.selected::after"), /content:\s*"✓"/);
// The Select Multiple pill lights up only while the mode is armed.
assert.match(cssRuleBody(".selection-mode-toggle:has(input:checked)"), /border-color:\s*var\(--select\)/);

console.log("panel layout persistence tests passed");
