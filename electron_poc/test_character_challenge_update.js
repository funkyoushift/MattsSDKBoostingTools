"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../external_app/v22_parts_codes_fixed/matt_editor/js/item-editor-10-yaml-save.js"), "utf8");
function extract(name, nextName) {
  const start = source.indexOf(`function ${name}(`);
  const end = source.indexOf(`function ${nextName}(`, start);
  assert(start >= 0 && end > start);
  return source.slice(start, end);
}
const data = { stats: { challenge: { siren_levelup: 91 }, untouched: { custom: 7 } } };
let writes = 0;
const context = vm.createContext({
  window: {},
  getYamlDataFromTextarea: () => data,
  setYamlDataToTextarea: () => { writes += 1; },
  isOpenWorldMiscPathParts: () => false,
});
vm.runInContext(extract("setDeepStatPathParts", "stripOpenworldMiscLeaves"), context);
vm.runInContext(extract("setDeepStatOnStatsRoot", "upsertStateChallengeObjective"), context);
vm.runInContext(extract("completeCharacterChallenges", "completeEnemiesChallenges"), context);
vm.runInContext("completeCharacterChallenges()", context);
assert.equal(writes, 1);
assert.equal(data.stats.challenge.siren_levelup, 91);
assert.equal(data.stats.challenge.exo_levelup, 50);
assert.equal(data.stats.cowbell_challenges.characters.robodealer_levelup, 50);
assert.equal(data.stats.cowbell_challenges.characters.robodealer_cleromancy_tiered, 1000);
assert.equal(data.stats.harmonica_challenges.dlc2_characters.corpohacker_levelup, 60);
assert.equal(data.stats.harmonica_challenges.dlc2_characters.corpohacker_vpn_tiered, 1000);
assert.equal(data.stats.challenge.corpohacker_levelup, undefined);
assert.equal(data.stats.untouched.custom, 7);
context.window.NEXUS_CHALLENGE_BY_NAME = {
  current: { associatedstat: "stats.harmonica_challenges.dlc2_characters.corpohacker_levelup", goalValue: 70 },
  other: { associatedstat: "stats.challenge.getcash", goalValue: 99999 },
};
vm.runInContext("completeCharacterChallenges()", context);
assert.equal(data.stats.harmonica_challenges.dlc2_characters.corpohacker_levelup, 70);
assert.equal(data.stats.challenge.getcash, undefined);
console.log("PASS character challenges cover six classes, preserve higher counters, and use current Nexus goals");
