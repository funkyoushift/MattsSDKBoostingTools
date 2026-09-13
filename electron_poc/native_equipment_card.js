"use strict";
const {reference} = require("./native_item_sources");
const TYPES = new Set(["Shield","Ordnance","Repkit","Enhancement","Classmod","Class Mod"]);
const truth = value => value === true || value === "true";
function localized(value) {
  return String(value || "").replace(/^[^,]*,\s*[a-f0-9]{16,32},\s*/i,"");
}
function iconUrl(value) {
  const asset = String(value || "").match(/'\/Game\/(uiresources\/[^']+)'/i)?.[1];
  return asset ? "coui://" + asset.split(".")[0] + ".png" : "";
}
function buildEquipmentCard(card,data,api) {
  if (!data || !TYPES.has(card.item_type)) return null;
  const ctx = api.buildStatContext(data,{set:card.set,partKeys:card.part_keys,partRoots:card.part_roots,level:card.level,element:card.element});
  const missing = new Set(), values = {};
  const attr = ref => {
    const key = reference(ref,"attribute") || String(ref || "").toLowerCase();
    const value = api.resolveAttribute(key,ctx);
    if (!Number.isFinite(value)) {missing.add(key);return null;}
    values[key] = value;return value;
  };
  const format = node => {
    if (!node) return "";
    if (/NumericDisplayValue/.test(node.structtype || "")) {
      // This requests the native modifier accumulator, not the final property.
      // Keep it explicitly unresolved until its display semantics are captured.
      if (truth(node.bshowstatmodifier)) {
        missing.add("modifier_display:" + reference(node.attributedef,"attribute"));
        return "—";
      }
      let value = attr(node.attributedef);
      if (value == null) return "—";
      if (truth(node.bdisplayasoneminus)) value = 1 - value;
      // Reduction math expresses a multiplicative bonus as its fractional change.
      if (truth(node.bcalculatewithreductionmath) && value > 0) value -= 1;
      if (node.signstyle === "OppositeSign") value *= -1;
      if (node.signstyle === "Positive") value = Math.abs(value);
      if (node.signstyle === "Negative") value = -Math.abs(value);
      if (truth(node.bdisplayaspercentage)) value *= 100;
      if (node.roundingmode === "RoundToInt") value = Math.round(value);
      if (node.roundingmode === "FloorToInt") value = Math.floor(value);
      if (node.roundingmode === "CeilToInt") value = Math.ceil(value);
      const decimals = Number.isFinite(Number(node.maximumfractionaldigits)) ? Number(node.maximumfractionaldigits) : 1;
      let text = value.toLocaleString("en-US",{maximumFractionDigits:Math.max(0,Math.min(decimals,6))});
      if (truth(node.bdisplayplussign) && value > 0) text = "+" + text;
      if (truth(node.bdisplayaspercentage)) text += "%";
      return truth(node.buseformattext) && node.formattext ? localized(node.formattext).replaceAll("$VALUE$",text) : text;
    }
    if (!/StringDisplayValue/.test(node.structtype || "")) {missing.add("display:"+(node.structtype || "unknown"));return "—";}
    let text = localized(node.formattext);
    const pairs = node.argsmap?.pairs || {};
    for (const row of Object.values(pairs)) if (row?.key && text.includes("{"+row.key+"}"))
      text = text.replaceAll("{"+row.key+"}",format(row.value));
    return text.replace(/\{[^{}]+\}/g,token=>{missing.add("argument:"+token);return "—";});
  };
  const condition = cond => {
    if (!cond?.attributedef) return true;
    const value = attr(cond.attributedef), compare = Number(cond.comparevalue || 0);
    if (value == null) return false;
    switch(cond.comparetype || "Equal") {
      case "Equal":return value===compare;case "NotEqual":return value!==compare;
      case "GreaterThan":return value>compare;case "GreaterOrEqual":return value>=compare;
      case "LessThan":return value<compare;case "LessOrEqual":return value<=compare;
      default:missing.add("condition:"+cond.comparetype);return false;
    }
  };
  const refs = [...ctx.assembled.uiStats.map(row=>row.reference)];
  const excluded = new Set();
  for(const row of ctx.assembled.aspects) {
    refs.push(...(row.definition.uistatstoinclude || []));
    for(const ref of row.definition.uistatstoexclude || []) excluded.add(reference(ref,"ui_stat"));
  }
  const groups = {};
  for(const key of new Set(refs.map(ref=>reference(ref,"ui_stat")))) {
    if(excluded.has(key))continue;
    const stat = data.uiStats.get(key);
    if(!stat){missing.add("ui_stat:"+key);continue;}
    if(!condition(stat.displaycondition))continue;
    const group = reference(stat.displaygroup,"ui_stat_group");
    (groups[group] ||= []).push({ident:key,image:iconUrl(stat.staticon),value:format(stat.statvalue),
      loc_text:format(stat.statlabel),comparison:"",priority:Number(stat.sortingpriority || 0)});
  }
  for(const rows of Object.values(groups))rows.sort((a,b)=>a.priority-b.priority);
  // A repair kit's headline is the sum of its initial and timed healing. The
  // shared BalanceFormula evaluator's nonzero-offset behavior is not yet
  // validated, so use the two independently resolved native heal attributes.
  if (card.item_type === "Repkit" && groups.headline?.length) {
    const instant=attr("repair_kit_health_instant_value"),timed=attr("repair_kit_health_over_time_value");
    const total=instant == null || timed == null ? null : instant+timed;
    values.calc_ui_repair_kit_health_total=total;
    groups.headline[0].value=total == null ? "—" : Math.round(total).toLocaleString("en-US");
  }
  // Native class-mod parts add points to graph nodes. Preserve repeated tier
  // parts, but show one icon with their summed rank for each distinct node.
  const passives=new Map(),skillIcons=new Map();
  for(const tree of data.skillTrees?.values() || []) {
    const walk=node=>{
      if(!node || typeof node!=="object")return;
      if(node.progressgraph && node.tiers) for(const tier of node.tiers)
        for(const skill of tier.nodes || [])skillIcons.set(reference(node.progressgraph,"progress_graph")+":"+skill.name,{...skill,hunter:tree.vaulthuntername});
      for(const child of Object.values(node))if(typeof child==="object")walk(child);
    };
    walk(tree);
  }
  const graphNode=(graph,name,seen=new Set())=>{
    if(seen.has(graph))return {};
    seen.add(graph);
    const def=data.progressGraphs?.get(graph);
    if(!def)return {};
    const inherited=graphNode(reference(def.parent,"progress_graph"),name,seen);
    return {...inherited,...Object.values(def.nodes?.pairs || {}).find(row=>row?.key===name)?.value};
  };
  for(const row of ctx.assembled.aspects)if(/ClassModPassivesAspect/.test(row.definition.structtype || "")) {
    for(const passive of row.definition.passives || []) {
      const graph=reference(passive.progressgraph,"progress_graph"),key=graph+":"+passive.nodename;
      const skill=skillIcons.get(key),definition=graphNode(graph,passive.nodename);
      const points=Number(row.definition.points);
      if(!Number.isFinite(points)){missing.add("passive_points:"+key);continue;}
      if(!skill?.icon)missing.add("passive_icon:"+key);
      const current=passives.get(key) || {ident:key,image:iconUrl(skill?.icon),name:definition.alias || passive.nodename,points:0,hunter:skill?.hunter,comparison:""};
      current.points+=points;passives.set(key,current);
    }
  }
  if(passives.size)groups.primary=[...passives.values()].map(row=>({...row,value:"+"+row.points}));
  // Price is an item formula, with every repeated part's native price modifier.
  const priceRef = ctx.assembled.sources.filter(row=>row.kind==="item").map(row=>row.definition.monetaryvalue?.attribute).filter(Boolean).at(-1);
  let price = priceRef ? attr(priceRef) : null;
  for(const ref of ctx.priceModAttrs) {
    const factor = attr(ref);
    price = price != null && factor != null ? price*factor : null;
  }
  if(price != null)price=Math.fround(Math.min(2147483647,Math.round(price)));
  const type = groups.typeline?.[0];
  return {groups,values,price,type_label:type?.value || card.item_type,thumbnail:type?.image || "",missing:[...missing]};
}
module.exports = {TYPES,buildEquipmentCard,localized,iconUrl};
