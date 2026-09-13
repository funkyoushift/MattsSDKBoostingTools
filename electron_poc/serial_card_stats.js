"use strict";

/**
 * Phase B — offline weapon card stats from mined Nexus data only.
 *
 * Game paths mirrored (do not invent):
 * - BalanceFormulaValueResolver: Multiplier * (Level ^ Power) * Scalar + Offset
 *   (Gbx ValueFormula; field wiring from Nexus attribute defs)
 * - PropertyValueResolver leaves from assembled part behaviors (FireRate, Damage, …)
 * - inv_aspect attributeeffecttemplate expansion (Resident column→attribute maps)
 * - GbxExpressionValueResolver / GbxConditionalAttributeValueResolver from attribute JSON
 * - weapon_dps_estimate expression from Nexus-Data-attribute0.json
 *
 * Leaves null when a required mined resolver/input cannot be evaluated.
 */

const fs = require("fs");
const path = require("path");

const GUN_TYPES = new Set([
  "Pistol",
  "Shotgun",
  "Assault Rifle",
  "SMG",
  "Sniper",
  "Heavy Weapon",
  "Heavy Gun Ordnance"
]);

function readJson(filePath) {
  try {
    if (!filePath || !fs.existsSync(filePath)) return null;
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function attrKey(ref) {
  if (ref == null) return "";
  const s = String(ref);
  const m = s.match(/attribute'([^']+)'/i) || s.match(/^'?([^']+)'?$/);
  return String(m ? m[1] : s).trim().toLowerCase();
}

function aspectKey(ref) {
  if (ref == null) return "";
  const s = String(ref);
  const m = s.match(/inv_aspect'([^']+)'/i);
  return String(m ? m[1] : s).trim().toLowerCase();
}

function normalizeDatatableName(ref) {
  if (!ref || typeof ref !== "string") return "";
  return ref.replace(/^gbx_ue_data_table'/i, "").replace(/'$/, "").trim();
}

function parseNum(x) {
  if (x == null || x === "") return NaN;
  if (typeof x === "number" && Number.isFinite(x)) return x;
  const n = parseFloat(String(x));
  return Number.isFinite(n) ? n : NaN;
}

function loadKeyedRecords(legitItems, filePrefix, rootKey) {
  const map = new Map();
  if (!legitItems || !fs.existsSync(legitItems)) return map;
  for (const name of fs.readdirSync(legitItems)) {
    if (!name.startsWith(filePrefix) || !name.endsWith(".json")) continue;
    const payload = readJson(path.join(legitItems, name));
    if (!payload) continue;
    const roots = rootKey ? [rootKey] : Object.keys(payload);
    for (const rk of roots) {
      const block = payload[rk];
      if (!block || !Array.isArray(block.records)) continue;
      for (const rec of block.records) {
        for (const ent of rec.entries || []) {
          if (!ent || typeof ent !== "object") continue;
          for (const [k, v] of Object.entries(ent)) {
            if (k.startsWith("__") || v == null) continue;
            // DLC reference-only records must not erase a concrete base row.
            if (typeof v !== "object" || Array.isArray(v)) continue;
            const fields = Object.keys(v).filter(field => !field.startsWith("__") && field !== rk);
            if (!fields.length && map.has(String(k).toLowerCase())) continue;
            map.set(String(k).toLowerCase(), v);
          }
        }
      }
    }
  }
  return map;
}

function loadDatatables(legitItems, rowDefaultsPath) {
  /** @type {Map<string, Map<string, Record<string, number>>>} */
  const tables = new Map();
  const rowDefaults = readJson(rowDefaultsPath || path.join(legitItems, "native_table_row_defaults.json"))?.definitions || {};
  const raw = loadKeyedRecords(legitItems, "Nexus-Data-gbx_ue_data_table", "gbx_ue_data_table");
  for (const [tableName, entry] of raw) {
    const rows = new Map();
    const rowStruct = rowDefaults[String(entry.row_struct || "").toLowerCase()] || {};
    const floatColumns = new Set((rowStruct.properties || [])
      .filter(property => property.Type === "FloatProperty")
      .map(property => normalizeDatatableColumnKey(property.Name) || String(property.Name).toLowerCase()));
    for (const row of entry.data || []) {
      if (!row || row.row_name == null) continue;
      // Cooked Nexus rows omit cells equal to their Unreal row-struct default.
      // Populate only defaults actually extracted from that exact struct.
      const cells = {};
      const defaults = rowStruct.defaults || {};
      for (const [ck, cv] of Object.entries(defaults)) {
        if (typeof cv === "number" && Number.isFinite(cv)) cells[normalizeDatatableColumnKey(ck) || String(ck).toLowerCase()] = cv;
      }
      const rv = row.row_value || {};
      for (const [ck, cv] of Object.entries(rv)) {
        const n = parseNum(cv);
        if (!Number.isNaN(n)) cells[normalizeDatatableColumnKey(ck) || String(ck).toLowerCase()] = n;
      }
      for (const key of floatColumns) if (Object.hasOwn(cells, key)) cells[key] = Math.fround(cells[key]);
      rows.set(String(row.row_name).toLowerCase(), cells);
    }
    tables.set(tableName.toLowerCase(), rows);
  }
  return tables;
}

function loadInvRoots(legitItems) {
  /** @type {Map<string, { root: object, parts: Map<string, object> }>} */
  const bySet = new Map();
  if (!legitItems || !fs.existsSync(legitItems)) return bySet;

  const ensure = (rootKey) => {
    const key = String(rootKey || "").toLowerCase();
    if (!key) return null;
    if (!bySet.has(key)) bySet.set(key, { root: null, parts: new Map() });
    return bySet.get(key);
  };

  const ingestDeps = (bucket, entry) => {
    if (!bucket) return;
    for (const dep of entry.__dep_entries || []) {
      if (!dep || typeof dep !== "object") continue;
      for (const [pk, part] of Object.entries(dep)) {
        if (
          pk.startsWith("__")
          || pk === "depTableName"
          || pk === "depTableId"
          || pk === "depIndex"
        ) {
          continue;
        }
        if (!part || typeof part !== "object") continue;
        const partKey = String(pk).toLowerCase();
        if (!bucket.parts.has(partKey)) bucket.parts.set(partKey, part);
      }
    }
  };

  for (const name of fs.readdirSync(legitItems)) {
    if (!name.startsWith("Nexus-Data-inv") || !name.endsWith(".json")) continue;
    if (name.includes("inv_name") || name.includes("inv_stat") || name.includes("inv_custom")) continue;
    const payload = readJson(path.join(legitItems, name));
    const records = (((payload || {}).inv || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        // Live root body (ord_ps: { ... }) and null wrappers (ord_ps: null + __dep_entries)
        // both carry part aspects; uniques like Roulette live on the null wrappers.
        for (const [k, v] of Object.entries(entry)) {
          if (k.startsWith("__")) continue;
          const bucket = ensure(k);
          if (!bucket) continue;
          if (v && typeof v === "object") bucket.root = bucket.root || v;
          ingestDeps(bucket, entry);
          if (v && typeof v === "object") ingestDeps(bucket, v);
        }
      }
    }
  }
  return bySet;
}

/**
 * Nexus dumps store friendly cell keys (firerate_value). Inv behavior graphs often
 * still reference the cooked UE export name (FireRate_Value_36_<32-hex GUID>).
 * Strip that suffix so PropertyValueResolver datatable leaves resolve.
 */
function normalizeDatatableColumnKey(columnName) {
  const raw = String(columnName || "").trim().toLowerCase();
  if (!raw || raw === "none") return "";
  const stripped = raw.replace(/_\d+_[0-9a-f]{32}$/i, "");
  return stripped || raw;
}

function getDatatableCell(tables, tableRef, rowName, columnName) {
  const tableName = normalizeDatatableName(tableRef).toLowerCase();
  if (!tableName || tableName === "none") return null;
  const table = tables.get(tableName);
  if (!table) return null;
  const wantRow = String(rowName || "").toLowerCase();
  let row = table.get(wantRow);
  if (!row && wantRow) {
    for (const [rk, rv] of table) {
      if (rk.toLowerCase() === wantRow) {
        row = rv;
        break;
      }
    }
  }
  if (!row) return null;
  const ck = String(columnName || "").toLowerCase();
  if (!ck || ck === "none") {
    const vals = Object.values(row);
    return vals.length === 1 ? vals[0] : null;
  }
  if (Object.prototype.hasOwnProperty.call(row, ck)) return row[ck];
  const friendly = normalizeDatatableColumnKey(ck);
  if (friendly && Object.prototype.hasOwnProperty.call(row, friendly)) return row[friendly];
  for (const [k, v] of Object.entries(row)) {
    const lk = k.toLowerCase();
    if (lk === ck || (friendly && lk === friendly)) return v;
    if (lk.startsWith(`${ck}_`) || (friendly && lk.startsWith(`${friendly}_`))) return v;
  }
  return null;
}

function cloneEffect(effect, templateDt) {
  const out = JSON.parse(JSON.stringify(effect));
  const patchValue = (node) => {
    if (!node || typeof node !== "object") return;
    if (node.datatablevalue && typeof node.datatablevalue === "object") {
      if (templateDt.datatable) node.datatablevalue.datatable = templateDt.datatable;
      if (templateDt.rowname) node.datatablevalue.rowname = templateDt.rowname;
    }
    for (const v of Object.values(node)) {
      if (v && typeof v === "object") patchValue(v);
    }
  };
  patchValue(out.modifiervalue);
  return out;
}

function expandTemplateEffects(aspectDef, templateModValue) {
  const dt = (((templateModValue || {}).datatablevalue) || {});
  if (!dt.datatable && !dt.rowname) return [];
  const effects = [];
  for (const block of aspectDef.usemodeattributeeffects || []) {
    for (const eff of block.attributeeffects || []) {
      effects.push(cloneEffect(eff, dt));
    }
  }
  for (const eff of aspectDef.attributeeffects || []) {
    effects.push(cloneEffect(eff, dt));
  }
  return effects;
}

function collectEffectsFromAspect(aspect, invAspects, sink) {
  if (!aspect || typeof aspect !== "object") return;
  if (String(aspect.battributeeffecttemplateset || "").toLowerCase() === "true") {
    const parent = aspectKey(aspect.parent);
    const def = invAspects.get(parent);
    const templateVal = (aspect.attributeeffecttemplate || {}).modifiervalue;
    if (def && templateVal) {
      for (const eff of expandTemplateEffects(def, templateVal)) sink.push(eff);
    }
  }
  for (const block of aspect.usemodeattributeeffects || []) {
    for (const eff of block.attributeeffects || []) sink.push(eff);
  }
  for (const eff of aspect.attributeeffects || []) sink.push(eff);
}

function walkBehaviorBindings(aspect, sink) {
  const behavior = aspect && aspect.behavior;
  if (!behavior || typeof behavior !== "object") return;
  const map = {
    firerate: "weapon_fire_rate",
    damage: "weapon_damage",
    reloadtime: "weapon_reload_time",
    maxloadedammo: "weapon_max_loaded_ammo",
    projectilespershot: "weapon_projectile_per_shot",
    chargetime: "weapon_charge_time",
    shotammocost: "weapon_shot_cost"
  };
  for (const [prop, attr] of Object.entries(map)) {
    if (behavior[prop] != null) {
      sink.push({
        attr,
        value: behavior[prop],
        postscale: parseNum(behavior[prop].postscale)
      });
    }
  }
}

function emptyMods() {
  return { override: null, preAdd: [], scales: [], postAdd: [], scaleSimple: [] };
}

function addModifier(bag, attr, modType, value) {
  if (!attr || value == null || Number.isNaN(value)) return;
  const key = attrKey(attr);
  if (!key) return;
  if (!bag.has(key)) bag.set(key, emptyMods());
  const slot = bag.get(key);
  const t = String(modType || "").toLowerCase();
  if (t === "overridebasevalue" || t === "override") slot.override = value;
  else if (t === "preadd") slot.preAdd.push(value);
  else if (t === "postadd") slot.postAdd.push(value);
  else if (t === "scaleadd" || t === "scalesimple" || !t) slot.scaleSimple.push(value);
  else if (t === "scalemultiply" || t === "scale" || t === "premultiply") {
    slot.scales.push(value);
  }
}

function applyMods(base, mods) {
  let v = base;
  if (mods.override != null && !Number.isNaN(mods.override)) v = mods.override;
  if (v == null || Number.isNaN(v)) return null;
  for (const a of mods.preAdd) v += a;
  for (const s of mods.scales) v *= s;
  v *= 1 + mods.scaleSimple.reduce((sum, value) => sum + value, 0);
  for (const a of mods.postAdd) v += a;
  return v;
}

function resolveValueNode(node, ctx, depth = 0) {
  if (node == null || depth > 24) return null;
  if (typeof node === "number") return node;
  if (typeof node === "string") {
    const n = parseNum(node);
    return Number.isNaN(n) ? null : n;
  }
  if (typeof node !== "object") return null;

  if (
    node.constant != null
    && (node.datatablevalue == null || normalizeDatatableName(node.datatablevalue.datatable) === "none")
  ) {
    const c = parseNum(node.constant);
    if (!Number.isNaN(c)) {
      const ps = parseNum(node.postscale);
      return Number.isNaN(ps) ? c : c * ps;
    }
  }
  if (node.datatablevalue && typeof node.datatablevalue === "object") {
    const cell = getDatatableCell(
      ctx.tables,
      node.datatablevalue.datatable,
      node.datatablevalue.rowname,
      node.datatablevalue.columnname
    );
    if (cell != null) {
      const ps = parseNum(node.postscale);
      return Number.isNaN(ps) ? cell : cell * ps;
    }
  }
  if (node.attribute) {
    const v = resolveAttribute(attrKey(node.attribute), ctx, depth + 1);
    if (v != null) {
      const ps = parseNum(node.postscale);
      return Number.isNaN(ps) ? v : v * ps;
    }
  }
  return null;
}

function evalBalanceFormula(valueDef, ctx, depth) {
  if (!valueDef || typeof valueDef !== "object") return null;
  const mult = resolveValueNode(valueDef.multiplier, ctx, depth + 1);
  const level = resolveValueNode(valueDef.level, ctx, depth + 1);
  const power = resolveValueNode(valueDef.power, ctx, depth + 1);
  const scalar = valueDef.scalar != null ? resolveValueNode(valueDef.scalar, ctx, depth + 1) : 1;
  const offset = valueDef.offset != null ? resolveValueNode(valueDef.offset, ctx, depth + 1) : 0;
  if (mult == null || level == null || power == null) return null;
  const s = scalar == null || Number.isNaN(scalar) ? 1 : scalar;
  const o = offset == null || Number.isNaN(offset) ? 0 : offset;
  return mult * (level ** power) * s + o;
}

function evalExpression(expr, ctx, depth) {
  if (expr == null) return null;
  if (typeof expr === "string") {
    const replaced = expr.replace(/attr\(([^)]+)\)/gi, (_, name) => {
      const v = resolveAttribute(attrKey(name), ctx, depth + 1);
      return v == null ? "NaN" : String(v);
    });
    if (/NaN/.test(replaced)) return null;
    if (!/^[\d\s.+\-*/()<>=!&|]+$/.test(replaced)) return null;
    try {
      // eslint-disable-next-line no-new-func
      const v = Function(`"use strict"; return (${replaced});`)();
      return typeof v === "boolean" ? Number(v) : Number.isFinite(v) ? v : null;
    } catch {
      return null;
    }
  }
  if (typeof expr === "object" && expr.formula) {
    const vars = {};
    const pairs = ((((expr.variables || {}).variablevalues || {}).pairs) || {});
    for (const pair of Object.values(pairs)) {
      if (!pair || !pair.key) continue;
      const raw = pair.value && pair.value.value ? pair.value.value : pair.value;
      let v = null;
      if (raw && raw.type === "Attribute") {
        v = resolveAttribute(attrKey(raw.value), ctx, depth + 1);
      } else {
        v = resolveValueNode(raw, ctx, depth + 1);
      }
      if (v == null) return null;
      vars[pair.key] = v;
    }
    let formula = String(expr.formula).replace(/attr\(([^)]+)\)/gi, (_, name) => {
      const value = resolveAttribute(attrKey(name), ctx, depth + 1);
      return value == null ? "NaN" : String(value);
    });
    for (const [k, v] of Object.entries(vars)) {
      formula = formula.replace(new RegExp(`\\b${k}\\b`, "g"), String(v));
    }
    if (!/^[\d\s.+\-*/()<>=!&|]+$/.test(formula)) return null;
    try {
      // eslint-disable-next-line no-new-func
      const v = Function(`"use strict"; return (${formula});`)();
      if (typeof v === "boolean") return v ? 1 : 0;
      return Number.isFinite(v) ? v : null;
    } catch {
      return null;
    }
  }
  return null;
}

