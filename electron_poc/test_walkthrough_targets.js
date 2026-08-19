const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { app, BrowserWindow } = require("electron");

async function auditWalkthroughs() {
  const win = new BrowserWindow({
    show: false,
    width: 1800,
    height: 900,
    webPreferences: {
      partition: `walkthrough-audit-${process.pid}`,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  await win.loadFile(path.join(__dirname, "renderer.html"), { query: { nosplash: "1" } });
  await new Promise((resolve) => setTimeout(resolve, 750));

  const result = await win.webContents.executeJavaScript(`(() => {
    const tours = [
      ...Object.entries(TUTORIAL_TOURS).map(([id, steps]) => [id, steps]),
      ...Object.entries(TAB_TUTORIALS).map(([id, steps]) => ["tab:" + id, steps])
    ];
    const missing = [];
    const zeroSized = [];
    let checked = 0;
    for (const [tourId, steps] of tours) {
      steps.forEach((step, index) => {
        if (!step || step.type === "choices") return;
        checked += 1;
        if (step.tab && typeof switchTab === "function") switchTab(step.tab);
        if (typeof prepareWalkthroughTarget === "function") prepareWalkthroughTarget(step);
        let target = null;
        if (step.target) target = document.getElementById(step.target);
        if (!target && step.targetSel) target = document.querySelector(step.targetSel);
        if (!target && step.targetSelFallback) target = document.querySelector(step.targetSelFallback);
        if (!target) missing.push({ tourId, index, title: step.title, target: step.target || step.targetSel });
        if (target) {
          const rect = target.getBoundingClientRect();
          if (rect.width < 1 || rect.height < 1) {
            zeroSized.push({ tourId, index, title: step.title, target: step.target || step.targetSel });
          }
        }
      });
    }
    const allCopy = tours.flatMap(([, steps]) => steps)
      .filter(Boolean)
      .map((step) => String(step.title || "") + "\\n" + String(step.body || ""))
      .join("\\n");
    return {
      checked,
      missing,
      zeroSized,
      staleCopy: {
        quickMax: /Quick Max/i.test(allCopy),
        debugPanel: /Debug Panel/i.test(allCopy),
        headerRefresh: /Refresh Status in (?:the )?header/i.test(allCopy)
      },
      requiredCopy: {
        selectMultiple: /Select Multiple/i.test(allCopy),
        redSelection: /turn red|red-highlighted/i.test(allCopy),
        hoardEnemyFilter: /enemies-only/i.test(allCopy),
        hoardVirtualized: /virtualized full list/i.test(allCopy),
        hoardShowAll: /Show all actors/i.test(allCopy),
        instantDropsHolds: allCopy.includes("Instant Drops / Instant Holds"),
        instantHotkeys: /direct oak2 hotkeys/i.test(allCopy),
        quickMenuPins: allCopy.toLowerCase().includes("gold + qm pins"),
        fixedPageTextScale: /scales docked panels, Fixed pages, and Dev Spawner/i.test(allCopy),
        instantActionHomes:
          /Essentials/i.test(allCopy) &&
          /Combat & Cheats/i.test(allCopy) &&
          /Debug Camera sits in its own Boosting panel/i.test(allCopy)
      },
      tourInventory: {
        structured: Object.fromEntries(Object.entries(TUTORIAL_TOURS).map(([id, steps]) => [id, steps.length])),
        tabs: Object.fromEntries(Object.entries(TAB_TUTORIALS).map(([id, steps]) => [id, steps.length]))
      },
      hoardGuide: {
        guide: Boolean(document.getElementById("hoardFirstRunGuide")),
        dismiss: Boolean(document.getElementById("hoardGuideDismissBtn")),
        steps: document.querySelectorAll("#hoardFirstRunGuide li").length
      },
      mainTitles: TUTORIAL_TOURS.main.map((step) => step && step.title),
      duplicateIds: (() => {
        const counts = new Map();
        document.querySelectorAll("[id]").forEach((node) => counts.set(node.id, (counts.get(node.id) || 0) + 1));
        return Array.from(counts.entries()).filter(([, count]) => count > 1);
      })(),
      duplicatePanels: (() => {
        const counts = new Map();
        document.querySelectorAll("[data-msbt-panel]").forEach((node) => {
          const id = node.getAttribute("data-msbt-panel");
          counts.set(id, (counts.get(id) || 0) + 1);
        });
        return Array.from(counts.entries()).filter(([, count]) => count > 1);
      })(),
      grid: (() => {
        switchTab("boosting");
        const root = document.querySelector("#tab-boosting [data-msbt-layout-root]");
        const instance = root && root.gridstack;
        if (!instance) return null;
        const columns = instance.getColumn();
        const rootWidth = root.clientWidth - 8; // root padding
        // Missing per-column CSS makes items shrink to content, so compare the
        // rendered width of every tile against the fraction it claims.
        const widthErrors = [];
        root.querySelectorAll(":scope > .grid-stack-item").forEach((item) => {
          const node = item.gridstackNode;
          if (!node || !rootWidth) return;
          const expected = (Number(node.w) / columns) * rootWidth;
          const actual = item.getBoundingClientRect().width;
          if (Math.abs(actual - expected) > Math.max(2, expected * 0.02)) {
            widthErrors.push({ w: node.w, expected: Math.round(expected), actual: Math.round(actual) });
          }
        });
        return {
          columns,
          cellHeight: instance.getCellHeight(),
          widthErrors
        };
      })()
    };
  })()`, true);

  const overlay = JSON.parse(
    fs.readFileSync(path.join(__dirname, "..", "docs", "data", "tutorial_copy.json"), "utf8")
  );
  for (const patch of overlay.tours.main || []) {
    assert.ok(result.mainTitles[patch.index], `tutorial overlay index ${patch.index} is out of range`);
    assert.strictEqual(
      result.mainTitles[patch.index],
      patch.title,
      `tutorial overlay "${patch.title}" points at "${result.mainTitles[patch.index]}"`
    );
  }
  assert.deepStrictEqual(result.missing, [], `missing walkthrough targets:\n${JSON.stringify(result.missing, null, 2)}`);
  assert.deepStrictEqual(result.zeroSized, [], `hidden/zero-size walkthrough targets:\n${JSON.stringify(result.zeroSized, null, 2)}`);
  assert.deepStrictEqual(
    result.staleCopy,
    { quickMax: false, debugPanel: false, headerRefresh: false },
    `stale walkthrough copy:\n${JSON.stringify(result.staleCopy, null, 2)}`
  );
  assert.deepStrictEqual(
    result.requiredCopy,
    {
      selectMultiple: true,
      redSelection: true,
      hoardEnemyFilter: true,
      hoardVirtualized: true,
      hoardShowAll: true,
      instantDropsHolds: true,
      instantHotkeys: true,
      quickMenuPins: true,
      fixedPageTextScale: true,
      instantActionHomes: true
    },
    `required walkthrough copy is incomplete:\n${JSON.stringify(result.requiredCopy, null, 2)}`
  );
  assert.deepStrictEqual(
    result.tourInventory.structured,
    { main: 12, layout: 7, "quick-menu-setup": 8 },
    "structured walkthrough inventory changed; audit the new/removed steps"
  );
  assert.deepStrictEqual(
    Object.keys(result.tourInventory.tabs).sort(),
    [
      "activity", "bl4-codes", "boosting", "dev-spawner", "hoard-builder", "inventory",
      "item-pool", "map-travel", "matt-editor", "mobile-gateway", "player-movement",
      "report", "serial-tools", "updates"
    ],
    "per-tab walkthrough inventory changed; audit the new/removed tour"
  );
  assert.deepStrictEqual(result.hoardGuide, { guide: true, dismiss: true, steps: 4 }, "Hoard first-run guide is incomplete");
  assert.deepStrictEqual(result.duplicateIds, [], "renderer must not contain duplicate DOM ids");
  assert.deepStrictEqual(result.duplicatePanels, [], "renderer must not contain orphaned duplicate panel ids");
  assert.ok(result.grid, "boosting tab must expose a GridStack instance");
  assert.strictEqual(result.grid.columns % 12, 0, "grid columns must stay a multiple of the authored 12");
  assert.strictEqual(result.grid.cellHeight * (result.grid.columns / 12), 72, "cell height must subdivide the 72px row");
  assert.deepStrictEqual(
    result.grid.widthErrors,
    [],
    `panel widths must match their column span:\n${JSON.stringify(result.grid.widthErrors, null, 2)}`
  );
  console.log(`walkthrough target audit passed (${result.checked} highlighted steps)`);
  win.destroy();
}

app.whenReady()
  .then(auditWalkthroughs)
  .then(() => app.exit(0))
  .catch((error) => {
    console.error(error && error.stack ? error.stack : error);
    app.exit(1);
  });
