"use strict";
const assert = require("assert");
const path = require("path");
const { app, BrowserWindow } = require("electron");
const { loadResolver } = require("./serial_card_resolve");
const samples = require("./fixtures/item_cards/equipped.json");

app.whenReady().then(async () => {
  const resolver = loadResolver({ sourceRoot: path.resolve(__dirname, "..") });
  const card = resolver.resolveFromHuman(samples.find((row) => row.slot === "W3").human);
  const win = new BrowserWindow({
    show: false, width: 1400, height: 1000,
    webPreferences: { partition: `item-card-test-${process.pid}`, sandbox: false }
  });
  await win.loadFile(path.join(__dirname, "renderer.html"), { query: { nosplash: "1" } });
  // Keep coverage of the legacy fallback. Native isolated frames are exercised
  // separately by test_native_card_render.js with their real resource protocol.
  await win.webContents.executeJavaScript("window.MSBTNativeCard.enabled=false");
  const result = await win.webContents.executeJavaScript(`(() => {
    const card = ${JSON.stringify(card)};
    const entry = applyOfflineCardToInventoryEntry({ display_name: "Debauched Strong Kitty" }, card);
    const node = createBl4ItemCard(entry);
    document.body.appendChild(node);
    const result = {
      name: node.querySelector(".bl4-card-name").textContent,
      status: node.querySelector(".bl4-card-name-status")?.textContent,
      strategy: entry.naming?.strategy,
      width: node.getBoundingClientRect().width,
      stats: node.querySelectorAll(".bl4-card-stat-value").length
    };
    node.remove();
    return result;
  })()`);
  assert.strictEqual(result.name, "Debauched Vibrating Kitty");
  assert.strictEqual(result.status, undefined);
  assert.strictEqual(result.strategy, "namestrat_tor");
  assert.ok(result.width > 0);
  assert.ok(result.stats > 0, "existing card stat fields must remain visible");
  for (const [index, name, type] of [[1, "Zealous Extolled Ichor", "Heavy Gun Ordnance"], [6, "Zealous Regulated Bubbles", "Assault Rifle"], [11, "Zealous Regulated Draupner", "Heavy Gun Ordnance"]]) {
    const sample = require("./fixtures/item_cards/mixed_order_user.json")[index];
    const resolved = resolver.resolveFromHuman(sample.human);
    const shown = await win.webContents.executeJavaScript(`(() => {
      const entry = applyOfflineCardToInventoryEntry({ display_name: "Prosperous G.M.R.", item_type: "Assault Rifle", rarity: "Legendary" }, ${JSON.stringify(resolved)});
      const node = createBl4ItemCard(entry);
      return { name: node.querySelector(".bl4-card-name").textContent, type: entry.item_type,
        estimate: node.querySelector(".bl4-card-stats-status")?.textContent };
    })()`);
    assert.strictEqual(shown.name, name);
    assert.strictEqual(shown.type, type);
    assert.strictEqual(shown.estimate, "Estimated stats");
  }
  const nativeName = await win.webContents.executeJavaScript(`(() => {
    const entry = applyOfflineCardToInventoryEntry({
      meta_source: "live_card", card_ok: true, card_name: "Zealous Regulated Draupner",
      display_name: "Zealous Regulated Draupner"
    }, ${JSON.stringify(resolver.resolveFromHuman(require("./fixtures/item_cards/mixed_order_user.json")[11].human))});
    return { name: entry.display_name, status: entry.name_status };
  })()`);
  assert.deepStrictEqual(nativeName, { name: "Zealous Regulated Draupner", status: "complete" });
  console.log("PASS real Electron renderer: screenshot names replace old guesses, stats preserved, live card names retained");
  win.destroy();
  app.exit(0);
}).catch((error) => { console.error(error); app.exit(1); });
