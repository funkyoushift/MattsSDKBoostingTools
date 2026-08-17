const assert = require("assert");
const { applySelectionGesture, selectionGestureFlags } = require("./list_selection");
const { filterEnemyActors, isEnemyActor } = require("./enemy_actor_filter");
const catalog = require("./dev_spawner_catalog.json");

const keys = ["a", "b", "c", "d"];
let result = applySelectionGesture({ selected: new Set(), orderedKeys: keys, key: "b" });
assert.deepStrictEqual([...result.selected], ["b"]);
result = applySelectionGesture({
  selected: result.selected, orderedKeys: keys, key: "d", anchor: result.anchor, shift: true
});
assert.deepStrictEqual([...result.selected], ["b", "c", "d"]);
result = applySelectionGesture({
  selected: result.selected, orderedKeys: keys, key: "c", anchor: result.anchor, toggle: true
});
assert.deepStrictEqual([...result.selected], ["b", "d"]);

// Select Multiple off: a plain click stays single-select.
assert.deepStrictEqual(selectionGestureFlags({}), { toggle: false, shift: false });
assert.deepStrictEqual(selectionGestureFlags({ ctrlKey: true }), { toggle: true, shift: false });
assert.deepStrictEqual(selectionGestureFlags({ metaKey: true }), { toggle: true, shift: false });
// Select Multiple on: a plain click toggles, and Shift still ranges.
assert.deepStrictEqual(selectionGestureFlags({ multiSelect: true }), { toggle: true, shift: false });
assert.deepStrictEqual(
  selectionGestureFlags({ multiSelect: true, shiftKey: true }),
  { toggle: true, shift: true }
);

const modeKeys = ["a", "b", "c", "d"];
function clickInMode(selected, key, anchor, event = {}, multiSelect = false) {
  const flags = selectionGestureFlags({ ...event, multiSelect });
  return applySelectionGesture({ selected, orderedKeys: modeKeys, key, anchor, ...flags });
}

let single = clickInMode(new Set(), "a", "");
single = clickInMode(single.selected, "c", single.anchor);
assert.deepStrictEqual([...single.selected], ["c"], "plain clicks replace the selection when the mode is off");

let multi = clickInMode(new Set(), "a", "", {}, true);
multi = clickInMode(multi.selected, "c", multi.anchor, {}, true);
multi = clickInMode(multi.selected, "d", multi.anchor, {}, true);
assert.deepStrictEqual([...multi.selected], ["a", "c", "d"], "plain clicks accumulate when the mode is on");
multi = clickInMode(multi.selected, "c", multi.anchor, {}, true);
assert.deepStrictEqual([...multi.selected], ["a", "d"], "clicking a selected row removes it when the mode is on");
// Shift range keeps earlier picks while the mode is on.
let ranged = clickInMode(new Set(), "b", "", {}, true);
ranged = clickInMode(ranged.selected, "d", ranged.anchor, { shiftKey: true }, true);
assert.deepStrictEqual([...ranged.selected], ["b", "c", "d"]);

assert.strictEqual(isEnemyActor("artillery_payload", catalog), false);
assert.strictEqual(isEnemyActor("Audio_IO_Cowbell_Main1_Moment_PicklesDeath", catalog), false);
assert.strictEqual(isEnemyActor("Char_Gadget_AutoTurret_Base", catalog), false);
assert.strictEqual(isEnemyActor("Char_NPC_NudgeCouncil04", catalog), false);
assert.strictEqual(isEnemyActor("Char_ArmyBandit_SHARED", catalog), true);

const allActors = Array.from(new Set([
  ...Object.values(catalog.categories || {}).flat(),
  ...Object.keys(catalog.display_names || {}),
  ...Object.keys(catalog.actor_metadata || {}),
  ...Object.keys(catalog.spawn_metadata || {})
]));
const enemies = filterEnemyActors(allActors, catalog);
assert(enemies.length > 500, "enemy filter should retain a useful combat catalog");
assert(enemies.length < allActors.length / 2, "enemy filter should remove non-character catalog noise");
assert(!enemies.some((name) => /audio|payload|gadget|turret/i.test(name)));

console.log(`selection and enemy filter tests passed (${enemies.length}/${allActors.length} retained)`);
