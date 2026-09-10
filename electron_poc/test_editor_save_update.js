"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const yaml = require("js-yaml");

const editor = path.resolve(__dirname, "../external_app/v22_parts_codes_fixed/matt_editor");
const source = fs.readFileSync(path.join(editor, "js/item-editor-10-yaml-save.js"), "utf8");

function definition(name) {
  const pattern = new RegExp(`^        (?:async )?function ${name}\\(`, "m");
  const start = source.search(pattern);
  const end = source.indexOf("\n        }", start);
  assert(start >= 0 && end > start, `missing function ${name}`);
  return source.slice(start, end + "\n        }".length);
}

function nativeRows(family) {
  const out = {};
  for (const shard of [0, 4, 6]) {
    const data = JSON.parse(fs.readFileSync(path.join(editor, `LegitItems/Nexus-Data-${family}${shard}.json`), "utf8"));
    for (const table of Object.values(data)) {
      for (const record of table.records || []) {
        for (const entry of record.entries || []) {
          for (const [key, value] of Object.entries(entry)) {
            if (key.startsWith('__') || !value || typeof value !== 'object' || Array.isArray(value)) continue;
            // Later Nexus shards may supply only changed fields for an existing definition.
            out[key] = { ...out[key], ...value };
          }
        }
      }
    }
  }
  return out;
}

