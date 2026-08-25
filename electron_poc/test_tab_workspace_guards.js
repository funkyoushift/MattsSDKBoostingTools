"use strict";

/**
 * Guardrail: Inventory layout CSS must not steal .tab-shell from Dev Spawner /
 * Matt Editor, and every main tab must still paint a usable workspace after
 * visiting Inventory. Run with: electron test_tab_workspace_guards.js
 */
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { app, BrowserWindow } = require("electron");

const cssPath = path.join(__dirname, "styles.css");
const htmlPath = path.join(__dirname, "renderer.html");

function assertCssIsolation() {
  const css = fs.readFileSync(cssPath, "utf8");
  const ruleBlocks = css.split("}").map((chunk) => `${chunk}}`);
  const shellHasRules = ruleBlocks.filter((block) => /\.tab-shell:has\(/.test(block));
  shellHasRules.forEach((block) => {
    const mentionsInventory = /#tab-inventory/.test(block);
    const mentionsDevSpawner = /#tab-dev-spawner/.test(block);
    const mentionsMattEditor = /#tab-matt-editor/.test(block);
    assert.ok(
      !(mentionsInventory && mentionsDevSpawner),
      "Inventory must not share a .tab-shell:has() rule with Dev Spawner"
    );
    assert.ok(
      !(mentionsInventory && mentionsMattEditor),
      "Inventory must not share a .tab-shell:has() rule with Matt Editor"
    );
  });
  assert.match(
    css,
    /\.tab-shell:has\(#tab-dev-spawner\.active\.msbt-fixed-tab\)\s*\{/,
    "Dev Spawner Compact still needs its dedicated tab-shell :has() rule"
  );
}

function assertHtmlTabSiblings() {
  const html = fs.readFileSync(htmlPath, "utf8");
  const ids = [...html.matchAll(/id="(tab-[^"]+)"/g)].map((m) => m[1]);
  assert.ok(ids.includes("tab-matt-editor"), "Matt Editor tab missing from renderer.html");
  assert.ok(ids.includes("tab-dev-spawner"), "Dev Spawner tab missing from renderer.html");
  assert.ok(ids.includes("tab-inventory"), "Inventory tab missing from renderer.html");
  assert.strictEqual(ids.length, new Set(ids).size, `duplicate tab ids: ${ids.join(", ")}`);
  assert.ok(html.includes('id="editorFrame"'), "Matt Editor iframe missing");
  assert.ok(html.includes('id="loadEditorBtn"'), "Matt Editor Load Editor button missing");
  assert.ok(html.includes("data-dev-host=\"actor-rows\""), "Dev Spawner actor list host missing");
  assert.ok(html.includes("data-dev-host=\"spawn-ai-btn\""), "Dev Spawner spawn button host missing");
}

const WORKSPACES = [
  { tab: "boosting", sel: "#tab-boosting [data-msbt-layout-root]", minH: 120 },
  { tab: "quick-menu", sel: "#tab-quick-menu", minH: 80 },
  { tab: "serial-tools", sel: "#tab-serial-tools", minH: 80 },
  { tab: "inventory", sel: "#tab-inventory .inv-root", minH: 120 },
  { tab: "bl4-codes", sel: "#tab-bl4-codes .bl4-layout", minH: 120 },
  { tab: "matt-editor", sel: "#editorFrame", minH: 200 },
  { tab: "item-pool", sel: "#tab-item-pool .item-pool-page", minH: 80 },
  { tab: "dev-spawner", sel: "#tab-dev-spawner .dev-spawner-primary", minH: 120 },
  { tab: "hoard-builder", sel: "#tab-hoard-builder", minH: 80 },
  { tab: "map-travel", sel: "#tab-map-travel", minH: 80 },
  { tab: "player-movement", sel: "#tab-player-movement", minH: 80 },
  { tab: "activity", sel: "#tab-activity", minH: 80 },
  { tab: "mobile-gateway", sel: "#tab-mobile-gateway", minH: 80 },
  { tab: "report", sel: "#tab-report", minH: 80 },
  { tab: "updates", sel: "#tab-updates", minH: 80 }
];

async function auditWorkspaces() {
  const win = new BrowserWindow({
    show: false,
    width: 1800,
    height: 1000,
    webPreferences: {
      partition: `workspace-guards-${process.pid}`,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  await win.loadFile(htmlPath, { query: { nosplash: "1" } });
  await new Promise((resolve) => setTimeout(resolve, 750));

  const result = await win.webContents.executeJavaScript(`(() => {
    const workspaces = ${JSON.stringify(WORKSPACES)};
    const nestedPanels = document.querySelectorAll(".tab-panel .tab-panel").length;
    const measure = (tab, sel) => {
      if (typeof switchTab === "function") switchTab(tab);
      const el = document.querySelector(sel);
      const tabEl = document.getElementById("tab-" + tab);
      const shell = document.querySelector(".tab-shell");
      const rect = el ? el.getBoundingClientRect() : null;
      const shellStyle = shell ? getComputedStyle(shell) : null;
      return {
        tab,
        sel,
        found: Boolean(el),
        tabActive: Boolean(tabEl && tabEl.classList.contains("active")),
        width: rect ? Math.round(rect.width) : 0,
        height: rect ? Math.round(rect.height) : 0,
        shellOverflow: shellStyle ? shellStyle.overflow : "",
        shellDisplay: shellStyle ? shellStyle.display : ""
      };
    };
    const firstPass = workspaces.map((row) => measure(row.tab, row.sel));
    measure("inventory", "#tab-inventory .inv-root");
    const afterInventory = [
      measure("matt-editor", "#editorFrame"),
      measure("dev-spawner", "#tab-dev-spawner .dev-spawner-primary"),
      measure("dev-spawner", "#tab-dev-spawner .dev-spawner-controls")
    ];
    const extra = {
      loadEditor: Boolean(document.getElementById("loadEditorBtn")),
      editorFrame: Boolean(document.getElementById("editorFrame")),
      spawnHost: Boolean(document.querySelector("#tab-dev-spawner [data-dev-host='spawn-ai-btn']")),
      actorHost: Boolean(document.querySelector("#tab-dev-spawner [data-dev-host='actor-rows']"))
    };
    return { nestedPanels, firstPass, afterInventory, extra };
  })()`);

  assert.strictEqual(result.nestedPanels, 0, "tab panels must not nest inside each other");
  assert.ok(result.extra.loadEditor, "Load Editor button missing at runtime");
  assert.ok(result.extra.editorFrame, "editorFrame missing at runtime");
  assert.ok(result.extra.spawnHost, "Dev Spawner spawn host missing at runtime");
  assert.ok(result.extra.actorHost, "Dev Spawner actor host missing at runtime");

  const failures = [];
  WORKSPACES.forEach((spec, i) => {
    const row = result.firstPass[i];
    if (!row.found) failures.push(`${spec.tab}: missing ${spec.sel}`);
    else if (!row.tabActive) failures.push(`${spec.tab}: tab did not become active`);
    else if (row.height < spec.minH) failures.push(`${spec.tab}: ${spec.sel} height ${row.height} < ${spec.minH}`);
  });

  const mattAfter = result.afterInventory.find((row) => row.tab === "matt-editor");
  const devPrimaryAfter = result.afterInventory.find((row) => row.sel.includes("dev-spawner-primary"));
  const devControlsAfter = result.afterInventory.find((row) => row.sel.includes("dev-spawner-controls"));
  if (!mattAfter || mattAfter.height < 200) {
    failures.push(`Matt Editor iframe collapsed after Inventory (h=${mattAfter && mattAfter.height})`);
  }
  if (!devPrimaryAfter || devPrimaryAfter.height < 120) {
    failures.push(`Dev Spawner list collapsed after Inventory (h=${devPrimaryAfter && devPrimaryAfter.height})`);
  }
  if (!devControlsAfter || devControlsAfter.height < 40) {
    failures.push(`Dev Spawner controls collapsed after Inventory (h=${devControlsAfter && devControlsAfter.height})`);
  }
  if (mattAfter && mattAfter.shellOverflow === "hidden") {
    failures.push("Matt Editor tab-shell overflow is hidden; Inventory CSS leaked into .tab-shell");
  }

  assert.deepStrictEqual(failures, [], failures.join("\n"));
  console.log(`tab workspace guards passed (${WORKSPACES.length} tabs; inventory→editor/spawner still sized)`);
  win.destroy();
}

assertCssIsolation();
assertHtmlTabSiblings();

app.whenReady()
  .then(auditWorkspaces)
  .then(() => app.exit(0))
  .catch((error) => {
    console.error(error && error.stack ? error.stack : error);
    app.exit(1);
  });
