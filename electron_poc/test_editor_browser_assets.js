"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const editor = process.env.EDITOR_ROOT || path.join(__dirname, "../external_app/v22_parts_codes_fixed/matt_editor");
const sha256 = blob => crypto.createHash("sha256").update(blob).digest("hex");
const nativeProvenance = JSON.parse(fs.readFileSync(path.join(editor, "LegitItems/local_game_data_provenance.json"), "utf8"));
for (const entry of nativeProvenance.imported) {
  assert.equal(sha256(fs.readFileSync(path.join(editor, "LegitItems", entry.file))), entry.imported_sha256, `Native table hash: ${entry.file}`);
}
const html = fs.readFileSync(path.join(editor, "index.html"), "utf8");
const bundlePath = "js/vendor/js-yaml-4.3.2.js";
assert(html.includes(bundlePath));
assert(!html.includes("js-yaml-4.1.1.js"));
for (const match of html.matchAll(/<script[^>]+src=["']([^"']+)["']/g)) {
  const relative = match[1].split("?")[0];
  if (/^(?:https?:)?\/\//.test(relative)) continue;
  assert(fs.existsSync(path.join(editor, relative)), `Missing browser script ${relative}`);
}
const blob = fs.readFileSync(path.join(editor, bundlePath));
const provenance = JSON.parse(fs.readFileSync(path.join(editor, "js/vendor/bundle-provenance.json"), "utf8"));
assert.equal(provenance.js_yaml_version, "4.3.2");
assert.equal(sha256(blob), provenance.bundle_sha256);
assert.equal(sha256(blob.subarray(blob.indexOf("/*! pako"))), provenance.preserved_pako_monaco_sha256);

const browser = { setTimeout, clearTimeout, console, TextEncoder, TextDecoder };
browser.window = browser;
browser.self = browser;
vm.createContext(browser);
vm.runInContext(blob.toString("utf8"), browser, { timeout: 2000 });
assert.equal(typeof browser.jsyaml.load, "function");
assert.equal(typeof browser.pako.deflate, "function");
assert.equal(typeof browser.require, "function", "Preserve the Monaco AMD loader");
const yaml = "state:\n  character_class: Char_CorpoHacker\n  experience:\n    - type: Character\n      level: 70\n      points: 123456\n  inventory:\n    - serial: '@example_serial'\nshared:\n  vaultcard5: 19\n  unicode: 'Loveless — 世界'\n";
const parsed = browser.jsyaml.load(yaml);
assert.equal(parsed.state.experience[0].level, 70);
assert.equal(parsed.state.experience[0].points, 123456);
assert.equal(parsed.shared.vaultcard5, 19);
assert.equal(JSON.stringify(browser.jsyaml.load(browser.jsyaml.dump(parsed))), JSON.stringify(parsed));
assert.equal(browser.pako.inflate(browser.pako.deflate(yaml), { to: "string" }), yaml);
assert.throws(() => browser.jsyaml.load("state: [broken"));

vm.runInContext(fs.readFileSync(path.join(editor, "js/release-new-parts.js"), "utf8"), browser);
const badges = browser.bl4ReleaseNewParts;
assert.equal(badges.gameBuild, "25234898");
assert.equal(badges.serialIds.size, 774);
assert.equal(badges.partKeys.size, 202);
assert(badges.serialIds.has("402:1") && badges.typeIds.has(402));
assert(!badges.serialIds.has("1:51"), "Retire the earlier catalog's NEW badges");
const supplemental = fs.readFileSync(path.join(editor, "js/item-editor/data/local-game-part-supplement.js"), "utf8");
vm.runInContext(supplemental, browser);
const ids = new Set(browser.MSBT_LOCAL_GAME_PART_SUPPLEMENT.map(row => row.fullId));
for (const id of badges.serialIds) assert(ids.has(id), `Badge references missing part ${id}`);

const theme = fs.readFileSync(path.join(editor, "js/item-editor/ui/legit-theme.js"), "utf8");
function functionSlice(name, next) {
  const begin = theme.indexOf(`function ${name}(`);
  const end = theme.indexOf(`function ${next}(`, begin);
  assert(begin >= 0 && end > begin);
  return theme.slice(begin, end);
}
let rows = [];
const host = { innerHTML: "" };
const dom = {
  querySelectorAll: () => rows,
  getElementById: () => host,
};
const controls = vm.createContext({
  document: dom, ITEM_MAX_LEVEL: 70,
  blackMarketLabelForComp: value => value,
  escapeHtmlProgressionUi: value => String(value),
});
vm.runInContext(functionSlice("getBlackMarketRowsFromDom", "renderBlackMarketSlotRows"), controls);
vm.runInContext(functionSlice("renderBlackMarketSlotRows", "updateBlackMarketSuggestRow"), controls);
rows = ["", "23", "invalid"].map(value => ({ querySelector: selector => ({ value: selector.includes("comp-hidden") ? "weapon.test" : value }) }));
assert.deepEqual(Array.from(controls.getBlackMarketRowsFromDom(), row => row.gamestage), [70, 23, 70]);
controls.renderBlackMarketSlotRows([{ itemcomp: "weapon.test" }]);
assert(host.innerHTML.includes('max="70" value="70"'));
assert(!html.includes("Added C4sh"));
assert(!html.includes("Vault Card 4 support!"));
process.stdout.write("Editor browser checks passed: YAML/pako/Monaco, script assets, catalog badges, Black Market defaults.\n");