async function main() {
  let text = yaml.dump({
    state: {
      class: "Char_CorpoHacker",
      inventory: { sentinel: "unchanged" },
      experience: [
        { type: "Character", level: 60, points: 1234567 },
        { type: "Specialization", level: 5, points: 7123456789 },
        { type: "Other_Track", level: 8, points: 9 }
      ]
    }
  });
  const read = () => yaml.load(text);
  const messages = [];
  const elements = new Map();
  function element(tagName) {
    const node = {
      tagName, style: {}, children: [], listeners: {},
      appendChild(child) { this.children.push(child); if (child.id) elements.set(child.id, child); },
      addEventListener(type, callback) { this.listeners[type] = callback; },
      querySelectorAll() { return []; }
    };
    return node;
  }
  elements.set("edit-values-inputs", element("div"));
  const context = vm.createContext({
    DEBUG: false, console, window: {},
    PRESET_CHARACTER_MAX_LEVEL: 70, PRESET_SPECIALIZATION_MAX_LEVEL: 701,
    PRESET_UVHM_MAX_LEVEL: 7, PRESET_MAYHEM_MAX_LEVEL: 20, ITEM_MAX_LEVEL: 70,
    getYamlDataFromTextarea: read,
    setYamlDataToTextarea(data, options) { text = yaml.dump(data); messages.push(options); },
    showSaveStatus(...args) { messages.push(args); },
    document: { getElementById: id => elements.get(id) || null, createElement: element },
    setTimeout(callback) { callback(); }, clearTimeout() {},
    alert(message) { throw new Error(message); }
  });
  for (const name of [
    "getCurrentValue", "setExperiencePoints", "setCharacterLevel", "setCharacterToMaxLevel",
    "setSpecializationLevel", "unlockAllSpecialization", "unlockMaxEverything",
    "renderEditValues", "updatePresetInputs", "lockPresetControls", "unlockPresetControls",
    "profileDataParseBlackMarketRow", "profileDataApplyBlackMarketItems"
  ]) vm.runInContext(definition(name), context);

  context.setCharacterLevel(70);
  context.setSpecializationLevel(701);
  let entries = read().state.experience;
  assert.strictEqual(entries[0].level, 70);
  assert.strictEqual(entries[0].points, 1234567);
  assert.strictEqual(entries[1].level, 701);
  assert.strictEqual(entries[1].points, 7123456789);
  assert.deepStrictEqual(entries[2], { type: "Other_Track", level: 8, points: 9 });
  assert.deepStrictEqual(read().state.inventory, { sentinel: "unchanged" });
  const validText = text;
  for (const level of [0, 71, 1.5, NaN]) context.setCharacterLevel(level);
  for (const level of [0, 702, 1.5, NaN]) context.setSpecializationLevel(level);
  assert.strictEqual(text, validText, "invalid direct level calls must not mutate saves");

  context.setExperiencePoints("Character", 0);
  context.setExperiencePoints("Specialization", 8123456789);
  assert.strictEqual(read().state.experience[0].level, 70);
  assert.strictEqual(read().state.experience[0].points, 0);
  assert.strictEqual(read().state.experience[1].level, 701);
  assert.strictEqual(read().state.experience[1].points, 8123456789);
  const explicitText = text;
  for (const points of [-1, 1.2, NaN, Number.MAX_SAFE_INTEGER + 1]) context.setExperiencePoints("Character", points);
  context.setExperiencePoints("Other_Track", 100);
  assert.strictEqual(text, explicitText, "invalid XP input must not round or change other tracks");
  await context.unlockMaxEverything();
  assert.strictEqual(read().state.experience[0].points, 0, "max preset preserves explicit zero XP");
  assert.strictEqual(read().state.experience[1].points, 8123456789, "max preset preserves specialization XP");
  assert(messages.some(row => row.successMessage && row.successMessage.includes("XP points preserved")));

  context.renderEditValues();
  const charXp = elements.get("preset-input-character-xp");
  const specXp = elements.get("preset-input-specialization-xp");
  assert(charXp && specXp, "both point fields must be rendered");
  assert.strictEqual(charXp.value, 0);
  assert.strictEqual(specXp.value, 8123456789);
  context.lockPresetControls();
  assert.strictEqual(charXp.disabled, true);
  context.unlockPresetControls();
  assert.strictEqual(charXp.disabled, false);
  charXp.value = "7654321";
  charXp.listeners.change.call(charXp);
  assert.strictEqual(read().state.experience[0].points, 7654321, "point field saves explicit input");
  assert.strictEqual(read().state.experience[0].level, 70);
  text = yaml.dump({ state: { experience: [{ type: "Character", level: 12, points: 9988 }] } });
  context.setSpecializationLevel(10);
  assert.deepStrictEqual(read().state.experience[1], { type: "Specialization", level: 10, points: 0 });
  assert.strictEqual(read().state.experience[0].points, 9988);

  for (const value of [undefined, null, "", "  ", "invalid"]) {
    assert.strictEqual(context.profileDataParseBlackMarketRow({ blackmarket_gamestage: value }).gamestage, 70);
    const data = { domains: { local: { shared: { currencies: { cash: 123 } } } } };
    context.profileDataApplyBlackMarketItems(data, [{ itemcomp: "classmod_corpohacker.comp_01_common", gamestage: value }]);
    assert.strictEqual(data.domains.local.shared.blackmarket_items[0].blackmarket_gamestage, 70);
    assert.strictEqual(data.domains.local.shared.currencies.cash, 123);
  }
  for (const level of [1, 50, 60, 61, 70]) {
    assert.strictEqual(context.profileDataParseBlackMarketRow({ blackmarket_gamestage: level }).gamestage, level);
    const data = {};
    context.profileDataApplyBlackMarketItems(data, [{ itemcomp: "classmod_corpohacker.comp_01_common", gamestage: level }]);
    assert.strictEqual(data.domains.local.shared.blackmarket_items[0].blackmarket_gamestage, level);
  }
  assert.strictEqual(context.profileDataParseBlackMarketRow(null).gamestage, 70);

  const missionSets = nativeRows("missionset");
  const nativeMissions = nativeRows("Mission");
  const nativeRegions = nativeRows("game_region");
  const unref = value => String(value || "").replace(/^[^']*'/, "").replace(/'$/, "").toLowerCase();
  const manifest = {};
  for (const [key, mission] of Object.entries(nativeMissions)) {
    const set = unref(mission.missionset);
    if (!set) continue;
    if (!manifest[set]) manifest[set] = { missions: {} };
    manifest[set].missions[key] = { worldregion: mission.worldregion };
  }
  context.window.NEXUS_MISSION_MANIFEST = manifest;
  for (const name of [
    "missionSetKeyIsCowbellDlcContent", "missionSetDlcLocation", "missionSetKeyIsDlcContent",
    "missionSetGroupAndLocation", "collectMissionsetKeysForZone", "augmentMissionTemplatesWithNexusStubs",
    "mergeMissionsetsByKeyList", "mergedSetKeysTouchCowbellOpenworld", "completeDlcMissionsBulk",
    "templateMissionsetKeys", "completeZoneMissionsBulk",
    "resetLocalSetsMatching", "resetDlcMissionsBulk", "resetZoneMissionsBulk"
  ]) vm.runInContext(definition(name), context);

  const harmonica = Object.keys(missionSets).filter(key => unref(missionSets[key].dlc) === "dlcdef_harmonica");
  assert(harmonica.length >= 18, "test must cover the current native Harmonica mission sets");
  for (const key of harmonica) {
    assert.strictEqual(context.missionSetDlcLocation(key), "Providence", key);
    assert.strictEqual(context.missionSetGroupAndLocation(key).groupName, "DLC Missions", key);
  }
  for (const [key, set] of Object.entries(missionSets)) {
    if (set.bisdlcmissionset === "true") assert.strictEqual(context.missionSetKeyIsDlcContent(key), true, `native DLC classification: ${key}`);
  }
  assert(missionSets.missionset_dlc_viola, "BP5 definition must exist in native data");
  assert.strictEqual(context.missionSetGroupAndLocation("missionset_dlc_viola").location, "Bounty Pack 5: Amara and the Vile Shadows");
  assert.strictEqual(context.missionSetKeyIsDlcContent("missionset_main_grasslands1"), false);
  assert.strictEqual(context.missionSetKeyIsDlcContent("missionset_main_harmonicatutorial"), false);
  for (const region of Object.keys(nativeRegions).filter(key => key.startsWith("harmonica_") || key.startsWith("viola_"))) {
    manifest.missionset_side_region_probe = { missions: { probe: { worldregion: `game_region'${region}'` } } };
    assert.strictEqual(context.missionSetDlcLocation("missionset_side_region_probe"), region.startsWith("harmonica_") ? "Providence" : "Bounty Pack 5: Amara and the Vile Shadows");
  }
  delete manifest.missionset_side_region_probe;
  const completableHarmonica = harmonica.filter(key => manifest[key] && Object.keys(manifest[key].missions).length);
  assert(completableHarmonica.length >= 16, "test must exercise current static Harmonica mission assignments");
  assert(!completableHarmonica.includes('missionset_dlc2_npcmoments'), "dynamic NPC moments have no static mission assignment");
  const picked = Array.from(context.collectMissionsetKeysForZone("providence", Object.keys(missionSets))).sort();
  assert.deepStrictEqual(picked, harmonica.sort());
  assert.deepStrictEqual(Array.from(context.collectMissionsetKeysForZone("bp5", Object.keys(missionSets))), ["missionset_dlc_viola"]);

  const baseSet = "missionset_main_grasslands1";
  let cowbellCalls = 0;
  let finalCalls = 0;
  context.getMissionTemplateDataForMerge = async () => ({
    [baseSet]: { missions: { keep: { status: "completed" } } },
    missionset_main_cowbell: { missions: { cowbell: { status: "completed" } } }
  });
  context.applyCowbellSpeakeasyPortalOpenworldStats = () => { cowbellCalls += 1; };
  context.applyNexusRememberedFinalsToLocalSets = () => { finalCalls += 1; };
  text = yaml.dump({ state: { inventory: { sentinel: true } }, missions: { local_sets: {
    [baseSet]: { status: "Active" },
    missionset_dlc2_npcmoments: { status: "Active", missions: { generated_existing: { status: "Active" } } }
  } } });
  await context.completeDlcMissionsBulk();
  for (const key of [...completableHarmonica, "missionset_dlc_viola"]) assert.strictEqual(read().missions.local_sets[key].status, "completed", `DLC complete omitted ${key}`);
  assert.strictEqual(read().missions.local_sets.missionset_dlc2_npcmoments.status, "Active", "do not invent dynamic NPC mission completion data");
  assert.strictEqual(read().missions.local_sets[baseSet].status, "Active", "DLC action must preserve base-game story");
  assert.strictEqual(cowbellCalls, 1);
  assert.strictEqual(finalCalls, 1);
  const beforeReset = text;
  context.resetZoneMissionsBulk("providence");
  for (const key of harmonica) assert(!read().missions.local_sets[key]);
  assert(read().missions.local_sets.missionset_dlc_viola, "Providence reset must preserve BP5");
  text = beforeReset;
  context.resetDlcMissionsBulk();
  for (const key of [...harmonica, "missionset_dlc_viola"]) assert(!read().missions.local_sets[key]);
  assert.strictEqual(read().missions.local_sets[baseSet].status, "Active");
  assert.deepStrictEqual(read().state.inventory, { sentinel: true });
  await context.completeZoneMissionsBulk('providence');
  for (const key of completableHarmonica) assert(read().missions.local_sets[key]);
  assert(!read().missions.local_sets.missionset_dlc_viola, "Providence completion must preserve BP5 progress");
  await context.completeZoneMissionsBulk('bp5');
  assert.strictEqual(read().missions.local_sets.missionset_dlc_viola.status, 'completed');
  console.log(`PASS editor save update: explicit XP, max preset preservation, Black Market70 defaults, ${harmonica.length} Providence sets (${completableHarmonica.length} static completion templates), BP5 and native region grouping`);
}

main().catch(error => { console.error(error); process.exitCode = 1; });