function evalConditional(valueDef, ctx, depth) {
  for (const row of valueDef.conditionalvalues || []) {
    const cond = row.condition || {};
    let ok = false;
    if (cond.externalattribute) {
      const v = resolveAttribute(attrKey(cond.externalattribute), ctx, depth + 1);
      ok = Boolean(v);
    } else if (cond.type === "ValueResolver" && cond.inlinestruct) {
      const v = evalExpression(cond.inlinestruct.expression, ctx, depth + 1);
      ok = Boolean(v);
    }
    if (ok) return resolveValueNode(row.value, ctx, depth + 1);
  }
  if (valueDef.defaultvalue) return resolveValueNode(valueDef.defaultvalue, ctx, depth + 1);
  return 0;
}

/** Wear/dirt/rust/sun live in InventoryStatsContainer; offline cards treat unset as 0 (new item). */
const WEAR_CONTAINER_DEFAULTS = {
  weapon_wear: 0,
  weapon_rust: 0,
  weapon_dirt: 0,
  weapon_sun_damage: 0
};

function priceAttrForItemType(itemType) {
  switch (String(itemType || "")) {
    case "Pistol":
      return "attr_calc_price_gun_pistol";
    case "Shotgun":
      return "attr_calc_price_gun_shotgun";
    case "Assault Rifle":
      return "attr_calc_price_gun_assault";
    case "SMG":
      return "attr_calc_price_gun_smg";
    case "Sniper":
      return "attr_calc_price_gun_sniper";
    case "Heavy Weapon":
    case "Heavy Gun Ordnance":
      return "attr_calc_price_heavy_weapon";
    default:
      return "";
  }
}

