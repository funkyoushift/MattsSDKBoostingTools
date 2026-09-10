"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const editor = path.join(root, "external_app", "v22_parts_codes_fixed", "matt_editor");
const renderer = fs.readFileSync(path.join(__dirname, "renderer.js"), "utf8");
const theme = fs.readFileSync(path.join(editor, "js", "item-editor", "ui", "legit-theme.js"), "utf8");
const save = fs.readFileSync(path.join(editor, "js", "item-editor-10-yaml-save.js"), "utf8");

function definition(source, name, indent = "") {
  const marker = `${indent}function ${name}(`;
  const start = source.indexOf(marker);
  assert(start >= 0, `missing ${name}`);
  const end = source.indexOf(`\n${indent}}`, start);
  assert(end > start, `missing end of ${name}`);
  return source.slice(start, end + indent.length + 2);
}

const els = {
  xpTrack: { value: "player" },
  xpLevel: { value: "99999" },
  boostSerialLevel: {}, bl4DeliveryLevel: {}, invSerialLevel: {}, itempoolLevel: {}
};
const rendererContext = vm.createContext({
  els,
  state: { gameParameters: { player_level_cap: 70, item_level_cap: 70, specialization_level_cap: 701, vault_card_level_cap: 9999 } }
});
for (const name of ["getValue", "getInt", "experienceLevelCap", "getExperienceLevel", "syncGameParameterControls"]) {
  vm.runInContext(definition(renderer, name), rendererContext);
}
for (const [track, cap] of [["player", 70], ["specialization", 701], ["vaultcard_xp_5", 9999]]) {
  els.xpTrack.value = track;
  els.xpLevel.value = "99999";
  rendererContext.syncGameParameterControls();
  assert.strictEqual(els.xpLevel.max, String(cap));
  assert.strictEqual(rendererContext.getExperienceLevel(), cap);
}
rendererContext.syncGameParameterControls({ vault_card_level_cap: 9998, item_level_cap: 70 });
assert.strictEqual(rendererContext.getExperienceLevel(), 9998, "bridge parameters must govern delivery");
rendererContext.syncGameParameterControls({ vault_card_level_cap: 0 });
assert.strictEqual(rendererContext.getExperienceLevel(), 9998, "invalid status must preserve known cap");

const fields = {};
for (let card = 1; card <= 5; card += 1) {
  const id = card === 1 ? "vaultcard" : `vaultcard0${card}`;
  fields[`${id}-tokens-input`] = { value: String(card * 100) };
  fields[`${id}-level-input`] = { value: String(card === 5 ? 9999 : card) };
  fields[`${id}-points-input`] = { value: String(card * 1000) };
}
let yaml = JSON.stringify({ domains: { local: { shared: {
  currencies: { cash: 123 },
  experience: [{ type: "Unrelated_Experience", level: 8, points: 9 }]
} } } });
const messages = [];
const profileContext = vm.createContext({
  VAULT_CARD_MAX_LEVEL: 9999,
  document: { getElementById: id => fields[id] || null },
  window: { profileMonacoEditor: { getValue: () => yaml, setValue: value => { yaml = value; } } },
  jsyaml: { load: JSON.parse, dump: JSON.stringify },
  showSaveStatus: (...message) => messages.push(message),
  console
});
vm.runInContext(definition(theme, "updateCurrencies", "        "), profileContext);
profileContext.updateCurrencies();
const shared = JSON.parse(yaml).domains.local.shared;
assert.strictEqual(shared.currencies.vaultcard05_tokens, 500);
assert.strictEqual(shared.currencies.cash, 123);
assert.deepStrictEqual(shared.experience.find(entry => entry.type === "VaultCard05_Experience"), {
  type: "VaultCard05_Experience", level: 9999, points: 5000
});
assert.deepStrictEqual(shared.experience[0], { type: "Unrelated_Experience", level: 8, points: 9 });
const before = yaml;
fields["vaultcard05-level-input"].value = "10000";
profileContext.updateCurrencies();
assert.strictEqual(yaml, before, "out-of-range card levels must leave the profile untouched");
assert.strictEqual(messages.at(-1)[2], false);
fields["vaultcard05-level-input"].value = "5";
for (let card = 1; card <= 5; card += 1) {
  const suffix = card === 1 ? "" : `0${card}`;
  const prefix = `vaultcard${suffix}`;
  const handler = `updateVaultCard${suffix}Level`;
  fields[`${prefix}-level-input`].value = String(100 + card);
  fields[`${prefix}-points-input`].value = String(987650 + card);
  vm.runInContext(definition(theme, handler, "        "), profileContext);
  profileContext[handler]();
  const experience = JSON.parse(yaml).domains.local.shared.experience;
  const saved = experience.find(entry => entry.type === `VaultCard0${card}_Experience`);
  assert.strictEqual(saved.level, 100 + card);
  assert.strictEqual(saved.points, 987650 + card, "changing Vault Card level must preserve explicit XP points");
  assert.strictEqual(fields[`${prefix}-points-input`].value, String(987650 + card));
}

const classStart = save.indexOf("const CHARACTER_CLASSES = ");
const classEnd = save.indexOf("\n        };", classStart) + "\n        };".length;
let character = { state: { class: "Char_DarkSiren", inventory: { sentinel: true } } };
const characterContext = vm.createContext({
  DEBUG: false,
  getYamlDataFromTextarea: () => character,
  setYamlDataToTextarea: value => { character = value; },
  generateUUID: () => "test-new-guid",
  showSaveStatus: () => {},
  console
});
vm.runInContext(save.slice(classStart, classEnd), characterContext);
vm.runInContext(definition(save, "setCharacterClass", "        "), characterContext);
characterContext.setCharacterClass("CorpoHacker", "Loveless");
assert.strictEqual(character.state.class, "Char_CorpoHacker");
assert.strictEqual(character.state.char_name, "Loveless");
assert.deepStrictEqual(character.state.inventory, { sentinel: true });

const partsSource = fs.readFileSync(path.join(editor, "js", "item-editor", "domain", "process-data.js"), "utf8");
const supplementSource = fs.readFileSync(path.join(editor, "js", "item-editor", "data", "local-game-part-supplement.js"), "utf8");
const partsContext = vm.createContext({ window: {}, typeIdMap: new Map(), partsMap: new Map(), partsByTypeId: new Map(), console });
vm.runInContext(supplementSource, partsContext);
const native = partsContext.window.MSBT_LOCAL_GAME_PART_SUPPLEMENT;
const loveless = native.filter(entry => entry.typeId === 402);
assert(loveless.length >= 546, "installed Loveless parts must be available to the browser");
partsContext.window.MSBT_GZO_FAMILY_PART_SUPPLEMENT = [{ ...loveless[0], name: "stale remote label" }];
vm.runInContext(definition(partsSource, "mergeMsbtPartSupplements", "        "), partsContext);
partsContext.mergeMsbtPartSupplements();
assert.strictEqual(partsContext.partsMap.get(loveless[0].fullId).name, loveless[0].name,
  "fresh extracted supplement must take precedence over stale external supplement");
assert.strictEqual(partsContext.partsByTypeId.get(402).length, loveless.length);

console.log("game update UI tests passed: track caps, Vault Card 5, Loveless class token and part import");
