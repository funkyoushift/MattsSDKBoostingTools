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
assert.match(source, /migrateSavedGridResolution\(primary\)/);
assert.match(source, /gridColumns: COLS/);
assert.match(source, /cellHeight: CELL_HEIGHT/);
assert.match(source, /const LAYOUT_LOCK_KEY = "msbt\.panelLayout\.locked\.v1"/);
assert.match(source, /data-msbt-layout-lock="locked"/);
assert.match(source, /addEventListener\("pagehide", persistAllReadyTabs\)/);
assert.match(source, /function applyLayoutLock\(/);
assert.doesNotMatch(source, /boosting:\s*12/);
assert.doesNotMatch(source, /savedLayoutHasHeavyOverlap/);
assert.doesNotMatch(source, /ignoring stale\/overlapping layout/);
assert.doesNotMatch(source, /localStorage\.removeItem\(storageKey\(tabId\)\);\s*\} catch \(_e\)/);

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
assert.match(styles, /\.msbt-layout-toolbar\[data-msbt-mode="fixed"\] \.msbt-layout-lock-switch/);
assert.match(styles, /\.msbt-layout-locked \.msbt-panel-handle/);

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

function memoryStorage() {
  const data = {};
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      data[key] = String(value);
    },
    removeItem(key) {
      delete data[key];
    }
  };
}

function fakeTab(tabId, panelIds) {
  return {
    getAttribute(name) {
      return name === "data-msbt-layout-tab" ? tabId : "";
    },
    querySelectorAll(sel) {
      if (sel !== "[data-msbt-panel]") return [];
      return panelIds.map((id) => ({
        getAttribute: (attr) => (attr === "data-msbt-panel" ? id : ""),
        classList: { contains: () => false }
      }));
    }
  };
}

global.localStorage = memoryStorage();
global.innerWidth = 1600;
const store = require("./panel_layout.js");

assert.strictEqual(store.layoutViewportKey(1600), "wide");
assert.strictEqual(store.layoutViewportKey(900), "compact");
assert.strictEqual(store.storageKey("boosting", "wide"), "msbt.panelLayout.v2.boosting.wide");

const overlappingLayout = {
  version: 2,
  revision: 11,
  gridColumns: store.COLS,
  cellHeight: store.CELL_HEIGHT,
  panelIds: "boost-essentials,boost-target",
  items: [
    { type: "panel", id: "boost-essentials", x: 0, y: 0, w: 32, h: 20 },
    { type: "panel", id: "boost-target", x: 8, y: 4, w: 24, h: 16 }
  ],
  hidden: []
};

const boostingTab = fakeTab("boosting", ["boost-essentials", "boost-target"]);
assert.strictEqual(
  store.savedLayoutIsUsable(boostingTab, overlappingLayout),
  true,
  "overlapping custom layouts must stay usable (overlap is an allowed arrange mode)"
);
assert.ok(
  !Object.prototype.hasOwnProperty.call(store.TAB_LAYOUT_MIN_REVISION, "boosting"),
  "Boosting must not wipe user layouts via a min-revision bump"
);

store.saveState("boosting", overlappingLayout);
const restored = store.loadState("boosting");
assert.ok(restored, "saved layout must load after a simulated restart");
assert.strictEqual(restored.items.length, 2);
assert.strictEqual(restored.items[0].x, 0);
assert.strictEqual(restored.items[0].w, 32);
assert.strictEqual(restored.items[1].x, 8);
assert.strictEqual(restored.items[1].y, 4);
assert.strictEqual(restored.items[1].w, 24);

global.innerWidth = 900;
const restoredCompact = store.loadState("boosting");
assert.ok(restoredCompact, "compact viewport must fall back to the wide saved layout");
assert.strictEqual(restoredCompact.items[1].x, 8);

const legacy12 = store.migrateSavedGridResolution({
  version: 2,
  revision: 10,
  items: [{ type: "panel", id: "boost-target", x: 6, y: 2, w: 6, h: 5 }]
});
assert.strictEqual(legacy12.gridColumns, store.COLS);
assert.strictEqual(legacy12.items[0].x, 6 * store.GRID_SCALE);
assert.strictEqual(legacy12.items[0].y, 2 * store.GRID_SCALE);
assert.strictEqual(legacy12.items[0].w, 6 * store.GRID_SCALE);
assert.strictEqual(legacy12.items[0].h, 5 * store.GRID_SCALE);

store.setLayoutLocked("boosting", true);
assert.strictEqual(store.isLayoutLocked("boosting"), true);
const lockRaw = JSON.parse(global.localStorage.getItem(store.LAYOUT_LOCK_KEY));
assert.strictEqual(lockRaw.boosting, true);
store.setLayoutLocked("boosting", false);
assert.strictEqual(store.isLayoutLocked("boosting"), false);

console.log("panel layout persistence tests passed");