function resolveAttribute(name, ctx, depth = 0) {
  const key = attrKey(name);
  if (!key || depth > 32) return null;
  if (ctx.cache.has(key)) return ctx.cache.get(key);
  if (ctx.resolving.has(key)) return null;
  ctx.resolving.add(key);

  let base = null;
  if (Object.prototype.hasOwnProperty.call(ctx.injected, key)) {
    base = ctx.injected[key];
  } else if (ctx.propertyBases.has(key)) {
    base = ctx.propertyBases.get(key);
  } else {
    const def = ctx.attributes.get(key);
    const valueDef = def && def.value;
    const st = String((valueDef && valueDef.structtype) || "");
    if (valueDef) {
      if (/BalanceFormulaValueResolver/i.test(st)) {
        base = evalBalanceFormula(valueDef, ctx, depth);
      } else if (/GbxExpressionValueResolver/i.test(st)) {
        base = evalExpression(valueDef.expression, ctx, depth);
      } else if (/GbxConditionalAttributeValueResolver/i.test(st)) {
        base = evalConditional(valueDef, ctx, depth);
      } else if (/OakStatusEffectApplicationDefaultsValueResolver/i.test(st)) {
        // These table cells are structured status-application records, not
        // ordinary numeric columns. Only the resolved primary element is known.
        if (!Number(valueDef.index || 0) && ctx.element) {
          const row = ctx.statusDefaults?.data?.find(row => String(row.row_name).toLowerCase() === ctx.element);
          const field = row?.row_value?.[String(valueDef.property || "").toLowerCase()];
          const value = parseNum(field?.value);
          if (Number.isFinite(value)) base = Math.fround(value);
        }
      } else if (/GbxConstantAttributeValueResolver/i.test(st)) {
        base = resolveValueNode(valueDef.attributeinit || valueDef, ctx, depth);
      } else if (/PropertyValueResolver/i.test(st)) {
        base = ctx.propertyBases.has(key) ? ctx.propertyBases.get(key) : null;
      } else if (/BalanceStateValueResolver/i.test(st)) {
        if (
          /ExperienceLevel/i.test(String(valueDef.valuetoresolve || ""))
          && ctx.injected.weapon_level != null
        ) {
          base = ctx.injected.weapon_level;
        }
      } else if (/InventoryStatsContainerValueResolver/i.test(st)) {
        // Accuracy UI weights / sway weights need live inv_stat containers — leave null.
        // Wear attrs are injected as 0 for offline sell (see WEAR_CONTAINER_ATTRS).
        base = Object.prototype.hasOwnProperty.call(ctx.injected, key)
          ? ctx.injected[key]
          : null;
      } else if (valueDef.constant != null || valueDef.datatablevalue || valueDef.attribute) {
        base = resolveValueNode(valueDef, ctx, depth);
      }
    }
  }

  const mods = ctx.modifiers.get(key) || emptyMods();
  const final = applyMods(base, mods);
  ctx.cache.set(key, final);
  ctx.resolving.delete(key);
  return final;
}

