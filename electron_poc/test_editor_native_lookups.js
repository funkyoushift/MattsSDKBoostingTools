"use strict";

// Exercise the browser's actual lookup helpers against the bundled native tables.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const editor = path.join(__dirname, "..", "external_app", "v22_parts_codes_fixed", "matt_editor");
const source = fs.readFileSync(path.join(editor, "js", "legit-builder", "legit-builder.js"), "utf8");
const context = vm.createContext({
  window: {}, Map, Set,
  NEXUS_COSMETIC_TAG_PREFIX: "Reward.Item.Cosmetic.",
  buildUitooltipStatsDescriptionRaw: () => "",
  assetPathToUiresourcesUrl: asset => asset,
});

function loadSection(startMarker, endMarker) {
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert.ok(start >= 0 && end > start, `Missing helper section: ${startMarker}`);
  vm.runInContext(source.slice(start, end), context);
}
loadSection("        function mapUnlockMethodTokenToProfilePrefix(", "        /** Nexus uiname/displayname:");
loadSection("        function mergeSkilltreesIntoData(", "        /** Merge uitooltipdata");
loadSection("        function normalizeSkilltreeNodeKey(", "        /** uitooltipdata StringDisplayValue");
loadSection("        function findDepEntryForTableItem(", "        function loadData()");

function table(name) {
  return JSON.parse(fs.readFileSync(path.join(editor, "LegitItems", `Nexus-Data-${name}.json`), "utf8"));
}
const residents = [0, 4, 6].map(suffix => table(`Resident${suffix}`));
const expectedLoveless = [
  "Head41_StarAlien", "Head42_SpaceDog", "Head43_Warrior", "Head44_FishBowl",
  "Skin78_Alien", "Skin79_Robot", "Skin80_Star", "Skin81_Warp", "Skin82_Eruption",
];
for (const ordered of [residents, [...residents].reverse()]) {
  const parents = new Map();
  ordered.forEach(payload => context.collectResidentCosmeticParents(payload, parents));
  const ids = new Set();
  ordered.forEach(payload => context.extractCosmeticUnlockIdsFromResident(payload, ids, parents));
  const loveless = [...ids].filter(id => id.startsWith("Unlockable_CorpoHacker."));
  assert.equal(loveless.length, 127, "Every native Loveless cosmetic must retain its character parent");
  expectedLoveless.forEach(id => assert.ok(ids.has(`Unlockable_CorpoHacker.${id}`), id));
  for (const [character, count] of Object.entries({ DarkSiren: 125, ExoSoldier: 125, Gravitar: 125, Paladin: 125, RoboDealer: 126 })) {
    assert.equal([...ids].filter(id => id.startsWith(`Unlockable_${character}.`)).length, count, character);
  }
  // The same reward exists for Vex too; correcting Loveless must preserve it.
  assert.ok(ids.has("Unlockable_DarkSiren.Head41_StarAlien"));
}

const partial = { unlockable: { records: [{ entries: [{
  unlockable_corpohacker: null,
  __dep_entries: [{ head_test: {
    entry: "Head_Test", unlockmethod: "Unlockable_DarkSiren, copied localization",
    typetag: { tagname: "Reward.Item.Cosmetic.PlayerHead" },
  } }],
}] }] } };
const canonical = { unlockable: { records: [{ entries: [{
  unlockable_corpohacker: { unlockable: "Unlockable_CorpoHacker" },
}] }] } };
const parents = context.collectResidentCosmeticParents(canonical);
const partialIds = new Set();
context.extractCosmeticUnlockIdsFromResident(partial, partialIds, parents);
assert.deepEqual([...partialIds], ["Unlockable_CorpoHacker.Head_Test"]);

