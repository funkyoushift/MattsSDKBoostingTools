"use strict";

const assert = require("assert");
const path = require("path");
const {
  matchesItemTypeFilter,
  matchesRarityFilter,
  matchesManufacturerFilter,
  matchesDlcFilter,
  matchesSearchQuery,
  rowManufacturer,
  mergeTypeFilters,
  mergeManufacturerFilters,
  submitFieldsFromCard,
  applySubmitFields,
  notesFromCard,
  GZO_SEARCH_TYPE_OPTIONS,
  GZO_SEARCH_MANUFACTURERS,
  GZO_UNSUPPORTED_FIELDS
} = require("./gzo_codes_form");
const { loadBl4Catalog } = require("./bl4_codes_catalog");
const { loadResolver } = require("./serial_card_resolve");

function searchRow(overrides = {}) {
  return {
    name: "Kindread",
    category: "Class Mods",
    type: "Siren",
    rarity: "Legendary",
    manufacturer: "",
    creator: "Aries",
    listing: "Legit",
    dlc: "Base Game",
    serial: "@Uabc",
    ...overrides
  };
}

function main() {
  const vladofGun = searchRow({
    name: "Lucian's Flank",
    category: "Vladof",
    type: "Assault Rifle",
    manufacturer: "",
    rarity: "Pearl"
  });
  assert.strictEqual(rowManufacturer(vladofGun), "Vladof", "GZO category is manufacturer");
  assert.ok(matchesManufacturerFilter(vladofGun, "Vladof"));
  assert.ok(!matchesManufacturerFilter(vladofGun, "Jakobs"));
  assert.ok(matchesRarityFilter(vladofGun, "Pearlescent"), "Pearl matches Pearlescent filter");
  assert.ok(matchesRarityFilter(vladofGun, "Pearl"));
  assert.ok(!matchesRarityFilter(vladofGun, "Legendary"));

  const classmod = searchRow();
  assert.ok(matchesItemTypeFilter(classmod, "Classmod"));
  assert.ok(matchesItemTypeFilter(classmod, "Vex"));
  assert.ok(!matchesItemTypeFilter(classmod, "Amon"));
  assert.ok(matchesSearchQuery(classmod, "vex"), "vex alias matches Siren classmod");
  assert.ok(matchesSearchQuery(classmod, "siren"));
  assert.ok(!matchesSearchQuery(classmod, "vex shotgun"));

  const sniper = searchRow({ category: "Jakobs", type: "Sniper Rifle", manufacturer: "Jakobs" });
  assert.ok(matchesItemTypeFilter(sniper, "Sniper"));
  assert.ok(matchesItemTypeFilter(sniper, "Sniper Rifle"));

  const dlcRow = searchRow({ dlc: "Stone Demon", catalog_parameters: { dlc: "Stone Demon" } });
  assert.ok(matchesDlcFilter(dlcRow, "Stone Demon"));
  assert.ok(matchesDlcFilter(dlcRow, "Bounty Pack 2"), "Stone Demon aliases Bounty Pack 2");
  assert.ok(matchesDlcFilter(dlcRow, "__any_dlc__"));
  assert.ok(!matchesDlcFilter(dlcRow, "Base Game"));

  const types = mergeTypeFilters(["Siren", "Custom Blade"]);
  assert.ok(GZO_SEARCH_TYPE_OPTIONS.every((label) => types.includes(label)));
  assert.deepStrictEqual(types, GZO_SEARCH_TYPE_OPTIONS, "browse type options stay GZO-exact");
  assert.ok(!types.includes("Custom Blade"));
  const manufacturers = mergeManufacturerFilters(["Classmod", "Unknown", "Order"]);
  assert.deepStrictEqual(manufacturers, GZO_SEARCH_MANUFACTURERS, "browse manufacturers omit Classmod/Unknown");
  const notes = notesFromCard({
    part_effects: [
      { index: 1, name: "JAK_AR.comp_06_pearl_Root", effects: ["Eat lead"] },
      { index: 2, name: "part_body_01", effects: [] }
    ],
    red_text: ["Eat lead"]
  });
  assert.ok(notes.includes("{1} - JAK_AR.comp_06_pearl_Root — Eat lead"));
  assert.ok(notes.includes("{2} - part_body_01"));
  assert.ok(!notes.includes("Red text: Eat lead"), "do not duplicate a part effect as generic red text");
  console.log("PASS GZO search param mapping (manufacturer-from-category, classmod aliases, Pearl, DLC)");

  const zipperHuman = "2, 0, 1, 60| 2, 2010|| {54} {2} {4} {3} {5} {1} {62} {63} {13} {25} {42}|";
  const resolver = loadResolver({ sourceRoot: path.resolve(__dirname, "..") });
  const card = resolver.resolveFromHuman(zipperHuman);
  assert.ok(card.meta_ok, "Zipper card should resolve");
  const fields = submitFieldsFromCard(card);
  assert.ok(fields.name && /zipper/i.test(fields.name), `expected Zipper name, got ${fields.name}`);
  assert.strictEqual(fields.category, "Daedalus");
  assert.strictEqual(fields.type, "Pistol");
  assert.strictEqual(fields.rarity, "Legendary");
  assert.ok(fields.notes.includes("{1}"), "notes include part breakdown");
  assert.ok(
    /shot caller|Prison Rules|Critical Damage|Red text:| — /i.test(fields.notes),
    `notes should include known part effects, got ${fields.notes}`
  );
  const filled = applySubmitFields({ name: "Keep Me" }, fields);
  assert.strictEqual(filled.name, "Keep Me", "do not overwrite an existing display name");
  assert.strictEqual(filled.category, "Daedalus");
  const overwritten = applySubmitFields({ name: "Keep Me" }, fields, { overwrite: true });
  assert.ok(/zipper/i.test(overwritten.name));
  console.log("PASS serial decode populates GZO submit fields from item card");
}

async function catalogManufacturerFromCategory() {
  const fs = require("fs/promises");
  const os = require("os");
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-gzo-form-"));
  try {
    await fs.writeFile(path.join(dir, "MattsSDKBoostingTools_lootlemon_codes.json"), JSON.stringify({ entries: [] }));
    await fs.writeFile(path.join(dir, "custom_bl4_codes.json"), JSON.stringify({ entries: [] }));
    await fs.writeFile(path.join(dir, "MattsSDKBoostingTools_gzo_codes.json"), JSON.stringify({
      entries: [{
        name: "Amp Generous Cindershelly",
        serial: "@Ugr$-Om/*xI!qAwYN+qg&bwKeO18UzoQ2RbK2m",
        listing: "Legit",
        category: "Order",
        type: "Shield",
        rarity: "Legendary",
        manufacturer: "",
        creator: "Aries Arsenal",
        dlc: "Vault of the Damned",
        deserialized: "293, 0, 1, 60| 2, 2324|| {10}|"
      }]
    }));
    const result = await loadBl4Catalog(dir);
    assert.strictEqual(result.entries.length, 1);
    assert.strictEqual(result.entries[0].manufacturer, "Order");
    assert.strictEqual(result.entries[0].category, "Order");
    assert.strictEqual(result.entries[0].dlc, "Vault of the Damned");
    assert.ok(result.filters.manufacturers.includes("Order"));
    assert.ok(result.filters.dlcs.includes("Vault of the Damned"));
    console.log("PASS GZO catalog recovers manufacturer from category and keeps DLC");
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
}

async function run() {
  main();
  await catalogManufacturerFromCategory();
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