function buildStatContext(data, item) {
  return require("./native_stat_context").createNativeContext(data, item, {resolveValueNode, addModifier});
}

function roundStat(value, mode) {
  if (value == null || Number.isNaN(value)) return null;
  if (mode === "int") return Math.round(value);
  if (mode === "1") return Math.round(value * 10) / 10;
  return value;
}

function evaluateWeaponCardStats(card, data) {
  const empty = {
    dps: null,
    damage: null,
    accuracy: null,
    reload: null,
    fire_rate: null,
    magazine: null,
    crit: null,
    value: null,
    stats_ok: false,
    stats_source: "none",
    stats_blocked: []
  };
  if (!card || !GUN_TYPES.has(card.item_type)) return empty;
  if (!data || !card.set || !Array.isArray(card.part_keys) || !card.part_keys.length) {
    return { ...empty, stats_blocked: ["missing_set_or_parts"] };
  }

  const levelMatch = String(card.human || "").match(/^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*(\d+)/);
  const level = Number(card.level != null ? card.level : (levelMatch ? levelMatch[1] : NaN));
  if (!Number.isFinite(level) || level <= 0) {
    return { ...empty, stats_blocked: ["missing_level"] };
  }

  const ctx = buildStatContext(data, {
    set: card.set,
    partKeys: card.part_keys,
    partRoots: card.part_roots,
    element: card.element,
    level
  });

  const blocked = [...ctx.errors];
  const need = (name, label) => {
    const v = resolveAttribute(name, ctx, 0);
    if (v == null || Number.isNaN(v)) blocked.push(label || name);
    return v;
  };

  const damage = need("weapon_damage", "weapon_damage");
  const fireRate = need("weapon_compare_burst_fire_rate", "fire_rate");
  const reload = need("weapon_compare_reload_time", "reload");
  const magazine = need("weapon_compare_shots_until_reload", "magazine");
  const dps = need("weapon_dps_estimate", "dps");
  const crit = resolveAttribute("weapon_damage_modifier_add_critical_hit", ctx, 0);
  const accuracy = resolveAttribute("weapon_accuracy_ui_compare", ctx, 0);
  const elementDps = card.element ? resolveAttribute("weapon_ui_elemental_dps",ctx) : null;
  const elementChance = card.element ? resolveAttribute("weapon_damage_modifier_base_status_effect_chance",ctx) : null;
  const namingFactors = {};
  const namingAttrs = data.globals?.get("def_globals_oak_inventory")?.inventorynamingattributes?.pairs || {};
  for (const row of Object.values(namingAttrs)) {
    const key = attrKey(row.value);
    const mods = ctx.modifiers.get(key) || emptyMods();
    // Naming uses the assembled modifier contribution, before the weapon's
    // base damage/level is applied. Base overrides are initialization values.
    namingFactors[row.key] = applyMods(1,{...mods,override:null});
    if (ctx.unresolved.some(error => attrKey(error.attribute) === key)) namingFactors[row.key] = null;
  }

  // Sell: inv.monetaryvalue → attr_calc_price_gun_* (BalanceFormula) × part monetaryvaluemodifier scales.
  let value = null;
  const priceAttr = ctx.assembled.sources.filter(source => source.kind === "item")
    .map(source => source.definition.monetaryvalue?.attribute).filter(Boolean).at(-1)
    || priceAttrForItemType(card.item_type);
  if (priceAttr) {
    let basePrice = resolveAttribute(priceAttr, ctx, 0);
    if (basePrice != null && !Number.isNaN(basePrice)) {
      for (const ref of ctx.priceModAttrs || []) {
        const modKey = attrKey(ref);
        if (!modKey) continue;
        const scale = resolveAttribute(modKey, ctx, 0);
        if (scale == null || Number.isNaN(scale)) {
          blocked.push(`price_mod:${modKey}`);
          basePrice = null;
          break;
        }
        basePrice *= scale;
      }
      if (basePrice != null && Number.isFinite(basePrice) && basePrice >= 0) {
        // The native card receives a float representation of the capped signed
        // integer price (INT_MAX consequently displays as 2,147,483,648).
        value = Math.fround(Math.min(2147483647,Math.round(basePrice)));
      }
    } else {
      blocked.push(priceAttr);
    }
  }

  if (accuracy == null) blocked.push("weapon_accuracy_ui_compare");

  const out = {
    dps: roundStat(dps, "int"),
    damage: roundStat(damage, "int"),
    accuracy: accuracy == null ? null : Math.ceil(accuracy * 100),
    reload: roundStat(reload, "1"),
    fire_rate: roundStat(fireRate, "1"),
    magazine: roundStat(magazine, "int"),
    crit: crit == null || Number.isNaN(crit) ? null : roundStat(crit * 100, "1"),
    value,
    stats_ok: false,
    stats_source: "none",
    stats_blocked: blocked,
    naming_factors: namingFactors,
    native_naming_ready: ctx.assembled.errors.length === 0 && Number.isFinite(ctx.statModifiers.rarityScale),
    damage_radius: roundStat(resolveAttribute("weapon_damage_radius", ctx), "int"),
    shot_cost: roundStat(resolveAttribute("weapon_shot_cost", ctx), "int"),
    projectile_count: roundStat(resolveAttribute("weapon_projectile_per_shot", ctx), "int")
  };
  out.element_dps = roundStat(elementDps,"int");
  out.element_chance = Number.isFinite(elementChance) ? Math.ceil(elementChance*100) : null;
  out.element_text = elementDps > 0 && out.element_chance != null
    ? `${out.element_dps.toLocaleString("en-US")} DMG/s | ${out.element_chance}% Chance` : "";
  if (
    out.dps != null
    || out.damage != null
    || out.fire_rate != null
    || out.reload != null
    || out.magazine != null
    || out.value != null
  ) {
    out.stats_ok = true;
    out.stats_source = out.dps != null ? "offline_nexus_stats" : "partial_nexus";
  }
  return out;
}

