"use strict";
const assert = require("node:assert/strict");
const {detectDlc,submitFieldsFromCard,applySubmitFields} = require("./gzo_codes_form");
const contract = require("./gzo_dlc_contract");
assert.ok(Object.keys(contract.parts).length >= 160);
for (const [key, label] of Object.entries(contract.parts)) {
  const [family, part] = key.split(":");
  for (const human of [`${family}, 0, 1, 60| 2, 1|| {${part}}|`, `1, 0, 1, 60| 2, 1|| {${key}}|`, `1, 0, 1, 60| 2, 1|| {${family}:[${part}, ${part}]}|`]) {
    assert.equal(detectDlc(human).dlc, label, human);
  }
}
assert.equal(detectDlc("2, 0, 1, 60| 2, 1|| {1}|").dlc, "Base Game");
assert.equal(detectDlc("2, 0, 1, 60| 2, 1|| {6:78} {2:80}|").dlc, "Mixed DLC");
const fields = submitFieldsFromCard({}, {deserialized:"6, 0, 1, 60| 2, 1|| {78}|"});
assert.equal(fields.dlc, "Stone Demon");
assert.equal(applySubmitFields({dlc:"Harmonica"},fields).dlc,"Harmonica");
console.log("PASS GZO DLC contract: all part mappings, short/pair/list forms, mixed packs, manual override");
