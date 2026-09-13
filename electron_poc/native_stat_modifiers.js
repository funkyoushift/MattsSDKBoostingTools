"use strict";

const {reference} = require("./native_item_sources");

// Native StatModifierAspect -> inv_stat conversion. This is separate from
// behavior selection and character/equipment buffs. The supplied resolver must
// read extracted table cells; missing inputs remain errors rather than zeroes.
function collectStatModifiers(assembled, data, resolveValue, useMode = 0) {
  const errors = [], ignored = [], points = new Map(), modifiers = [];
  const pointGroups = new Map([["inventory",new Map()],["use_mode",new Map()]]);
  const mask = 1 << useMode;
  const rarityKeys = [...new Set(assembled.sources.map(source => reference(source.definition.rarity, "rarity")).filter(Boolean))];
  let rarityScale = null;
  const rarityScales = [];
  for (const rarityKey of rarityKeys) {
    const rarity = data.rarities.get(rarityKey);
    const handle = rarity?.raritybalancetablerowhandle;
    const scale = handle && rarity.statmultipliercolumnname
      ? resolveValue({datatablevalue:{...handle,columnname:rarity.statmultipliercolumnname}}) : null;
    if (!Number.isFinite(scale)) errors.push(`Missing rarity stat scale: ${rarityKey}`);
    else rarityScales.push(scale);
  }
  if (rarityScales.length && new Set(rarityScales).size === 1 && !errors.length) rarityScale = rarityScales[0];
  else errors.push("Missing or conflicting rarity stat scales");
  for (const row of assembled.aspects) {
    const aspect = row.definition;
    const useModeMask = Number(aspect.usemodebitmask || 0);
    if (useModeMask && !(useModeMask & mask)) continue;
    const group = pointGroups.get(useModeMask ? "use_mode" : "inventory");
    for (const modifier of aspect.statmodifiers || []) {
      const tag = String(modifier.stattagname || "").toLowerCase();
      if (!tag || tag === "none") {ignored.push({source:row.source,reason:"No stat tag"}); continue;}
      const value = resolveValue(modifier.modifiervalue);
      if (!Number.isFinite(value)) {errors.push(`Unresolved stat amount: ${row.source}:${tag}`); continue;}
      points.set(tag, (points.get(tag) || 0) + value);
      group.set(tag, (group.get(tag) || 0) + value);
    }
  }
  if (!assembled.stats) errors.push("Missing native stat definition");
  // Inventory-wide and use-mode stat bonuses form separate conversions. The
  // mixed Ichor native reference verifies their products for damage and radius;
  // flattening the points first loses both multipliers' cross term.
  if (Number.isFinite(rarityScale)) for (const [group,groupPoints] of pointGroups) for (const [key, definition] of assembled.stats?.attributes || []) {
    const stat = String(definition.stat || "").toLowerCase();
    const amount = groupPoints.get(stat);
    if (amount == null || amount === 0) continue;
    const scalar = resolveValue(definition.stattoattributemodifierscalar);
    const base = definition.basemultiplier == null ? 1 : resolveValue(definition.basemultiplier);
    if (!Number.isFinite(scalar) || !Number.isFinite(base)) {errors.push(`Missing stat conversion: ${key}`); continue;}
    const type = definition.modifiertype || "ScaleMultiply";
    const delta = amount * rarityScale * scalar * base;
    const zeroIsBetter = String(definition.bzeroisbetter).toLowerCase() === "true";
    const additive = ["PreAdd", "PostAdd", "ScaleAdd"].includes(type);
    const value = additive ? (zeroIsBetter ? -delta : delta) : Math.max(0, 1 + (zeroIsBetter ? -delta : delta));
    if (!definition.definition) {errors.push(`Missing attribute for stat: ${key}`); continue;}
    // The read-only Roulette reference has zero spread/sway when stat points
    // exceed the zero-is-better range, rather than a negative property value.
    modifiers.push({key,group,stat,amount,rarityScale,scalar,base,attributetomodify:definition.definition,
      modifiertype:type,modifiervalue:{constant:value},roundingMode:definition.roundingmode || "None"});
  }
  return {rarity:rarityKeys[0] || "",rarityScale,points,pointGroups,modifiers,ignored,errors};
}

module.exports = {collectStatModifiers};