function defaultLegitItems(sourceRoot) {
  return path.join(
    sourceRoot || process.cwd(),
    "external_app",
    "v22_parts_codes_fixed",
    "matt_editor",
    "LegitItems"
  );
}

function loadStatData(options = {}) {
  const legitItems = options.legitItemsPath || defaultLegitItems(options.sourceRoot);
  return {
    legitItems,
    attributes: loadKeyedRecords(legitItems, "Nexus-Data-attribute", "attribute"),
    globals: loadKeyedRecords(legitItems, "Nexus-Data-Resident", "globals"),
    uiStats: loadKeyedRecords(legitItems, "Nexus-Data-ui_stat", "ui_stat"),
    tables: loadDatatables(legitItems, options.rowDefaultsPath),
    statusDefaults: loadKeyedRecords(legitItems,"Nexus-Data-gbx_ue_data_table","gbx_ue_data_table").get("status_application_defaults"),
    invAspects: loadKeyedRecords(legitItems, "Nexus-Data-Resident", "inv_aspect"),
    invStats: loadKeyedRecords(options.cardRulesPath || legitItems, "Nexus-Data-inv_stat", "inv_stat"),
    rarities: loadKeyedRecords(options.cardRulesPath || legitItems, "Nexus-Data-Rarity", "rarity"),
    behaviorRules: readJson(path.join(legitItems, "native_behavior_rules.json")),
    equipmentDefaults: readJson(path.join(legitItems, "native_equipment_defaults.json")),
    progressGraphs: loadKeyedRecords(legitItems,"Nexus-Data-progress_graph","progress_graph"),
    skillTrees: loadKeyedRecords(legitItems,"Nexus-Data-skilltrees_data","skilltrees_data"),
    invRoots: loadInvRoots(legitItems)
  };
}