const skillData = { skilltreesNodeByGraphAndName: new Map(), uitooltipByKey: new Map() };
const nativeEmptyNodeKeys = new Set();
[0, 4].forEach(suffix => {
  const payload = table(`skilltrees_data${suffix}`);
  context.mergeSkilltreesIntoData(skillData, payload);
  for (const record of payload.skilltrees_data.records) {
    for (const entry of record.entries || []) {
      for (const tree of Object.values(entry)) {
        for (const branch of tree?.skilltrees || []) {
          for (const segment of branch.segments || []) {
            for (const tier of segment.tiers || []) {
              for (const node of tier.nodes || []) {
                if (node.name && node.nodetype === "None" && !node.tooltip && !node.icon) {
                  nativeEmptyNodeKeys.add(context.normalizeSkilltreeNodeKey(segment.progressgraph, node.name));
                }
              }
            }
          }
        }
      }
    }
  }
});
const graphChunks = [0, 4, 6].map(suffix => ({ data: table(`progress_graph${suffix}`) }));
skillData.skilltreeNodeAliases = context.collectSkilltreeNodeAliases(graphChunks);
[0, 4, 6].forEach(suffix => {
  const payload = table(`uitooltipdata${suffix}`);
  for (const record of payload.uitooltipdata?.records || []) {
    for (const entry of record.entries || []) {
      for (const [key, value] of Object.entries(entry)) {
        if (value && typeof value === "object") skillData.uitooltipByKey.set(key.toLowerCase(), value);
      }
    }
  }
});
const refs = new Map();
function visit(value) {
  if (!value || typeof value !== "object") return;
  if (Array.isArray(value.passives)) {
    for (const passive of value.passives) {
      if (passive?.progressgraph && passive?.nodename) {
        refs.set(context.normalizeSkilltreeNodeKey(passive.progressgraph, passive.nodename), passive);
      }
    }
  }
  Object.values(value).forEach(visit);
}
[0, 4, 6].forEach(suffix => visit(table(`inv${suffix}`)));
assert.equal(refs.size, 612);
const unresolved = [];
let lovelessResolved = 0;
for (const [key, passive] of refs) {
  const info = context.getSkilltreeNodeInfo(skillData, passive.progressgraph, passive.nodename);
  if (!info) { unresolved.push(key); continue; }
  assert.equal(
    context.getSkilltreeNodeInfo(skillData, passive.progressgraph.toUpperCase(), ` ${passive.nodename.toUpperCase()} `),
    info, `Case-insensitive skill lookup: ${key}`,
  );
  if (key.includes("corpohacker")) lovelessResolved++;
}
assert.equal(lovelessResolved, 98, "All Loveless passive positions with native metadata should resolve");
assert.equal(unresolved.filter(key => nativeEmptyNodeKeys.has(key)).length, 43);
assert.deepEqual(unresolved.filter(key => !nativeEmptyNodeKeys.has(key)).sort(), [
  "progress_exo_branch_remoteagent_01|branch - row 1 - 1",
  "progress_exo_trunk_gimmick|trunk - row 1 - 2",
  "progress_grav_trunk_stasisshard|trunk - row 1 - 2",
  "progress_grav_trunk_stasisshard|trunk - row 3 - 2",
], "Native empty positions must retain the existing fallback instead of invented metadata");
const rearmItem = { aspects: [{ passives: [{
  progressgraph: "progress_graph'Progress_PLD_Branch_Calamity_02'", nodename: "Branch - Row 3 - 1",
}] }] };
assert.equal(context.getSkillInfoForPassive(rearmItem, skillData).name, "Rearm");
assert.match(context.getPassiveUiresourcesIconUrl(rearmItem, skillData), /paladin_rearm/);
const fakeGraph = [{ data: { progress_graph: { records: [{ entries: [{ demo: {
  nodes: { pairs: {
    a: { key: "Visible", value: { itemdata: { skill: "skill'One'" } } },
    b: { key: "Hidden", value: { itemdata: { skill: "skill'Two'" } } },
  } },
} }] }] } } }];
assert.equal(context.collectSkilltreeNodeAliases(fakeGraph).size, 0, "Different native skills cannot alias");

