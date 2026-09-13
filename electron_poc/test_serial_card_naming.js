"use strict";
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { loadResolver, resolveFromHuman } = require("./serial_card_resolve");
const { loadNamingStrategies } = require("./serial_card_naming");
const sourceRoot = path.resolve(__dirname, "..");
const resolver = loadResolver({ sourceRoot });
// User supplied serials and in-game screenshots, 2026-09-13. These titles are
// not generated from the old resolver's output.
const mixedOrder = require("./fixtures/item_cards/mixed_order_user.json");
for (let index = 1; index < mixedOrder.length; index++) {
  const card = resolver.resolveFromHuman(mixedOrder[index].human);
  const title = index < 6 ? "Ichor" : index < 11 ? "Bubbles" : "Draupner";
  assert.strictEqual(card.display_name, `Zealous ${title === "Ichor" ? "Extolled" : "Regulated"} ${title}`, `user serial ${index}`);
  assert.strictEqual(card.item_type, title === "Bubbles" ? "Assault Rifle" : "Heavy Gun Ordnance");
  assert.strictEqual(card.rarity, title === "Ichor" ? "Legendary" : "Pearlescent");
  assert.strictEqual(card.name_status, "resolved");
  assert.ok(card.part_keys.length > 96, "do not truncate stacked parts before evaluation");
}
const stacked = resolver.resolveFromHuman(mixedOrder[1].human);
assert.ok(stacked.part_keys.filter((key, i) => key === "part_barrel_02_rowan" && stacked.part_roots[i] === "jak_ar").length > 4);
const sameType = resolver.resolveFromHuman("15, 0, 1, 60| 2, 82|| {15:2}|");
assert.deepStrictEqual(sameType.part_keys, ["part_barrel_02_gmr"]);
const unknownType = resolver.resolveFromHuman("15, 0, 1, 60| 2, 82|| {999999:2}|");
assert.deepStrictEqual(unknownType.part_keys, [], "unknown typed reference must not fall back to an Order part");
// Equal priorities keep serial order; a genuinely higher-priority name wins.
const originalGmr = resolver.ctx.invNameParts.get("np_gmr");
try {
  resolver.ctx.invNameParts.set("np_gmr", { ...originalGmr, priority: 4 });
  assert.strictEqual(resolver.resolveFromHuman(mixedOrder[6].human).unique_name, "G.M.R.");
} finally {
  resolver.ctx.invNameParts.set("np_gmr", originalGmr);
}
const dir = path.join(sourceRoot, "external_app/v22_parts_codes_fixed/matt_editor/LegitItems");
const provenance = JSON.parse(fs.readFileSync(path.join(dir, "item_naming_provenance.json")));
for (const file of provenance.files) {
  assert.strictEqual(crypto.createHash("sha256").update(fs.readFileSync(path.join(dir, file.file))).digest("hex"), file.imported_sha256);
}

// Actual game strategies explicitly describe threshold comparisons, single and
// doubled stats, and combination priorities. A top-two tag-count model cannot
// substitute for these inputs. This verifies extraction, not native execution.
for (const [id, label, priority] of [
  ["namestrat_ord", "Extolled", 908],
  ["namestrat_tor", "Vibrating", 602],
  ["namestrat_vla", "Lionized", 907],
  ["namestrat_mal", "Nadir", 807]
]) {
  const strategy = resolver.ctx.namingStrategies.get(id);
  assert.ok(strategy?.structtype.includes("OakWeaponNamingStrategy"), id);
  const row = strategy.combinationnames.find((r) => r.namepart.partname.endsWith(", " + label));
  assert.ok(row, `${id}: missing ${label}`);
  assert.strictEqual(Number(row.namepart.priority), priority);
  const damage = strategy.namingattributethresholds.find((r) => r.attributename === "Damage");
  assert.strictEqual(Number(damage.firstthreshold), 1.2);
  assert.strictEqual(Number(damage.secondthreshold), 1.4);
  const reload = strategy.namingattributethresholds.find((r) => r.attributename === "ReloadSpeed");
  assert.ok(Number(reload.secondthreshold) < Number(reload.firstthreshold));
}

const strategy = { structtype: "OakWeaponNamingStrategy", namingattributethresholds: [] };
const merged = loadNamingStrategies([
  { inv_name_strategy: { records: [{ entries: [{ namestrat_ord: { namingstrategy: strategy } }] }] } },
  { inv_name_strategy: { records: [{ entries: [{ namestrat_ord: { inv_name_strategy: "NameStrat_ORD" } }] }] } }
]);
assert.strictEqual(merged.get("namestrat_ord"), strategy, "reference-only DLC row must not erase strategy");
const samples = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures/item_cards/equipped.json")));
for (const slot of ["W1", "W2", "W3", "W4"]) {
  const card = resolveFromHuman(samples.find((r) => r.slot === slot).human,{...resolver.ctx,statData:null});
  assert.strictEqual(card.stat_prefix, "", `${slot}: unsupported prefix must be omitted`);
  assert.strictEqual(card.naming.reason, "assembled_naming_attributes_unresolved");
  assert.ok(card.naming.required_attributes.length >= 8);
  const entry = resolver.mergeCardOntoEntry({ display_name: "Old guessed title" }, card);
  assert.strictEqual(entry.name_status, "partial");
  assert.strictEqual(entry.naming.strategy, card.naming.strategy);
}
console.log(`PASS naming: ${resolver.ctx.namingStrategies.size} extracted strategies; screenshot prefixes, priorities, missing-input partial-name propagation`);
