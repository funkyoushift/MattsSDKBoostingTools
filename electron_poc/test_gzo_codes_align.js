"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const gzo = require("./gzo_codes_form");

assert.deepStrictEqual(gzo.GZO_SEARCH_MANUFACTURERS, [
  "Atlas", "CoV", "Daedalus", "Hyperion", "Jakobs", "Maliwan",
  "Order", "Ripper", "Tediore", "Torgue", "Vladof"
]);
assert.ok(!gzo.mergeManufacturerFilters().includes("Classmod"));
assert.ok(!gzo.mergeManufacturerFilters().includes("Unknown"));
assert.ok(gzo.manufacturerKeys().includes("Classmod"));
assert.ok(gzo.manufacturerKeys().includes("Unknown"));
assert.deepStrictEqual(gzo.manufacturerKeys()[0], "Atlas");
assert.ok(gzo.manufacturerKeys().indexOf("Classmod") < gzo.manufacturerKeys().indexOf("CoV"));
assert.deepStrictEqual(gzo.GZO_MANUFACTURER_TYPES.Unknown, ["AI"]);
assert.deepStrictEqual(gzo.GZO_MANUFACTURER_TYPES.Jakobs.includes("SMG"), false);
assert.deepStrictEqual(gzo.GZO_MANUFACTURER_TYPES.Atlas, ["Enhancement"]);
assert.ok(gzo.GZO_SEARCH_RARITIES.includes("Pearlescent"));
assert.ok(!gzo.GZO_SEARCH_RARITIES.includes("Pearl"));
assert.ok(gzo.GZO_SUBMIT_RARITIES.includes("Pearl"));
assert.ok(gzo.GZO_DLC_SEARCH_OPTIONS.some((row) => row.value === "__any_dlc__" && row.label === "Any DLC"));
assert.ok(!gzo.GZO_DLC_OPTIONS.includes("Any DLC"));

const paladin = { category: "Class Mods", type: "Paladin" };
assert.strictEqual(gzo.matchesItemTypeFilter(paladin, "Classmod"), true);
assert.strictEqual(gzo.matchesItemTypeFilter(paladin, "Amon"), true);
assert.strictEqual(gzo.matchesItemTypeFilter(paladin, "Harlowe"), false);
assert.strictEqual(gzo.matchesItemTypeFilter({ type: "Sniper Rifle" }, "Sniper"), true);
assert.strictEqual(gzo.matchesRarityFilter({ rarity: "Pearl" }, "Pearlescent"), true);
assert.strictEqual(gzo.matchesManufacturerFilter({ category: "Order", manufacturer: "" }, "Order"), true);
assert.strictEqual(gzo.matchesManufacturerFilter({ category: "Classmod" }, "Atlas"), false);
assert.strictEqual(gzo.matchesDlcFilter({ catalog_parameters: {} }, "Base Game"), true);
assert.strictEqual(gzo.matchesDlcFilter({ catalog_parameters: { dlc: "Story Pack 1" } }, "__any_dlc__"), true);
assert.strictEqual(gzo.matchesDlcFilter({ catalog_parameters: { dlc: "Bounty Pack 2" } }, "Stone Demon"), true);
assert.strictEqual(gzo.matchesListingSection({ listing: "Legit" }, "Legit"), true);
assert.strictEqual(gzo.matchesListingSection({ listing: "Lootlemon" }, "Legit"), true);
assert.strictEqual(gzo.matchesListingSection({ listing: "Modded" }, "Legit"), false);

const sorted = gzo.sortItemsByVotes([
  { name: "B", catalog_parameters: { votes: 1 } },
  { name: "A", catalog_parameters: { votes: 1 } },
  { name: "C", catalog_parameters: { votes: 9 } }
]);
assert.deepStrictEqual(sorted.map((row) => row.name), ["C", "A", "B"]);

const jakobs = gzo.submitFieldsFromCard({
  display_name: "Fatal Complex Root",
  manufacturer: "Jakobs",
  item_type: "Assault Rifle",
  rarity: "Pearlescent",
  red_text: ["Eat lead"],
  part_names: ["JAK_AR.comp_06_pearl_Root"]
});
assert.strictEqual(jakobs.category, "Jakobs");
assert.strictEqual(jakobs.type, "Assault Rifle");
assert.strictEqual(jakobs.rarity, "Pearl");
assert.ok(jakobs.notes.includes("Eat lead"));

const amon = gzo.submitFieldsFromCard({
  display_name: "Paladin Mod",
  manufacturer: "C4SH",
  item_type: "Classmod",
  character_class: "Paladin",
  rarity: "Legendary"
});
assert.strictEqual(amon.category, "Classmod");
assert.strictEqual(amon.type, "Paladin");

const ai = gzo.submitFieldsFromCard({ item_type: "AI", character_class: "AI", rarity: "Common" });
assert.strictEqual(ai.category, "Unknown");
assert.strictEqual(ai.type, "AI");

const html = fs.readFileSync(path.join(__dirname, "renderer.html"), "utf8");
assert.ok(html.includes('placeholder="Name, type, creator, etc."'));
assert.ok(html.includes("All creators") || html.includes('aria-label="Select author or creator"'));
assert.ok(html.includes("Legit (game-standard)"));
assert.ok(html.includes("Modded / non-legit"));
assert.ok(html.includes("Fill deserialized"));
assert.ok(html.includes("codes/Pending"));
assert.ok(html.includes('id="gzoSubmitCardPreview"'));
assert.ok(html.includes('id="bl4DlcFilter"'));
assert.ok(html.includes("Select manufacturer first"));
assert.ok(html.includes('id="bl4LegitSectionBtn"'));
assert.ok(html.includes("Use this card as the screenshot"));
assert.ok(html.includes("Upload a different image"));
assert.ok(html.includes('class="gzo-submit-cta submit-btn"'));
assert.ok(html.indexOf("Photo with item (camera or gallery)") < html.indexOf('id="gzoSubmitBase85"'));
assert.ok(html.indexOf('id="bl4DlcFilter"') < html.indexOf('id="bl4LegitSectionBtn"'));
assert.ok(html.indexOf("Submit to server") < html.indexOf('id="gzoSubmitClearBtn"'));
assert.ok(!gzo.mergeDlcFilters(["Custom Pack"]).some((row) => (row.label || row.value || row) === "Custom Pack"));

console.log("PASS GZO option lists, search matching, and submit auto-fill mapping");