let release = context.getReleaseNewPartSets();
assert.equal(release.serialIds.size + release.partKeys.size + release.typeIds.size, 0);
context.window.bl4ReleaseNewParts = {
  serialIds: ["402:1"], partKeys: [" New_Part "], typeIds: [402],
};
release = context.getReleaseNewPartSets();
assert.ok(release.serialIds.has("402:1"));
assert.ok(release.partKeys.has("new_part"));
assert.ok(release.typeIds.has("402"));
assert.ok(!release.serialIds.has("1:51"), "An older release badge must not survive manifest replacement");
context.window.bl4ReleaseNewParts = {
  serialIds: new Set(["402:2"]), partKeys: new Set(["NEW_OTHER"]), typeIds: new Set([403]),
};
release = context.getReleaseNewPartSets();
assert.ok(release.serialIds.has("402:2") && release.partKeys.has("new_other") && release.typeIds.has("403"));
const badgeStart = source.indexOf("const partIdStr = part.rootSerial != null ?");
const badgeEnd = source.indexOf("const newBadge =", badgeStart);
assert.ok(badgeStart >= 0 && badgeEnd > badgeStart);
vm.runInContext(`function partHasNewBadge(part) {
  const releaseNewParts = getReleaseNewPartSets();
  const newSerialIds = releaseNewParts.serialIds;
  const newPartKeys = releaseNewParts.partKeys;
  ${source.slice(badgeStart, badgeEnd)}
  return Boolean(isNewPart);
}`, context);
context.window.bl4ReleaseNewParts = {
  serialIds: new Set(["1:51"]), partKeys: new Set(["new_part"]), typeIds: new Set([1]),
};
assert.ok(context.getReleaseNewPartSets().typeIds.has("1"));
assert.equal(context.partHasNewBadge({ rootSerial: 1, serial: 1, partKey: "existing_part" }), false,
  "A type with an added part must not mark its existing parts as new");
assert.equal(context.partHasNewBadge({ rootSerial: 1, serial: 51, partKey: "new_serial" }), true);
assert.equal(context.partHasNewBadge({ rootSerial: 2, serial: 1, partKey: "NEW_PART" }), true);

// Run the actual unlocked selector, including its body classification and final filtering.
const guidelines = fs.readFileSync(path.join(editor, "js", "item-editor", "ui", "guidelines-ui.js"), "utf8");
const selectorStart = guidelines.indexOf("            const getAvailablePartsForCategory =");
const selectorEnd = guidelines.indexOf("                // Build partsByCategory dynamically", selectorStart);
assert.ok(selectorStart >= 0 && selectorEnd > selectorStart);
let selectedTypeId = 2;
const selectorContext = vm.createContext({
  window: {}, Set, Map,
  document: { getElementById: () => ({ value: String(selectedTypeId) }) },
  console: { log() {}, warn() {} },
  typeIdMap: new Map([[2, { category: "Weapon" }], [263, { category: "Grenades" }],
    [402, { category: "Class Mod" }], [404, { category: "Class Mod" }],
    [9999, { category: "Class Mod" }]]),
  partsByTypeId: new Map(), currentParts: [],
});
vm.runInContext(fs.readFileSync(path.join(editor, "js", "item-editor", "data", "local-game-part-supplement.js"), "utf8"), selectorContext);
const nativeParts = selectorContext.window.MSBT_LOCAL_GAME_PART_SUPPLEMENT;
for (const root of [402, 404]) {
  const entry = nativeParts.find(part => part.typeId === root && part.partType === "class_mod_body");
  assert.ok(entry, `Native class body for ${root}`);
  selectorContext.partsByTypeId.set(root, [{ ...entry, id: String(entry.partId), path: entry.source }]);
}
for (const [root, category] of [[2, "Weapon"], [263, "Grenades"], [9999, "Class Mod"]]) {
  selectorContext.partsByTypeId.set(root, [{
    id: "1", fullId: `${root}:1`, typeId: root, category,
    name: "Fixture body", partType: "body", spawnCode: "fixture.body", path: "",
  }]);
}
const selectorBody = guidelines.slice(selectorStart, selectorEnd);
vm.runInContext(selectorBody + "\n}; globalThis.nativeBodySelector = getAvailablePartsForCategory;", selectorContext);
for (const root of [2, 263]) {
  selectedTypeId = root;
  const bodies = selectorContext.nativeBodySelector("body", true);
  assert.ok(bodies.some(part => part.typeId === root), "Valid bodies must remain selectable");
  assert.ok(!bodies.some(part => [402, 404, 9999].includes(part.typeId)),
    "Known and metadata-defined class mod bodies must stay out of weapon/grenade choices");
}
selectedTypeId = 402;
assert.ok(selectorContext.nativeBodySelector("body", true).some(part => part.typeId === 402),
  "The class mod body must remain available in its own selector");
selectorContext.typeIdMap.delete(402);
selectorContext.typeIdMap.delete(404);
selectedTypeId = 2;
assert.ok(!selectorContext.nativeBodySelector("body", true).some(part => [402, 404].includes(part.typeId)),
  "Known current class IDs must remain protected while category metadata is unavailable");
console.log(`editor native lookups passed: 127 Loveless cosmetics, ${refs.size - unresolved.length} passive references resolved; ${unresolved.length} native empty positions retain fallback`);
