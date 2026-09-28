"use strict";
const assert = require("assert");
const fs = require("fs");
const vm = require("vm");
const path = require("path");
const form = require("./gzo_codes_form");
const catalog = require("./bl4_codes_catalog");

async function main() {
  const source = fs.readFileSync(path.join(__dirname, "renderer.js"), "utf8");
  const start = source.indexOf("async function enrichBl4EntriesOffline(");
  const end = source.indexOf("\nfunction invFillSelect", start);
  assert.ok(start >= 0 && end > start);
  const context = vm.createContext({
    gzoForm: () => form,
    resolveOfflineCardMap: async () => new Map([
      ["@Utest", { meta_ok: true, item_type: "Classmod", character_class: "Siren" }],
      ["@Ufallback", { meta_ok: true, item_type: "Classmod" }]
    ])
  });
  vm.runInContext(source.slice(start, end), context);
  for (const [type, character] of [["Siren", "Vex"], ["Paladin", "Amon"], ["Gravitar", "Harlowe"], ["Exo Soldier", "Rafa"], ["C4SH", "C4SH"], ["Loveless", "Loveless"]]) {
    const original = { type, category: "Classmod", serial: "@Ufallback", name: "Test" };
    const [enriched] = await context.enrichBl4EntriesOffline([original]);
    for (const row of [original, enriched, { type: "Classmod", character_class: character }]) {
      assert.ok(form.matchesItemTypeFilter(row, character), character);
      assert.ok(form.matchesItemTypeFilter(row, "Classmod"));
      for (const query of ["class mod", "class mods", "classmod", "classmods", character]) {
        assert.ok(form.matchesSearchQuery(row, query), `${character}: ${query}`);
      }
      if (character !== "Amon") assert.ok(!form.matchesItemTypeFilter(row, "Amon"));
    }
  }
  const [resolved] = await context.enrichBl4EntriesOffline([{ type: "Classmod", serial: "@Utest" }]);
  assert.equal(resolved.character_class, "Siren");
  assert.ok(form.matchesItemTypeFilter(resolved, "Vex"));
  const raw = { type: "Classmod", character_class: "Siren", serial: "@U12345678901234567890" };
  const normalized = catalog.normalizeGzoRow(raw);
  assert.equal(normalized.character_class, "Siren");
  assert.equal(catalog.normalizeCodeEntry(normalized, { prefix: "test", source: "GZO" }).character_class, "Siren");
  console.log("PASS class-mod filters and search survive card enrichment for all six classes");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
