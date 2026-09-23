"use strict";

const assert = require("assert");
const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { loadBl4Catalog, refreshGzoCatalog } = require("./bl4_codes_catalog");

async function writeCatalog(dir, file, entries) {
  await fs.writeFile(path.join(dir, file), JSON.stringify({ entries }), "utf8");
}

async function main() {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-bl4-catalog-"));
  const serial = "@U12345678901234567890";
  try {
    await writeCatalog(dir, "MattsSDKBoostingTools_lootlemon_codes.json", [{
      name: "Shared Item",
      serial,
      source: "Lootlemon",
      url: "https://www.lootlemon.com/weapon/shared-item-bl4",
      content: "Bounty Pack 1"
    }]);
    await writeCatalog(dir, "MattsSDKBoostingTools_gzo_codes.json", [{
      name: "Shared Item GZO",
      image: "codes/Legit/Tester/Watts 150% Amp.png?v=1",
      base85: serial,
      source: "GZO",
      targetListing: "Legit",
      category: "Vladof",
      type: "SMG",
      deserialized: "18, 0, 1, 60| 2, 1|| {1}|",
      dlc: "Bounty Pack 1",
      votes: 7,
      tacklebox: true
    }, {
      name: "Paladin Row",
      base85: "@UPaladin12345678901234567890",
      targetListing: "Legit",
      category: "Classmod",
      type: "Paladin",
      rarity: "Pearl"
    }, {
      name: "Sniper Row",
      base85: "@USniper12345678901234567890",
      targetListing: "Legit",
      category: "Jakobs",
      type: "Sniper",
      rarity: "Legendary"
    }]);
    await writeCatalog(dir, "custom_bl4_codes.json", []);

    const result = await loadBl4Catalog(dir);
    assert.strictEqual(result.entries.length, 3, "identical serials should merge; extra GZO rows stay distinct");
    assert.strictEqual(result.counts.duplicatesCollapsed, 1);
    const shared = result.entries.find((row) => row.serial === serial);
    assert.deepStrictEqual(shared.sources, ["GZO", "Lootlemon"]);
    assert.strictEqual(shared.item_level, 60);
    assert.ok(shared.image_url.includes("150%25%20Amp.png"),"GZO percent filenames must not produce HTTP 400");
    assert.strictEqual(shared.manufacturer, "Vladof");
    assert.strictEqual(shared.type, "SMG");
    assert.strictEqual(shared.dlc, "Bounty Pack 1");
    assert.strictEqual(shared.catalog_parameters.votes, 7);
    assert.strictEqual(shared.url, "https://www.lootlemon.com/weapon/shared-item-bl4");
    assert.ok(result.filters.levels.includes("60"));
    const paladin = result.entries.find((row) => row.name === "Paladin Row");
    assert.ok(paladin);
    assert.strictEqual(paladin.category, "Classmod");
    assert.strictEqual(paladin.type, "Paladin");
    assert.strictEqual(paladin.rarity, "Pearlescent");
    const sniper = result.entries.find((row) => row.name === "Sniper Row");
    assert.ok(sniper);
    assert.strictEqual(sniper.manufacturer, "Jakobs");
    assert.strictEqual(sniper.type, "Sniper");
    console.log("PASS BL4 catalog dedupe, GZO parameters, and item level normalization");

    const freshSerial = "@UFresh12345678901234567890";
    const cachePath = path.join(dir, "cache", "gzo.json");
    const customPath = path.join(dir, "selected-custom.json");
    const customSerial = "@UCustom12345678901234567890";
    await fs.writeFile(customPath, JSON.stringify({ entries: [{ name: "Selected Custom", serial: customSerial }] }));
    const filePaths = {
      gzo: path.join(dir, "MattsSDKBoostingTools_gzo_codes.json"),
      custom: customPath
    };
    const refreshed = await refreshGzoCatalog(dir, cachePath, {
      filePaths,
      fetch: async () => ({
        ok: true,
        text: async () => JSON.stringify({ entries: [{ name: "Fresh GZO", base85: freshSerial }] })
      })
    });
    assert.strictEqual(refreshed.refreshed, 1);
    assert.ok(refreshed.entries.some((row) => row.serial === freshSerial), "first refresh must return newly cached GZO data");
    assert.ok(refreshed.entries.some((row) => row.serial === customSerial), "other selected catalog paths must be preserved");
    assert.ok(refreshed.entries.find((row) => row.serial === serial).sources.every((source) => source !== "GZO"), "stale bundled GZO data must not be reused");
    assert.strictEqual(filePaths.gzo, path.join(dir, "MattsSDKBoostingTools_gzo_codes.json"), "refresh must not mutate caller paths");
    const cached = JSON.parse(await fs.readFile(cachePath, "utf8"));
    assert.strictEqual(cached.entries[0].serial, freshSerial);
    console.log("PASS first GZO refresh selects fresh cache and retains other catalog overrides");
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
