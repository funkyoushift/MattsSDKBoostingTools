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

console.log("panel layout persistence tests passed");
