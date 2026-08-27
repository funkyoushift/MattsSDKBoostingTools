const assert = require("assert");
const fs = require("fs");
const path = require("path");

const source = fs.readFileSync(path.join(__dirname, "panel_layout.js"), "utf8");

assert.match(source, /const NAV_TABS_KEY = "msbt\.navTabs\.v2"/);
assert.match(source, /const NAV_TABS_LEGACY_KEY = "msbt\.navTabs\.v1"/);
assert.match(source, /const DEFAULT_HIDDEN_NAV_TABS = \["activity", "mobile-gateway", "report", "updates"\]/);
assert.match(source, /const LAYOUT_TOOLBAR_VISIBLE_KEY = "msbt\.layoutToolbar\.visible\.v1"/);
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
assert.match(styles, /html:not\(\.msbt-show-layout-toolbar\) \.msbt-layout-toolbar-host/);
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
assert.deepStrictEqual(
  store.BOOSTING_SPLIT_PANEL_IDS,
  ["boost-ground-loot", "boost-farm", "boost-uvh", "boost-combat-xp", "boost-debug"]
);
assert.ok(store.BOOSTING_DEFAULT_TILES["boost-essentials"].h <= 20, "Essentials default tile must stay compact");
assert.ok(store.BOOSTING_DEFAULT_TILES["boost-ground-loot"], "Ground Loot must have a default tile");
assert.ok(store.BOOSTING_DEFAULT_TILES["boost-farm"], "Chests & Vendors must have a default tile");

const oldBoostingLayout = {
  version: 2,
  revision: 12,
  items: [
    { type: "panel", id: "boost-essentials", x: 0, y: 0, w: 32, h: 32 },
    { type: "panel", id: "boost-target", x: 32, y: 0, w: 16, h: 26 }
  ],
  hidden: []
};
store.migrateBoostingSavedLayout(oldBoostingLayout);
const migratedIds = oldBoostingLayout.items.map((spec) => spec.id);
store.BOOSTING_SPLIT_PANEL_IDS.forEach((id) => {
  assert.ok(migratedIds.includes(id), `vanilla Boosting save must gain ${id} without Reset`);
});
assert.strictEqual(oldBoostingLayout.items.find((spec) => spec.id === "boost-essentials").h, 20);

const customBoostingLayout = {
  version: 2,
  revision: 12,
  items: [
    { type: "panel", id: "boost-essentials", x: 4, y: 2, w: 28, h: 18 },
    { type: "panel", id: "boost-target", x: 0, y: 0, w: 16, h: 16 }
  ],
  hidden: []
};
store.migrateBoostingSavedLayout(customBoostingLayout);
assert.strictEqual(customBoostingLayout.items[0].x, 4, "custom Essentials geometry must be kept");
assert.ok(customBoostingLayout.items.some((spec) => spec.id === "boost-ground-loot" && spec.y >= 18));

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

const html = fs.readFileSync(path.join(__dirname, "renderer.html"), "utf8");
assert.match(html, /id="funkPoweredMark"/);
assert.match(html, /id="msbtBootSplash"/);
assert.match(html, /branding\/fu-logo\.png/);
assert.match(html, /id="bootWelcomeDontShow"/);
assert.match(html, /Join the Discord for support/);
assert.match(html, /Leave a tip/);
assert.doesNotMatch(html, /branding\/msbt-together-splash\.png/);
assert.match(html, /Powered by Funk/);
[
  "boost-essentials",
  "boost-ground-loot",
  "boost-farm",
  "boost-uvh",
  "boost-combat-xp",
  "boost-debug",
  "boost-target",
  "boost-challenges"
].forEach((id) => {
  assert.match(html, new RegExp(`data-msbt-panel="${id}"`), `Boosting is missing panel ${id}`);
});
assert.doesNotMatch(html, /boost-essentials-layout/, "Essentials mega-layout wrapper should be gone");
assert.ok(fs.existsSync(path.join(__dirname, "branding", "fu-logo.png")));
assert.ok(fs.existsSync(path.join(__dirname, "branding", "msbt-together-splash.png")));
assert.match(fs.readFileSync(path.join(__dirname, "renderer.js"), "utf8"), /function runBootSplash\(/);

console.log("panel layout persistence tests passed");