function attachStatsToCard(card, data) {
  if (!card || typeof card !== "object") return card;
  const equipment = require("./native_equipment_card").buildEquipmentCard(card,data,{buildStatContext,resolveAttribute});
  if (equipment) {
    card.native_equipment = equipment;
    card.value = equipment.price;
    card.stats_ok = Object.keys(equipment.values).length > 0;
    card.stats_source = "offline_native_equipment";
    card.stats_blocked = equipment.missing;
    return card;
  }
  const stats = evaluateWeaponCardStats(card, data);
  card.dps = stats.dps;
  card.damage = stats.damage;
  card.accuracy = stats.accuracy;
  card.reload = stats.reload;
  card.fire_rate = stats.fire_rate;
  card.magazine = stats.magazine;
  card.crit = stats.crit;
  card.value = stats.value;
  card.stats_ok = stats.stats_ok;
  card.stats_source = stats.stats_source;
  card.stats_blocked = stats.stats_blocked;
  card.naming_factors = stats.naming_factors;
  card.native_naming_ready = stats.native_naming_ready;
  card.damage_radius = stats.damage_radius;
  card.shot_cost = stats.shot_cost;
  card.projectile_count = stats.projectile_count;
  card.element_dps = stats.element_dps;
  card.element_chance = stats.element_chance;
  card.element_text = stats.element_text;
  return card;
}

module.exports = {
  loadStatData,
  evaluateWeaponCardStats,
  attachStatsToCard,
  getDatatableCell,
  evalBalanceFormula,
  GUN_TYPES,
  buildStatContext, resolveAttribute, resolveValueNode, addModifier, applyMods, emptyMods
};
