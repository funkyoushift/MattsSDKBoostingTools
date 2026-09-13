"use strict";
const assert = require("node:assert/strict");
const path = require("node:path");
const s = require("./serial_card_stats");
const {loadResolver} = require("./serial_card_resolve");
const sourceRoot = path.resolve(__dirname,"..");
const data = s.loadStatData({sourceRoot}), resolver = loadResolver({sourceRoot});
const context = card => s.buildStatContext(data,{set:card.set,partKeys:card.part_keys,partRoots:card.part_roots,level:card.level});
const near = (value,expected,tolerance,label) => assert.ok(Number.isFinite(value) && Math.abs(value-expected)<=tolerance,`${label}: ${value} != ${expected}`);

// Independent read-only native property capture; not generated calculator output.
const native = require("./fixtures/item_cards/roulette_native_reference.json");
const roulette = resolver.resolveFromHuman(native.human), rouletteContext = context(roulette);
assert.equal(roulette.display_name,native.display_name);
for (const [key,value] of Object.entries(native.base_values))
  near(s.resolveAttribute(key,rouletteContext),value,key === "weapon_damage" ? .01 : .00001,key);

const ichorReference = require("./fixtures/item_cards/ichor_native_reference.json");
const ichorContext = context(resolver.resolveFromHuman(ichorReference.human));
for (const [key,value] of Object.entries(ichorReference.base_values))
  near(s.resolveAttribute(key,ichorContext),value,Math.max(.00001,Math.abs(value)*.000001),`Ichor ${key}`);
assert.equal(ichorContext.statModifiers.pointGroups.get("inventory").get("damage"),84.5);
assert.equal(ichorContext.statModifiers.pointGroups.get("use_mode").get("damage"),34);

// User screenshots supply these display values. Unproven screenshot fields
// (Draupner accuracy, selected perks) are intentionally not goldens.
const fixtures = require("./fixtures/item_cards/mixed_order_user.json");
for (const [index,title,damage,rate,dps,price] of [
  [6,"Zealous Regulated Bubbles",541,12.8,270000,546842560],
  [11,"Zealous Regulated Draupner",646,6.9,178000,472383232]
]) {
  const card = resolver.resolveFromHuman(fixtures[index].human);
  assert.equal(card.display_name,title);
  assert.equal(card.damage,damage); assert.equal(card.fire_rate,rate);
  assert.equal(card.reload,1.7); assert.equal(card.crit,533);
  assert.equal(card.damage_radius,199);
  near(card.magazine,9779000,500,"magazine display rounding");
  near(card.dps,dps,500,"DPS display rounding");
  near(card.value,price,price*.00001,"price floating-point tolerance");
}
const ichor = resolver.resolveFromHuman(fixtures[1].human);
const shockBubbles = resolver.resolveFromHuman(fixtures[10].human);
assert.equal(shockBubbles.element_dps,654);
assert.equal(shockBubbles.element_chance,10);
assert.equal(shockBubbles.element_text,"654 DMG/s | 10% Chance");
assert.equal(ichor.display_name,"Zealous Extolled Ichor");
assert.equal(ichor.value,2147483648);
near(ichor.magazine,20000000,500000,"Ichor magazine display rounding");
assert.equal(ichor.damage_radius,4153);
near(ichor.dps,6569000000,500000,"Ichor screenshot DPS display rounding");

// Default modifier enum is ScaleAdd; duplicates add before multiplication.
const bag = new Map();
s.addModifier(bag,"attribute'ammo'",undefined,.25);
s.addModifier(bag,"attribute'ammo'","ScaleAdd",.25);
s.addModifier(bag,"attribute'ammo'","ScaleMultiply",2);
assert.equal(s.applyMods(20,bag.get("ammo")),60);
const ctx = {tables:new Map(),attributes:new Map(),cache:new Map(),resolving:new Set(),injected:{negative:-2},propertyBases:new Map(),modifiers:new Map()};
assert.equal(s.resolveValueNode({constant:3,postscale:2},ctx),6);
ctx.attributes.set("absolute",{value:{structtype:"GbxConditionalAttributeValueResolver",defaultvalue:{attribute:"attribute'negative'"},conditionalvalues:[{condition:{type:"ValueResolver",inlinestruct:{expression:{formula:"attr(negative)<0"}}},value:{attribute:"attribute'negative'",postscale:-1}}]}});
assert.equal(s.resolveAttribute("absolute",ctx),2);
console.log("PASS native card math: runtime base properties, screenshot names/combat/magazine/radius, repeated price modifiers, capped price, conditional formulas.");
