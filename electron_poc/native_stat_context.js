"use strict";

const {assembleItemDefinitions} = require("./native_item_sources");
const {collectStatModifiers} = require("./native_stat_modifiers");

function className(ref) { return String(ref || "").split(".").pop().replace(/'$/, ""); }
function propertyValue(object, propertyPath) {
  let value = object;
  for (const part of String(propertyPath || "").split(".")) {
    if (!value || typeof value !== "object") return undefined;
    const key = Object.keys(value).find(key => key.toLowerCase() === part.toLowerCase());
    if (key == null) return undefined;
    value = value[key];
  }
  return value;
}

function createNativeContext(data, item, api) {
  const assembled = assembleItemDefinitions(data, item);
  const ctx = {
    tables:data.tables, attributes:data.attributes, statusDefaults:data.statusDefaults,
    element:String(item.element || "").toLowerCase(), cache:new Map(), resolving:new Set(),
    injected:{weapon_level:Number(item.level),weapon_wear:0,weapon_rust:0,weapon_dirt:0,weapon_sun_damage:0},
    // The additive critical property starts at zero in the captured native
    // DamageModifierData; item and stat modifiers then contribute separately.
    propertyBases:new Map([["weapon_damage_modifier_add_critical_hit",0],["weapon_shot_cost",1],["weapon_projectile_per_shot",1]]),
    modifiers:new Map(), priceModAttrs:[], assembled, errors:[...assembled.errors], unresolved:[]
  };
  const priorities = Object.fromEntries(Object.entries(data.behaviorRules?.enums?.EInventoryAspectSelectionPriority || {})
    .map(([value,name]) => [name,Number(value)]));
  const priority = row => priorities[row.definition.selectionpriority || "Default"] ?? 0;
  const parents = data.behaviorRules?.behaviorParents || {};
  const itemClass = assembled.sources.filter(row=>row.kind==="item").map(row=>className(row.definition.class)).filter(Boolean).at(-1);
  const itemDefaults = data.equipmentDefaults?.classes?.[itemClass];
  if (itemDefaults) for (const [key,attribute] of data.attributes) {
    const resolver = className(attribute.context?.structtype);
    const relevant = resolver === "InventoryContextResolver" || resolver === "ShieldAttributeContextResolver" && itemClass === "Shield"
      || resolver === "RepairKitContextResolver" && itemClass === "RepairKit" || resolver === "EnhancementContextResolver" && itemClass === "Enhancement";
    const property = String(attribute.value?.property?.propertypath || "").toLowerCase();
    if(relevant && Number.isFinite(itemDefaults[property]))ctx.propertyBases.set(key,itemDefaults[property]);
  }
  function isA(child, parent) {
    const seen = new Set();
    while (child && !seen.has(child)) {
      if (child === parent) return true;
      seen.add(child); child = parents[child];
    }
    return false;
  }
  const aspects = assembled.aspects.filter(row => !Number(row.definition.usemodebitmask || 0) || Number(row.definition.usemodebitmask) & 1);
  const behaviorCandidates = aspects.filter(row => row.definition.behavior && row.definition.bremovefromusemodes !== "true")
    .sort((a,b) => priority(b)-priority(a));
  // Primary use modes select the first highest-priority behavior. Attribute
  // contexts resolve through its actual extracted class inheritance.
  for (const [key, attribute] of data.attributes) {
    if (!/PropertyValueResolver/.test(attribute.value?.structtype || "")) continue;
    const wanted = className(attribute.context?.behaviortypetofurtherresolveto);
    if (!wanted) continue;
    const candidate = behaviorCandidates.find(row => isA(className(row.definition.behavior.behaviorclass), wanted)
      && propertyValue(row.definition.behavior,attribute.value.property?.propertypath) !== undefined);
    if (!candidate) continue;
    const node = propertyValue(candidate.definition.behavior,attribute.value.property.propertypath);
    const value = api.resolveValueNode(node,ctx);
    if (Number.isFinite(value)) ctx.propertyBases.set(key,value);
    else ctx.unresolved.push({source:candidate.source,attribute:key,reason:"behavior_value"});
    ctx.cache.clear();
  }
  // Attribute effects are applied in native aspect-priority order. Keep every
  // occurrence; later lower-priority override effects remain meaningful.
  const effects = [];
  for (const row of [...aspects].sort((a,b) => priority(b)-priority(a))) {
    for (const effect of row.definition.attributeeffects || []) effects.push({...effect,source:row.source});
    for (const mode of row.definition.usemodeattributeeffects || []) {
      if (mode.usemodebitmask != null && !(Number(mode.usemodebitmask) & 1)) continue;
      for (const effect of mode.attributeeffects || []) effects.push({...effect,source:row.source});
    }
  }
  // Resolve initialization values against the unmodified weapon, then install
  // the modifiers together. This avoids order-dependent cache contamination.
  const resolved = effects.map(effect => ({...effect,value:api.resolveValueNode(effect.modifiervalue,ctx)}));
  for (const effect of resolved) {
    if (Number.isFinite(effect.value)) api.addModifier(ctx.modifiers,effect.attributetomodify,effect.modifiertype,effect.value);
    else ctx.unresolved.push({source:effect.source,attribute:effect.attributetomodify,reason:"modifier_value"});
  }
  ctx.cache.clear();
  ctx.statModifiers = collectStatModifiers(assembled,data,node => api.resolveValueNode(node,ctx));
  for (const modifier of ctx.statModifiers.modifiers)
    api.addModifier(ctx.modifiers,modifier.attributetomodify,modifier.modifiertype,modifier.modifiervalue.constant);
  ctx.errors.push(...ctx.statModifiers.errors);
  for (const source of assembled.sources) {
    const price = source.definition.monetaryvaluemodifier;
    if (price?.attribute) ctx.priceModAttrs.push(price.attribute);
  }
  ctx.cache.clear();
  return ctx;
}

module.exports = {createNativeContext,className,propertyValue};
