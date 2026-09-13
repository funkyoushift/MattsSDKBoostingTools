"use strict";

/**
 * Offline serial → card fields for Electron Inventory + BL4 Codes (Phase A).
 * Uses local GZO part index + legit_rules_flat np_names / rarity + optional ui_stat perk map.
 * Weapon titles follow mined Oak naming data (not invented heuristics):
 *   InventoryNamingAspect.titlepartlist → inv_name_part (unique/body)
 *   {MFG}_Weapon_LicensedPartPrefix_Table keyed by part addtags
 *   inv_name_strategy thresholds/priorities (native attribute inputs still unresolved)
 * Phase B weapon combat stats: serial_card_stats.js (mined Nexus expressions only).
 */

const fs = require("fs");
const path = require("path");
const { loadNamingStrategies, buildRootNamingIndex, weaponNamingStatus, evaluateWeaponNaming } = require("./serial_card_naming");
const {
  loadStatData,
  attachStatsToCard
} = require("./serial_card_stats");

const MAKER_PREFIXES = {
  DAD: "Daedalus",
  JAK: "Jakobs",
  ORD: "Order",
  TED: "Tediore",
  TOR: "Torgue",
  VLA: "Vladof",
  MAL: "Maliwan",
  BOR: "Ripper",
  RIP: "Ripper",
  COV: "CoV",
  ATL: "Atlas",
  HYP: "Hyperion",
  C4SH: "C4SH"
};

const TYPE_SUFFIXES = {
  PS: "Pistol",
  SG: "Shotgun",
  AR: "Assault Rifle",
  // GZO roots are VLA_SM / MAL_SM / DAD_SM (not *_SMG). Map both.
  SM: "SMG",
  SMG: "SMG",
  SR: "Sniper",
  // Mined Primary type string from heavy_weapon_uistats (not invented "Heavy Weapon").
  HW: "Heavy Gun Ordnance",
  HEAVY: "Heavy Gun Ordnance",
  SHIELD: "Shield",
  ARMOR_SHIELD: "Shield",
  ENERGY_SHIELD: "Shield",
  GADGET: "Ordnance",
  GRENADE_GADGET: "Ordnance",
  TURRET_GADGET: "Ordnance",
  HEAVY_WEAPON_GADGET: "Ordnance",
  TERMINAL_GADGET: "Ordnance",
  TERMINAL_BARRIER: "Ordnance",
  BARRIER: "Ordnance",
  ORDNANCE: "Ordnance",
  ENHANCEMENT: "Enhancement",
  REPAIR_KIT: "Repkit",
  REPKIT: "Repkit",
  CLASS_MOD: "Classmod",
  CLASSMOD: "Classmod"
};

const TYPE_HINTS = [
  ["classmod", "Classmod"],
  ["class_mod", "Classmod"],
  ["repair_kit", "Repkit"],
  ["repkit", "Repkit"],
  ["enhancement", "Enhancement"],
  ["grenade_gadget", "Ordnance"],
  ["turret_gadget", "Ordnance"],
  ["heavy_weapon_gadget", "Ordnance"],
  ["terminal_barrier", "Ordnance"],
  ["terminal_gadget", "Ordnance"],
  ["_gadget", "Ordnance"],
  ["energy_shield", "Shield"],
  ["armor_shield", "Shield"],
  ["_shield", "Shield"],
  ["shield", "Shield"],
  // Enemy/DLC meathead guns (Weapon_Meathead_Chaingun / Rocket / Flamethrower).
  ["weapon_meathead", "Heavy Gun Ordnance"],
  ["meathead_", "Heavy Gun Ordnance"]
];

const CLASS_NAMES = {
  siren: "Siren",
  dark_siren: "Siren",
  forgeknight: "Paladin",
  paladin: "Paladin",
  exo_soldier: "Exo Soldier",
  gravitar: "Gravitar",
  ai: "AI",
  c4sh: "C4SH",
  robodealer: "C4SH",
  corpohacker: "Loveless",
  corpo_hacker: "Loveless",
  hacker: "Loveless",
  loveless: "Loveless"
};

const GUN_TYPES = new Set([
  "Pistol",
  "Shotgun",
  "Assault Rifle",
  "SMG",
  "Sniper",
  "Heavy Weapon",
  "Heavy Gun Ordnance"
]);

const RARITY_LABEL = {
  pearlescent: "Pearlescent",
  pearl: "Pearlescent",
  legendary: "Legendary",
  epic: "Epic",
  rare: "Rare",
  uncommon: "Uncommon",
  common: "Common"
};

const COMP_RARITY_RE = [
  [/(?:^|\.)comp_06_pearl(?:escent)?(?:_|$)/i, "Pearlescent"],
  [/(?:^|\.)comp_05_legendary(?:_|$)/i, "Legendary"],
  [/(?:^|\.)comp_04_epic(?:_|$)/i, "Epic"],
  [/(?:^|\.)comp_03_rare(?:_|$)/i, "Rare"],
  [/(?:^|\.)comp_02_uncommon(?:_|$)/i, "Uncommon"],
  [/(?:^|\.)comp_01_common(?:_|$)/i, "Common"]
];

const COMP05_NAMED_RE = /(?:^|\.)comp_05_(?!legendary(?:_|$)|pearl(?:escent)?(?:_|$))(.+)$/i;
const UNIQUE_COMP_RE = /(?:^|\.)comp_0(?:5_legendary|6_pearl(?:escent)?)_(.+)$/i;
const NAMED_BARREL_RE = /(?:^|\.)part_barrel_\d+_(.+)$/i;
const NAMED_PART_RES = [
  /(?:^|\.)part_unique_(.+)$/i,
  /(?:^|\.)part_firmware_(.+)$/i,
  /(?:^|\.)part_core_[a-z0-9]+_(.+)$/i,
  /(?:^|\.)part_augment_unique_(.+)$/i,
  /(?:^|\.)part_body_armor_(.+)$/i,
  /(?:^|\.)part_body_(?!ele_|armor(?:_|$)|0?\d+[_\-]?(?:common|uncommon|rare|epic|legendary|pearl))(.+)$/i,
  /(?:^|\.)leg_body_(.+)$/i
];

const DAMAGE_TYPE_PATTERNS = [
  [/(?:^|[_\.])(?:incendiary|fire)(?:[_\.]|$)/i, "Fire"],
  [/(?:^|[_\.])(?:shock|electric)(?:[_\.]|$)/i, "Shock"],
  [/(?:^|[_\.])cryo(?:[_\.]|$)/i, "Cryo"],
  [/(?:^|[_\.])corrosive(?:[_\.]|$)/i, "Corrosive"],
  [/(?:^|[_\.])(?:radiation|rad)(?:[_\.]|$)/i, "Radiation"],
  [/(?:^|[_\.])kinetic(?:[_\.]|$)/i, "Kinetic"]
];

const WEAK_BARREL_SUFFIXES = new Set([
  "a", "b", "c", "d", "e", "f", "g", "h",
  "base", "body", "stock", "mag", "scope", "grip", "foregrip",
  "armor", "energy", "common", "uncommon", "rare", "epic", "legendary", "pearl", "pearlescent"
]);

const CLASSMOD_NAMED_TOKENS = new Set(["raid1", "raid2", "cowbell", "tuba", "dlc1", "dlc2"]);

function emptyCard() {
  return {
    display_name: "",
    unique_name: "",
    licensed_prefix: "",
    stat_prefix: "",
    rarity: "",
    manufacturer: "",
    item_type: "",
    type: "",
    character_class: "",
    category: "Other",
    element: "",
    damage_type: "",
    perk_lines: [],
    red_text: [],
    description_lines: [],
    part_names: [],
    part_keys: [],
    part_roots: [],
    set: "",
    type_id: "",
    human: "",
    level: null,
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
    stats_blocked: [],
    meta_ok: false,
    meta_source: "none"
  };
}

function leafPartName(partName) {
  const text = String(partName || "").trim();
  if (text.includes(".")) return text.split(".").pop().trim();
  return text;
}

function titleFromSlug(text) {
  return String(text || "")
    .replace(/[_\-]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => (["smg", "ai", "cov"].includes(w.toLowerCase()) ? w.toUpperCase() : w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()))
    .join(" ");
}

function humanizeUniqueToken(token) {
  const raw = String(token || "").trim();
  if (!raw) return "";
  let spaced = raw.replace(/([a-z0-9])([A-Z])/g, "$1 $2");
  spaced = spaced.replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2");
  spaced = spaced.replace(/[_-]+/g, " ");
  return spaced
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => {
      if (word === word.toUpperCase() && word.length >= 2 && word.length <= 8) return word;
      if (word === word.toUpperCase()) return word.charAt(0) + word.slice(1).toLowerCase();
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ")
    .trim();
}

function isWeakUniqueToken(token) {
  const t = String(token || "").trim().toLowerCase();
  if (!t || t.length <= 1) return true;
  if (/^\d+$/.test(t)) return true;
  if (/^0?\d{1,2}$/.test(t)) return true;
  if (/^(?:0?\d+[_\-]?)?(?:common|uncommon|rare|epic|legendary|pearl|pearlescent)$/.test(t)) return true;
  if (WEAK_BARREL_SUFFIXES.has(t)) return true;
  if (t.startsWith("ele_")) return true;
  return false;
}

function categoryForType(itemType) {
  const t = String(itemType || "").trim();
  if (GUN_TYPES.has(t)) return "Guns";
  if (t === "Shield") return "Shields";
  if (t === "Ordnance" || t === "Gadget") return "Ordnance";
  if (t === "Repkit") return "Repkits";
  if (t === "Enhancement") return "Enhancements";
  if (t === "Classmod") return "Class Mods";
  return "Other";
}

function typeInfoFromLabel(rawLabel) {
  const raw = String(rawLabel || "").trim();
  const low = raw.toLowerCase();
  const info = {
    set: raw,
    manufacturer: "",
    type: "",
    character_class: ""
  };
  if (!raw) return info;
  if (low.includes("classmod") || low.includes("class_mod")) {
    info.type = "Classmod";
    const tail = low.replace("classmod", "").replace("class_mod", "").replace(/^_+|_+$/g, "");
    info.character_class = tail ? (CLASS_NAMES[tail] || titleFromSlug(tail)) : "";
    return info;
  }
  const pieces = raw.split(/[_\s]+/).filter(Boolean);
  if (pieces.length) {
    const prefix = pieces[0].toUpperCase();
    if (MAKER_PREFIXES[prefix]) info.manufacturer = MAKER_PREFIXES[prefix];
    for (let i = 1; i < pieces.length; i += 1) {
      const suffix = pieces.slice(i).join("_").toUpperCase();
      if (TYPE_SUFFIXES[suffix]) {
        info.type = TYPE_SUFFIXES[suffix];
        break;
      }
    }
    if (!info.type) {
      const alone = pieces[0].toUpperCase();
      if (TYPE_SUFFIXES[alone]) info.type = TYPE_SUFFIXES[alone];
    }
  }
  if (!info.type) {
    for (const [key, val] of TYPE_HINTS) {
      if (low.includes(key)) {
        info.type = val;
        break;
      }
    }
  }
  if (!info.manufacturer && pieces.length) {
    for (const piece of pieces) {
      const pref = piece.toUpperCase();
      if (MAKER_PREFIXES[pref]) {
        info.manufacturer = MAKER_PREFIXES[pref];
        break;
      }
      if (pref.startsWith("BOR")) {
        info.manufacturer = "Ripper";
        break;
      }
    }
  }
  return info;
}

function normalizeRarity(raw) {
  const text = String(raw || "").trim();
  if (!text) return "";
  const low = text.toLowerCase();
  for (const [needle, label] of Object.entries(RARITY_LABEL)) {
    if (low.includes(needle)) return label;
  }
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function guessRarityFromPartNames(names) {
  for (const name of names) {
    const leaf = leafPartName(name);
    for (const [re, label] of COMP_RARITY_RE) {
      if (re.test(leaf)) return label;
    }
    if (COMP05_NAMED_RE.test(leaf)) return "Legendary";
    if (/(?:^|\.)part_unique_/i.test(leaf)) return "Legendary";
  }
  const hay = names.join(" ").toLowerCase();
  for (const [needle, label] of Object.entries(RARITY_LABEL)) {
    if (hay.includes(needle)) return label;
  }
  return "";
}

function guessDamageTypeFromPartNames(names) {
  for (const name of names) {
    const leaf = leafPartName(name);
    for (const [re, label] of DAMAGE_TYPE_PATTERNS) {
      if (re.test(leaf)) return label;
    }
  }
  return "";
}

function tokenFromNamedPatterns(leaf) {
  for (const pattern of [UNIQUE_COMP_RE, COMP05_NAMED_RE, NAMED_BARREL_RE, ...NAMED_PART_RES]) {
    const m = leaf.match(pattern);
    if (!m) continue;
    const token = String(m[1] || "").trim();
    if (!token) continue;
    const low = token.toLowerCase();
    if (CLASSMOD_NAMED_TOKENS.has(low) || !isWeakUniqueToken(token)) {
      if (!low.startsWith("ele_")) return token;
    }
  }
  return "";
}

function uniqueDisplayFromPartNames(names) {
  for (const name of names) {
    const leaf = leafPartName(name);
    const m = leaf.match(UNIQUE_COMP_RE);
    if (m) {
      const token = String(m[1] || "").trim();
      const low = token.toLowerCase();
      if (CLASSMOD_NAMED_TOKENS.has(low) || (token && !isWeakUniqueToken(token))) {
        return humanizeUniqueToken(token);
      }
    }
  }
  for (const name of names) {
    const leaf = leafPartName(name);
    if (UNIQUE_COMP_RE.test(leaf)) continue;
    const token = tokenFromNamedPatterns(leaf);
    if (token) return humanizeUniqueToken(token);
  }
  return "";
}

function fallbackDisplayName(manufacturer, itemType, characterClass, setLabel) {
  if (itemType === "Classmod") {
    const pieces = [characterClass, "Class Mod"].filter(Boolean);
    if (pieces.length) return pieces.join(" ");
  }
  const pieces = [manufacturer, itemType || characterClass].filter(Boolean);
  if (pieces.length) return pieces.join(" ");
  return String(setLabel || "").replace(/_/g, " ").trim();
}

function stripUiStatFormatText(fmt) {
  let plain = String(fmt || "");
  // Drop localization prefix: "Name, HASH, rest"
  const parts = plain.split(",");
  if (parts.length >= 3 && String(parts[1] || "").trim().length >= 16) {
    plain = parts.slice(2).join(",").trim();
  }
  plain = plain.replace(/\[[^\]]+\]/g, "");
  return plain.replace(/\s+/g, " ").trim();
}

/** Hide unresolved game format placeholders ({mod}, {duration}, …) rather than showing raw tags. */
function sanitizePerkPreviewText(text) {
  let plain = String(text || "").trim();
  if (!plain) return "";
  if (!/\{[a-z][a-z0-9_]*\}/i.test(plain)) return plain;
  // If the whole line is an unresolved template, hide it.
  if (/^\{[a-z][a-z0-9_]*\}/i.test(plain) || /^Every\s+\{/i.test(plain)) return "";
  // Multi-{modN} legendary lines (Stalker / Big Name Hunter): keep the mined title, never invent values.
  const titled = plain.match(/^([^—–\-{][^—–\-]*?)\s*[—–-]\s*(.*)$/);
  if (titled) {
    const title = titled[1].replace(/\s+/g, " ").trim();
    if (title) return title;
  }
  // Drop dash/parenthetical clauses that still contain unresolved format tokens.
  let cleaned = plain
    .replace(/\s*[—–-]\s*[^{}\n]*\{[a-z][a-z0-9_]*\}[^{}\n]*/gi, "")
    .replace(/\([^)]*\{[a-z][a-z0-9_]*\}[^)]*\)/gi, "")
    .replace(/\{[a-z][a-z0-9_]*\}/gi, "")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([.,;:!])/g, "$1")
    .trim();
  if (!cleaned || /^[-–—:.\s]*$/.test(cleaned)) return "";
  if (/\{[a-z][a-z0-9_]*\}/i.test(cleaned)) return "";
  return cleaned;
}

function entryRootKey(entry) {
  if (!entry || typeof entry !== "object") return "";
  for (const key of Object.keys(entry)) {
    if (key.startsWith("__")) continue;
    return String(key || "").trim().toLowerCase();
  }
  return "";
}

function buildTypeIdIndex(gzoPartsMap) {
  const idx = new Map();
  if (!gzoPartsMap || typeof gzoPartsMap !== "object") return idx;
  for (const [key, table] of Object.entries(gzoPartsMap)) {
    if (!table || typeof table !== "object") continue;
    const m = String(key).match(/^\s*(\d+)\s*\|\s*(.+?)\s*$/);
    if (!m) continue;
    idx.set(Number(m[1]), { label: m[2], table });
  }
  return idx;
}

function buildLegitPartIndex(legitRules) {
  /**
   * Keys are `root::part` (preferred) and bare `part` only when a single np_name
   * set exists across roots — shared keys like leg_body_04 must not collapse Cooler
   * over Kindread Spirits.
   * @type {Map<string, { np_names: string[], rarity: string, display: string, add: string[] }>}
   */
  const byKey = new Map();
  /** @type {Map<string, Set<string>>} */
  const bareNameSets = new Map();
  /** @type {Set<string>} */
  const bareConflicted = new Set();
  const roots = (legitRules && legitRules.roots) || [];
  for (const root of roots) {
    const rootKey = String((root && root.key) || "").trim().toLowerCase();
    for (const part of root.parts || []) {
      if (!part || typeof part !== "object") continue;
      const key = String(part.key || "").trim().toLowerCase();
      if (!key) continue;
      const names = Array.isArray(part.np_names)
        ? part.np_names.map((n) => String(n || "").trim()).filter(Boolean)
        : [];
      const add = Array.isArray(part.add)
        ? part.add.map((t) => String(t || "").trim().toLowerCase()).filter(Boolean)
        : [];
      const row = {
        np_names: names,
        rarity: String(part.rarity || "").trim(),
        display: String(part.display || "").trim(),
        add
      };
      if (rootKey) byKey.set(`${rootKey}::${key}`, row);
      const sig = names.join("\0");
      const set = bareNameSets.get(key) || new Set();
      if (sig) set.add(sig);
      bareNameSets.set(key, set);
      if (set.size > 1 || bareConflicted.has(key)) {
        bareConflicted.add(key);
        byKey.delete(key);
      } else if (!byKey.has(key)) {
        byKey.set(key, row);
      }
    }
  }
  return byKey;
}

function lookupLegitPart(legitByKey, rootSet, partKey) {
  if (!legitByKey || !legitByKey.size) return null;
  const key = String(partKey || "").toLowerCase();
  const root = String(rootSet || "").toLowerCase();
  if (root) {
    const scoped = legitByKey.get(`${root}::${key}`);
    if (scoped) return scoped;
  }
  return legitByKey.get(key) || null;
}

function buildPerkIndexFromUiAndInv(uiStatPayloads, invPayloads) {
  const uiByKey = new Map();
  for (const payload of uiStatPayloads || []) {
    const records = (((payload || {}).ui_stat || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const [key, val] of Object.entries(entry)) {
          if (!val || typeof val !== "object") continue;
          const dg = String(val.displaygroup || "");
          const sv = val.statvalue || {};
          const fmt = sv && typeof sv === "object" ? String(sv.formattext || "") : "";
          if (!fmt) continue;
          const plain = stripUiStatFormatText(fmt);
          if (!plain) continue;
          let kind = "";
          if (dg.includes("RedText")) kind = "red";
          else if (dg.includes("TypeLine")) kind = "type";
          else if (dg.includes("Secondary") || (dg.includes("Text") && !dg.includes("Primary") && !dg.includes("Headline"))) kind = "desc";
          else continue;
          const slot = uiByKey.get(String(key).toLowerCase()) || {};
          slot[kind] = plain;
          uiByKey.set(String(key).toLowerCase(), slot);
        }
      }
    }
  }

  const perkByPart = new Map();
  const refRe = /ui_stat'([^']+)'/i;
  for (const payload of invPayloads || []) {
    const records = (((payload || {}).inv || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        const rootKey = entryRootKey(entry);
        for (const dep of entry.__dep_entries || []) {
          if (!dep || typeof dep !== "object") continue;
          for (const [partKey, part] of Object.entries(dep)) {
            if (
              partKey.startsWith("__")
              || partKey === "depTableName"
              || partKey === "depTableId"
              || partKey === "depIndex"
              || !part
              || typeof part !== "object"
            ) {
              continue;
            }
            const reds = [];
            const descs = [];
            let itemType = "";
            for (const aspect of part.aspects || []) {
              if (!aspect || typeof aspect !== "object") continue;
              if (!String(aspect.structtype || "").includes("UIStatAspect")) continue;
              for (const ref of aspect.uistatstoinclude || []) {
                const m = String(ref).match(refRe);
                if (!m) continue;
                const info = uiByKey.get(m[1].toLowerCase()) || {};
                if (info.type) itemType = info.type;
                if (info.red) {
                  const line = sanitizePerkPreviewText(info.red);
                  if (line) reds.push(line);
                }
                if (info.desc) {
                  const line = sanitizePerkPreviewText(info.desc);
                  if (line) descs.push(line);
                }
              }
            }
            if (!reds.length && !descs.length && !itemType) continue;
            const row = {
              item_type: itemType,
              red: [...new Set(reds)],
              desc: [...new Set(descs)]
            };
            const key = String(partKey).toLowerCase();
            if (rootKey) perkByPart.set(`${rootKey}::${key}`, row);
            if (!perkByPart.has(key)) perkByPart.set(key, row);
          }
        }
      }
    }
  }
  return perkByPart;
}

/**
 * Accept a cross-set `{typeId:partId}` ref (editor / incomplete-gzo convention).
 * Gun→gun: same manufacturer only (TOR_PS Kitty on TOR_SG; blocks TED Eigenburst on ORD_PS).
 * Gear→gear: same item type only (Shield↔Armor_Shield, Ordnance↔grenade pools, Repkit↔repair_kit).
 */
function acceptCrossSetPart(itemInfo, foreignInfo) {
  if (!foreignInfo) return false;
  const foreignIsGun = GUN_TYPES.has(foreignInfo.type);
  const itemIsGun = GUN_TYPES.has(itemInfo.type);
  if (itemIsGun && foreignIsGun) {
    const a = String(itemInfo.manufacturer || "").toLowerCase();
    const b = String(foreignInfo.manufacturer || "").toLowerCase();
    return Boolean(a && b && a === b);
  }
  if (!itemIsGun && !foreignIsGun) {
    return Boolean(itemInfo.type && foreignInfo.type && itemInfo.type === foreignInfo.type);
  }
  return false;
}

function foreignListIsNamingParts(foreignLabel) {
  // Armor_Shield / Enhancement stacks are naming part-id lists.
  // Ordnance grenade_gadget stacks mix roll values with naming stat parts — expand then
  // keep only parts that carry InventoryNamingAspect (filtered in push via caller).
  const low = String(foreignLabel || "").trim().toLowerCase();
  if (low === "armor_shield" || low === "enhancement" || /_enhancement$/i.test(low)) return true;
  if (/grenade_gadget$/i.test(low) || low === "grenade_gadget") return "ordnance_filter";
  return false;
}

function pushResolvedPart(out, partName, rootSet, limit, { allowDup = false } = {}) {
  if (!partName || out.keys.length >= limit) return;
  const key = leafPartName(partName).toLowerCase();
  const root = String(rootSet || "").toLowerCase();
  const sig = `${root}::${key}`;
  // Keep intentional Armor_Shield stacks (Barrage Barrage); dedupe spammy core repeats.
  const stackable = allowDup || /^part_ra_.*_(primary|secondary)$/i.test(key);
  if (!stackable) {
    if (out._seen.has(sig)) return;
    out._seen.add(sig);
  } else {
    const n = (out._seenCounts.get(sig) || 0) + 1;
    if (n > 4) return;
    out._seenCounts.set(sig, n);
  }
  out.names.push(String(partName));
  out.keys.push(key);
  out.roots.push(root);
}

/**
 * Decode human serial part tokens.
 * Bare `{index}` → part on this item's typeId table.
 * Weapon `{typeId:partId}` / `{typeId:[ids…]}` always uses the referenced table,
 * including same-type refs, and preserves every part in serial order.
 * The existing non-weapon naming path below remains bounded; it has not been
 * reworked as part of this mixed-weapon correction.
 */
function partNamesFromHuman(human, typeIdIndex, limit = 192) {
  const out = { names: [], keys: [], roots: [], _seen: new Set(), _seenCounts: new Map() };
  const header = String(human || "").match(/^\s*(\d+)\s*,/);
  const itemTypeId = header ? Number(header[1]) : 0;
  const typeRow = typeIdIndex.get(itemTypeId);
  if (!typeRow) return out;
  const itemInfo = typeInfoFromLabel(typeRow.label);
  const itemRoot = String(typeRow.label || "").toLowerCase();
  if (GUN_TYPES.has(itemInfo.type)) {
    // Typed tokens always name a part table, including same-type references.
    // Manufacturer/type compatibility is a builder restriction, not a decoder
    // rule: modded guns deliberately contain heavy, grenade and enhancement parts.
    // Preserve order and multiplicity; both matter to the assembled item.
    for (const match of String(human || "").matchAll(/\{\s*(\d+)(?:\s*:\s*(?:\[([^\]]*)\]|(\d+)))?\s*\}/g)) {
      const typed = match[2] != null || match[3] != null;
      const row = typed ? typeIdIndex.get(Number(match[1])) : typeRow;
      if (!row) continue;
      const ids = match[2] != null ? match[2].trim().split(/\s+/) : [typed ? match[3] : match[1]];
      for (const id of ids) {
        const name = row.table[id];
        if (!name) continue;
        out.names.push(String(name));
        out.keys.push(leafPartName(name).toLowerCase());
        out.roots.push(String(row.label).toLowerCase());
      }
    }
    return out;
  }
  const refs = String(human || "").matchAll(/\{\s*(\d+)(?:\s*:\s*(?:\[([^\]]*)\]|(\d+)))?\s*\}/g);
  for (const match of refs) {
    if (out.keys.length >= limit) break;
    const first = Number(match[1]);
    if (!Number.isFinite(first)) continue;
    const listBody = match[2];
    const intBody = match[3];
    const hasPayload = listBody != null || intBody != null;
    const foreignRow = hasPayload && first !== itemTypeId ? typeIdIndex.get(first) : null;

    if (foreignRow) {
      const foreignInfo = typeInfoFromLabel(foreignRow.label);
      const accepted = acceptCrossSetPart(itemInfo, foreignInfo);
      // Franken gun lists `{malTypeId:[partIds…]}` (e.g. MAL_SG Mantra barrel stack on
      // VLA_SM). Expand those so naming matches the game. Keep int `{typeId:part}` on the
      // same-mfg path only — Roulette `{11:82}` must still fall through as on-item subtype.
      const frankenGunList = !accepted
        && listBody != null
        && GUN_TYPES.has(itemInfo.type)
        && GUN_TYPES.has(foreignInfo.type);
      if (accepted || frankenGunList) {
        const foreignRoot = String(foreignRow.label || "").toLowerCase();
        if (listBody != null) {
          const listMode = foreignListIsNamingParts(foreignRow.label);
          if (listMode) {
            for (const tok of String(listBody).trim().split(/\s+/)) {
              if (!tok) continue;
              const partName = foreignRow.table[String(tok)];
              if (!partName) continue;
              const leaf = leafPartName(partName).toLowerCase();
              // Grenade list payloads include roll ids; keep naming-bearing part keys only.
              if (listMode === "ordnance_filter" && !/^part_stat_05_|^part_stat_07_|^part_spinning|^comp_05_spinning|^part_payload_/i.test(leaf)) {
                continue;
              }
              pushResolvedPart(out, partName, foreignRoot, limit, {
                allowDup: listMode === true && /^armor_shield$/i.test(foreignRow.label)
              });
              if (out.keys.length >= limit) break;
            }
          } else if (GUN_TYPES.has(foreignInfo.type)) {
            for (const tok of String(listBody).trim().split(/\s+/)) {
              if (!tok) continue;
              const partName = foreignRow.table[String(tok)];
              if (!partName || !isCrossSetGunNamingPart(partName)) continue;
              pushResolvedPart(out, partName, foreignRoot, limit);
              if (out.keys.length >= limit) break;
            }
          }
          continue;
        }
        if (intBody != null && accepted) {
          const partName = foreignRow.table[String(intBody)];
          pushResolvedPart(out, partName, foreignRoot, limit);
          continue;
        }
      } else if (!GUN_TYPES.has(foreignInfo.type)) {
        // Valid non-gun typeId in the colon (e.g. base Weapon) — not an on-item subtype.
        // Skipping avoids treating {1:14} as TOR_SG Linebacker when 1 is type Weapon.
        continue;
      }
      // Rejected other-mfg gun colon (Roulette {11:82}): fall through to on-item index.
    }

    // On-item index (bare token, rejected foreign, or same-type subtype payload).
    const partName = typeRow.table[String(first)];
    pushResolvedPart(out, partName, itemRoot, limit);
  }
  return out;
}

function pickBestNpName(partKeys, legitByKey, rootSet, partRoots) {
  const hit = pickBestNpNameHit(partKeys, legitByKey, rootSet, partRoots);
  return hit ? hit.name : "";
}

/**
 * Prefer legendary/pearl comps, then barrels/unique carriers, then any np_names.
 * Source: InventoryNamingAspect.titlepartlist → inv_name_part (imported into np_names).
 * Returns the winning display name plus the part that supplied it (for RedText attach).
 */
function pickBestNpNameHit(partKeys, legitByKey, rootSet, partRoots) {
  const rootFor = (i) => {
    if (Array.isArray(partRoots) && partRoots[i]) return partRoots[i];
    return rootSet;
  };
  const ordered = [];
  partKeys.forEach((key, i) => {
    if (/^comp_0(?:5_legendary|6_pearl)/i.test(key) || /^comp_05_/i.test(key)) {
      ordered.push({ key, root: rootFor(i), i });
    }
  });
  partKeys.forEach((key, i) => {
    if (
      /^part_barrel_/i.test(key)
      || /^part_unique_/i.test(key)
      || /^part_firmware_/i.test(key)
      || /^leg_body_/i.test(key)
      || /^part_spinning_blade$/i.test(key)
      || /^part_augment_unique_/i.test(key)
    ) {
      if (!ordered.some((row) => row.key === key && row.root === rootFor(i))) {
        ordered.push({ key, root: rootFor(i), i });
      }
    }
  });
  partKeys.forEach((key, i) => {
    if (!ordered.some((row) => row.key === key && row.root === rootFor(i))) {
      ordered.push({ key, root: rootFor(i), i });
    }
  });
  for (const row of ordered) {
    const hit = lookupLegitPart(legitByKey, row.root, row.key);
    if (hit && hit.np_names && hit.np_names.length) {
      return {
        name: hit.np_names[0],
        key: row.key,
        root: String(row.root || "").toLowerCase(),
        index: row.i
      };
    }
  }
  return null;
}

function pickWeaponTitle(partKeys, partRoots, ctx) {
  let best = null;
  partKeys.forEach((key, index) => {
    const root = partRoots[index];
    // Compositions' generated np_names describe their default barrels; they
    // do not supply an InventoryNamingAspect to a modified weapon themselves.
    const naming = ctx.partMetaByKey?.get(`${root}::${key}`)?.naming;
    for (const id of naming?.titles || []) {
      const row = ctx.invNameParts?.get(id.toLowerCase());
      // Equal-priority titles retain serial order (the supplied mixed-barrel
      // Ichor/Bubbles/Draupner examples all have priority 3).
      if (row && (!best || row.priority > best.priority)) {
        best = { name: row.display, priority: row.priority, key, root, index };
      }
    }
  });
  return best;
}

const LICENSED_PREFIX_ROW_PRIORITY = ["jak_barrel_acc", "licensed_ted", "hyp_shield", "default"];
const LICENSED_PREFIX_COL_PRIORITY = ["borg_mag", "cov_mag", "tor_mag", "default"];

/** Franken `{otherGunType:[ids…]}` lists mix roll values; keep unique/licensed barrels + torgue mags. */
function isCrossSetGunNamingPart(partName) {
  const leaf = leafPartName(partName).toLowerCase();
  if (/^comp_0(?:5|6)_/i.test(leaf)) return true;
  if (/^part_barrel_licensed_/i.test(leaf)) return true;
  // Named barrels (mantra, soulsurvivor, …) — not generic part_barrel_01_a / _02_c.
  if (/^part_barrel_\d+_[a-z][a-z0-9_]{2,}$/i.test(leaf)) return true;
  // Torgue mag license column (VLA licensed_ted → -Wasted).
  if (/^part_mag_(?:03_tor|torgue_)/i.test(leaf)) return true;
  return false;
}

function nexusLocalizedTail(raw) {
  return stripUiStatFormatText(raw);
}

function buildPartTagAndStatIndex(invPayloads) {
  /** @type {Map<string, { tags: string[], statTags: string[], naming: object }>} */
  const byKey = new Map();
  const mergeInto = (mapKey, tags, statTags, naming) => {
    const prev = byKey.get(mapKey) || { tags: [], statTags: [], naming: null };
    byKey.set(mapKey, {
      tags: [...new Set([...prev.tags, ...tags])],
      // Keep per-root lists; do not concat across manufacturers (shared part keys).
      statTags: prev.statTags.length ? prev.statTags : statTags,
      naming: prev.naming || naming
    });
  };
  for (const payload of invPayloads || []) {
    const records = (((payload || {}).inv || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        const rootKey = entryRootKey(entry);
        for (const dep of entry.__dep_entries || []) {
          if (!dep || typeof dep !== "object") continue;
          for (const [partKey, part] of Object.entries(dep)) {
            if (
              partKey.startsWith("__")
              || partKey === "depTableName"
              || partKey === "depTableId"
              || partKey === "depIndex"
              || !part
              || typeof part !== "object"
            ) {
              continue;
            }
            const key = String(partKey).toLowerCase();
            const tags = [];
            // Only addtags/basetags contribute to naming. dependencytags are
            // requirements (e.g. TED thrown mags require licensed_ted) — counting
            // them invents licensed prefixes like ORD -Vested without a TED license part.
            for (const listName of ["addtags", "basetags"]) {
              for (const row of part[listName] || []) {
                if (typeof row === "string") {
                  tags.push(row.toLowerCase());
                } else if (row && typeof row === "object") {
                  for (const val of Object.values(row)) {
                    if (val != null) tags.push(String(val).toLowerCase());
                  }
                }
              }
            }
            const statTags = [];
            /** @type {{ prefixes: string[], titles: string[], suffixes: string[], tableRow: string, disablePrefixes: boolean, passives: {graph:string,node:string}[] }} */
            const naming = {
              prefixes: [],
              titles: [],
              suffixes: [],
              tableRow: "",
              disablePrefixes: false,
              passives: []
            };
            for (const aspect of part.aspects || []) {
              if (!aspect || typeof aspect !== "object") continue;
              for (const sm of aspect.statmodifiers || []) {
                const st = String((sm && sm.stattagname) || "").trim().toLowerCase();
                if (st) statTags.push(st);
              }
              const stype = String(aspect.structtype || "");
              if (stype.includes("InventoryNamingAspect")) {
                for (const ref of aspect.prefixpartlist || []) {
                  const m = String(ref).match(/inv_name_part'([^']+)'/i);
                  if (m) naming.prefixes.push(m[1]);
                }
                for (const ref of aspect.titlepartlist || []) {
                  const m = String(ref).match(/inv_name_part'([^']+)'/i);
                  if (m) naming.titles.push(m[1]);
                }
                for (const ref of aspect.suffixpartlist || []) {
                  const m = String(ref).match(/inv_name_part'([^']+)'/i);
                  if (m) naming.suffixes.push(m[1]);
                }
                if (aspect.datatablerowname) {
                  naming.tableRow = String(aspect.datatablerowname).trim();
                }
                if (String(aspect.bdisableprefixes || "").toLowerCase() === "true") {
                  naming.disablePrefixes = true;
                }
              }
              if (stype.includes("ClassModPassivesAspect")) {
                for (const passive of aspect.passives || []) {
                  if (!passive || typeof passive !== "object") continue;
                  const graph = String(passive.progressgraph || "").trim().toLowerCase();
                  const node = String(passive.nodename || "").trim().toLowerCase();
                  if (graph || node) naming.passives.push({ graph, node });
                }
              }
            }
            const namingPayload = (
              naming.prefixes.length
              || naming.titles.length
              || naming.suffixes.length
              || naming.tableRow
              || naming.disablePrefixes
              || naming.passives.length
            ) ? naming : null;
            if (rootKey) mergeInto(`${rootKey}::${key}`, tags, statTags, namingPayload);
            // Fallback only when no root-scoped entry exists yet.
            if (!byKey.has(key)) mergeInto(key, tags, statTags, namingPayload);
          }
        }
      }
    }
  }
  return byKey;
}

function lookupPartMeta(partMetaByKey, rootSet, partKey) {
  if (!partMetaByKey || !partMetaByKey.size) return null;
  const key = String(partKey || "").toLowerCase();
  const root = String(rootSet || "").toLowerCase();
  if (root) {
    const scoped = partMetaByKey.get(`${root}::${key}`);
    if (scoped) return scoped;
  }
  return partMetaByKey.get(key) || null;
}

function buildWeaponNamingTables(gbxPayloads) {
  /** @type {Map<string, { licensed: Map<string, Record<string, string>>, stat: Map<string, Record<string, string>> }>} */
  const byMfg = new Map();
  const reLicensed = /^([a-z]+)_weapon_licensedpartprefix_table$/i;
  const reStat = /^([a-z]+)_weapon_statprefix_table$/i;
  for (const payload of gbxPayloads || []) {
    const records = (((payload || {}).gbx_ue_data_table || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const [key, table] of Object.entries(entry)) {
          if (!table || typeof table !== "object") continue;
          const tableName = String(table.gbx_ue_data_table || key || "");
          let mfg = "";
          let kind = "";
          let m = tableName.match(reLicensed) || key.match(reLicensed);
          if (m) {
            mfg = m[1].toLowerCase();
            kind = "licensed";
          } else {
            m = tableName.match(reStat) || key.match(reStat);
            if (m) {
              mfg = m[1].toLowerCase();
              kind = "stat";
            }
          }
          if (!mfg || !kind) continue;
          const slot = byMfg.get(mfg) || {
            licensed: new Map(),
            stat: new Map()
          };
          const target = kind === "licensed" ? slot.licensed : slot.stat;
          for (const row of table.data || []) {
            const rowName = String((row && row.row_name) || "").trim().toLowerCase();
            if (!rowName || !row.row_value || typeof row.row_value !== "object") continue;
            /** @type {Record<string, string>} */
            const cols = {};
            for (const [col, raw] of Object.entries(row.row_value)) {
              const label = nexusLocalizedTail(raw);
              if (label) cols[String(col).toLowerCase()] = label;
            }
            target.set(rowName, cols);
          }
          byMfg.set(mfg, slot);
        }
      }
    }
  }
  return byMfg;
}

function buildInvNamePartIndex(invNamePartPayloads) {
  /** @type {Map<string, { display: string, priority: number }>} */
  const byId = new Map();
  for (const payload of invNamePartPayloads || []) {
    const records = (((payload || {}).inv_name_part || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const [key, val] of Object.entries(entry)) {
          if (!val || typeof val !== "object") continue;
          const id = String(val.inv_name_part || key || "").trim().toLowerCase();
          if (!id) continue;
          const display = nexusLocalizedTail(val.partname || "");
          const priority = Number.parseFloat(String(val.priority || "0")) || 0;
          if (!display) continue;
          const prev = byId.get(id);
          if (!prev || priority >= prev.priority) {
            byId.set(id, { display, priority });
          }
        }
      }
    }
  }
  return byId;
}

function buildShieldNameTable(gbxPayloads) {
  /** @type {Map<string, { primary: string, secondary: string, both: string }>} */
  const byRow = new Map();
  for (const payload of gbxPayloads || []) {
    const records = (((payload || {}).gbx_ue_data_table || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const [key, table] of Object.entries(entry)) {
          if (!table || typeof table !== "object") continue;
          const tname = String(table.gbx_ue_data_table || key || "");
          if (!/^ShieldNameTable$/i.test(tname)) continue;
          for (const row of table.data || []) {
            const rowName = String((row && row.row_name) || "").trim().toLowerCase();
            if (!rowName || rowName.startsWith("--")) continue;
            const rv = (row && row.row_value) || {};
            byRow.set(rowName, {
              primary: nexusLocalizedTail(rv.primary || ""),
              secondary: nexusLocalizedTail(rv.secondary || ""),
              both: nexusLocalizedTail(rv.both || "")
            });
          }
        }
      }
    }
  }
  return byRow;
}

function buildEnhancementNamingTables(gbxPayloads) {
  /** @type {{ core: Map<string, Record<string, string>>, stat: Map<string, Record<string, string>>, priority: string[] }} */
  const out = {
    core: new Map(),
    stat: new Map(),
    priority: []
  };
  for (const payload of gbxPayloads || []) {
    const records = (((payload || {}).gbx_ue_data_table || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const [key, table] of Object.entries(entry)) {
          if (!table || typeof table !== "object") continue;
          const tname = String(table.gbx_ue_data_table || key || "");
          if (/EnhancementNamingCoreCombinationsTable/i.test(tname)) {
            for (const row of table.data || []) {
              const rowName = String((row && row.row_name) || "").trim().toLowerCase();
              if (!rowName || !row.row_value) continue;
              /** @type {Record<string, string>} */
              const cols = {};
              for (const [col, raw] of Object.entries(row.row_value)) {
                const label = nexusLocalizedTail(raw);
                if (label) cols[String(col).toLowerCase()] = label;
              }
              out.core.set(rowName, cols);
            }
          } else if (/EnhancementNamingStatCombinationsTable/i.test(tname)) {
            for (const row of table.data || []) {
              const rowName = String((row && row.row_name) || "").trim().toLowerCase();
              if (!rowName || !row.row_value) continue;
              /** @type {Record<string, string>} */
              const cols = {};
              for (const [col, raw] of Object.entries(row.row_value)) {
                const label = nexusLocalizedTail(raw);
                if (label) cols[String(col).toLowerCase()] = label;
              }
              out.stat.set(rowName, cols);
            }
          } else if (/EnhancementNamingStatPriorityTable/i.test(tname)) {
            for (const row of table.data || []) {
              const pn = nexusLocalizedTail(((row || {}).row_value || {}).partname || "");
              if (pn) out.priority.push(pn.toLowerCase());
            }
          }
        }
      }
    }
  }
  return out;
}

function buildClassModPassiveNameTables(gbxPayloads) {
  /** @type {Map<string, Map<string, { slot: number, graph: string, node: string, display: string }[]>>} */
  const byClass = new Map();
  const classFromTable = (tname) => {
    const m = String(tname || "").match(/ClassModPassiveAndDisplayNameDataTable_([A-Za-z]+)/i);
    if (!m) return "";
    const raw = m[1].toLowerCase();
    if (raw === "darksiren") return "classmod_dark_siren";
    if (raw === "exosolider" || raw === "exosoldier") return "classmod_exo_soldier";
    if (raw === "gravitar") return "classmod_gravitar";
    if (raw === "paladin") return "classmod_paladin";
    if (raw === "corpohacker") return "classmod_corpohacker";
    if (raw === "robodealer") return "classmod_robodealer";
    return `classmod_${raw}`;
  };
  for (const payload of gbxPayloads || []) {
    const records = (((payload || {}).gbx_ue_data_table || {}).records) || [];
    for (const rec of records) {
      for (const entry of rec.entries || []) {
        if (!entry || typeof entry !== "object") continue;
        for (const [key, table] of Object.entries(entry)) {
          if (!table || typeof table !== "object") continue;
          const tname = String(table.gbx_ue_data_table || key || "");
          const classKey = classFromTable(tname);
          if (!classKey) continue;
          const bodyMap = byClass.get(classKey) || new Map();
          for (const row of table.data || []) {
            const body = String((row && row.row_name) || "").trim().toLowerCase();
            if (!body) continue;
            const slots = [];
            const rv = (row && row.row_value) || {};
            for (let i = 1; i <= 8; i += 1) {
              const cell = rv[`passive${i}`];
              if (!cell || typeof cell !== "object") continue;
              const passive = cell.passive || {};
              slots.push({
                slot: i,
                graph: String(passive.progressgraph || "").trim().toLowerCase(),
                node: String(passive.nodename || "").trim().toLowerCase(),
                display: nexusLocalizedTail(cell.displayname || "")
              });
            }
            bodyMap.set(body, slots);
          }
          byClass.set(classKey, bodyMap);
        }
      }
    }
  }
  return byClass;
}

function resolveNpDisplay(npId, invNameParts) {
  if (!npId || !invNameParts) return null;
  return invNameParts.get(String(npId).toLowerCase()) || null;
}

function shieldRoleFromPartKey(partKey) {
  const key = String(partKey || "").toLowerCase();
  if (key.includes("_secondary")) return "secondary";
  if (key.includes("_primary")) return "primary";
  return "both";
}

function pickShieldTableLabel(row, role) {
  if (!row) return "";
  if (role === "primary") return row.primary || row.both || "";
  if (role === "secondary") return row.secondary || row.both || "";
  return row.both || row.primary || row.secondary || "";
}

/**
 * Compose non-weapon titles from mined InventoryNamingAspect fields:
 * prefixpartlist + datatablerowname tables + titlepartlist (+ suffix).
 */
function composeGearDisplayName(itemType, partKeys, partMetaByKey, rootSet, ctx, partRoots) {
  const invNameParts = ctx.invNameParts || new Map();
  const shieldTable = ctx.shieldNameTable || new Map();
  const enhTables = ctx.enhancementNaming || { core: new Map(), stat: new Map(), priority: [] };
  const classModTables = ctx.classModPassiveTables || new Map();

  const prefixTokens = [];
  const titleTokens = [];
  const suffixTokens = [];
  let disablePrefixes = false;
  /** @type {{ id: string, priority: number, display: string }[]} */
  const rankedPrefixes = [];
  /** @type {{ id: string, priority: number, display: string }[]} */
  const rankedTitles = [];

  const rootFor = (i) => (Array.isArray(partRoots) && partRoots[i]) || rootSet;

  const pushNp = (npId, bucket) => {
    const row = resolveNpDisplay(npId, invNameParts);
    if (!row || !row.display) return;
    bucket.push({ id: String(npId).toLowerCase(), priority: row.priority, display: row.display });
  };

  for (let i = 0; i < partKeys.length; i += 1) {
    const key = partKeys[i];
    const meta = lookupPartMeta(partMetaByKey, rootFor(i), key);
    const naming = meta && meta.naming;
    if (!naming) continue;
    if (naming.disablePrefixes) disablePrefixes = true;
    for (const np of naming.prefixes || []) pushNp(np, rankedPrefixes);
    for (const np of naming.titles || []) pushNp(np, rankedTitles);
    for (const np of naming.suffixes || []) {
      const row = resolveNpDisplay(np, invNameParts);
      if (row && row.display) suffixTokens.push(row.display);
    }
  }

  const dedupeKeepOrder = (items) => {
    const out = [];
    const seen = new Set();
    for (const item of items) {
      const label = String(item || "").trim();
      if (!label) continue;
      const sig = label.toLowerCase();
      // Allow intentional repeats (Barrage Barrage) when consecutive from distinct parts.
      out.push(label);
      seen.add(sig);
    }
    return out;
  };

  if (itemType === "Shield") {
    const shieldLabels = [];
    for (let i = 0; i < partKeys.length; i += 1) {
      const key = partKeys[i];
      const meta = lookupPartMeta(partMetaByKey, rootFor(i), key);
      const rowName = meta && meta.naming && meta.naming.tableRow;
      if (!rowName) continue;
      const label = pickShieldTableLabel(
        shieldTable.get(String(rowName).toLowerCase()),
        shieldRoleFromPartKey(key)
      );
      if (label) shieldLabels.push(label);
    }
    // ShieldNameTable labels: keep multiples (Barrage Barrage) and stable alpha order
    // so Barrage stacks precede Scaled for Hopscotch-style cards.
    shieldLabels.sort((a, b) => String(a).localeCompare(String(b)));
    for (const label of shieldLabels) prefixTokens.push(label);
  }

  if (itemType === "Enhancement") {
    const statRows = [];
    const coreKeys = [];
    const prioritySet = new Set((enhTables.priority || []).map((s) => String(s).toLowerCase()));
    for (let i = 0; i < partKeys.length; i += 1) {
      const key = partKeys[i];
      const meta = lookupPartMeta(partMetaByKey, rootFor(i), key);
      const rowName = meta && meta.naming && meta.naming.tableRow;
      if (!rowName) continue;
      const low = String(rowName).toLowerCase();
      // Only stats listed in EnhancementNamingStatPriorityTable drive the title
      // (FireRate/Accuracy combination rows exist but are not naming drivers alone).
      if (enhTables.stat.has(low) && (prioritySet.size === 0 || prioritySet.has(low))) {
        const pri = enhTables.priority.indexOf(low);
        statRows.push({ key: low, pri: pri === -1 ? 999 : pri });
      }
    }
    for (const key of partKeys) {
      if (/^part_core_/i.test(key)) coreKeys.push(key.toLowerCase());
    }
    const uniqCores = [...new Set(coreKeys)];
    if (statRows.length) {
      statRows.sort((a, b) => a.pri - b.pri);
      const primary = statRows[0].key;
      const secondary = statRows.length >= 2 ? statRows[1].key : "single";
      const table = enhTables.stat.get(primary) || {};
      const label = table[secondary] || table.single || "";
      if (label) titleTokens.push(label);
    } else if (uniqCores.length) {
      const primary = uniqCores[0];
      const secondary = uniqCores.length >= 2 ? uniqCores[1] : "single";
      const table = enhTables.core.get(primary) || {};
      const label = table[secondary] || table.single || "";
      if (label) titleTokens.push(label);
    }
  }

  if (itemType === "Classmod") {
    let bodyRow = "";
    const equippedPassives = [];
    for (let i = 0; i < partKeys.length; i += 1) {
      const key = partKeys[i];
      const meta = lookupPartMeta(partMetaByKey, rootFor(i), key);
      const naming = meta && meta.naming;
      if (!naming) continue;
      if (naming.tableRow && (/^leg_body_/i.test(key) || /^body_/i.test(key))) {
        bodyRow = String(naming.tableRow).toLowerCase();
      }
      for (const passive of naming.passives || []) equippedPassives.push(passive);
    }
    const classTable = classModTables.get(String(rootSet || "").toLowerCase());
    const slots = (classTable && bodyRow && classTable.get(bodyRow)) || [];
    let best = null;
    for (const slot of slots) {
      if (!slot.display) continue;
      const hit = equippedPassives.some((p) => (
        (slot.graph && p.graph && slot.graph === p.graph && slot.node && p.node && slot.node === p.node)
        || (slot.node && p.node && slot.node === p.node)
      ));
      if (hit && (!best || slot.slot > best.slot)) best = slot;
    }
    if (best && best.display) prefixTokens.push(best.display);
  }

  rankedPrefixes.sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id));
  rankedTitles.sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id));

  if (!disablePrefixes) {
    for (const row of rankedPrefixes) prefixTokens.push(row.display);
  }
  // Prefer highest-priority title (unique) when multiple titleparts exist.
  if (rankedTitles.length) {
    let candidates = rankedTitles;
    if (itemType === "Ordnance") {
      const blade = rankedTitles.filter((r) => /spinning\s*blade/i.test(r.display));
      if (blade.length) candidates = blade;
    }
    if (itemType === "Repkit") {
      const own = rankedTitles.filter((r) => {
        // Prefer titles from this item's manufacturer repair-kit parts over foreign uniques.
        return true;
      });
      // Prefer Triple Bypass / item np over Pacemaker when multiple unique augments exist:
      // use highest priority among titles whose id includes the item root's unique if possible.
      const bypass = rankedTitles.filter((r) => /bypass|triple/i.test(r.display));
      if (bypass.length) candidates = bypass;
    }
    const topPri = Math.max(...candidates.map((r) => r.priority));
    const top = candidates.filter((r) => r.priority === topPri);
    // Matt Editor prefers second np when multiple on one list; across parts keep unique max priority.
    titleTokens.push(top[top.length - 1].display);
  }

  const parts = [
    ...dedupeKeepOrder(prefixTokens),
    ...dedupeKeepOrder(titleTokens),
    ...dedupeKeepOrder(suffixTokens)
  ];
  // Keep intentional consecutive duplicates (Barrage Barrage) from shield augments.
  return parts.join(" ").replace(/\s+/g, " ").trim();
}

function manufacturerPrefixCode(manufacturer) {
  const m = String(manufacturer || "").trim().toLowerCase();
  if (m === "order") return "ord";
  if (m === "daedalus") return "dad";
  if (m === "jakobs") return "jak";
  if (m === "tediore") return "ted";
  if (m === "torgue") return "tor";
  if (m === "vladof") return "vla";
  if (m === "maliwan") return "mal";
  if (m === "ripper") return "bor";
  if (m === "atlas") return "atl";
  if (m === "hyperion") return "hyp";
  if (m === "cov") return "cov";
  return "";
}

function collectPartTags(partKeys, legitByKey, partMetaByKey, rootSet, partRoots) {
  const tags = new Set();
  partKeys.forEach((key, i) => {
    const root = (Array.isArray(partRoots) && partRoots[i]) || rootSet;
    const legit = lookupLegitPart(legitByKey, root, key);
    for (const t of (legit && legit.add) || []) {
      if (t) tags.add(String(t).toLowerCase());
    }
    const meta = lookupPartMeta(partMetaByKey, root, key);
    for (const t of (meta && meta.tags) || []) {
      if (t) tags.add(String(t).toLowerCase());
    }
  });
  return tags;
}

function pickLicensedPartPrefix(manufacturer, tags, namingTables, diagnostics = {}) {
  const code = manufacturerPrefixCode(manufacturer);
  const tables = namingTables && namingTables.get(code);
  if (!tables || !tables.licensed || !tables.licensed.size) return "";
  let rowName = "default";
  for (const cand of LICENSED_PREFIX_ROW_PRIORITY) {
    if (cand === "default") continue;
    if (tags.has(cand) && tables.licensed.has(cand)) {
      rowName = cand;
      break;
    }
  }
  if (!tables.licensed.has(rowName)) {
    if (!tables.licensed.has("default")) return "";
    rowName = "default";
  }
  const row = tables.licensed.get(rowName) || {};
  // Mixed magazine families require native aspect selection. The old filter
  // hid competing families; guessing a column can turn Wasted into Affixed.
  if (LICENSED_PREFIX_COL_PRIORITY.filter((key) => key !== "default" && tags.has(key) && row[key]).length > 1) {
    diagnostics.ambiguous = true;
    return "";
  }
  let colName = "default";
  for (const cand of LICENSED_PREFIX_COL_PRIORITY) {
    if (cand === "default") continue;
    if (tags.has(cand) && row[cand]) {
      colName = cand;
      break;
    }
  }
  let label = row[colName] || row.default || "";
  // TED payload-style cells are stored as "-Wasted"; strip the marker and keep the word.
  // (Previously skipped entirely, which dropped Vladof Mantra's licensed prefix.)
  if (label.startsWith("-")) label = label.slice(1).trim();
  return label;
}

function composeWeaponDisplayName(licensedPrefix, statPrefix, uniqueName, fallback) {
  const parts = [licensedPrefix, statPrefix, uniqueName].map((s) => String(s || "").trim()).filter(Boolean);
  if (parts.length) return parts.join(" ");
  return String(fallback || "").trim();
}

function pickRarityFromParts(partKeys, partNames, legitByKey, rootSet, partRoots) {
  for (const [index, key] of partKeys.entries()) {
    const row = lookupLegitPart(legitByKey, partRoots?.[index] || rootSet, key);
    if (row && row.rarity) {
      const label = normalizeRarity(row.rarity);
      if (label) return label;
    }
  }
  return guessRarityFromPartNames(partNames);
}

function collectPerks(partKeys, perkByPart, rootSet, partRoots, opts = {}) {
  const red = [];
  const desc = [];
  if (!perkByPart || !perkByPart.size) return { red, desc, perk_lines: [] };
  const itemRoot = String(rootSet || "").toLowerCase();
  const namingKey = String(opts.namingPartKey || "").toLowerCase();
  const namingRoot = String(opts.namingPartRoot || "").toLowerCase();
  const namingIndex = Number.isInteger(opts.namingPartIndex) ? opts.namingPartIndex : -1;
  const namingUnique = String(opts.namingUnique || "").trim().toLowerCase();
  const legitByKey = opts.legitByKey || null;
  const shinyRed = [];
  const namingRed = [];
  const uniqueCarrierRed = [];
  const partMatchesNamingUnique = (key, root) => {
    if (!namingUnique || !legitByKey) return false;
    const hit = lookupLegitPart(legitByKey, root, key);
    const names = (hit && hit.np_names) || [];
    return names.some((n) => String(n || "").trim().toLowerCase() === namingUnique);
  };
  for (let i = 0; i < partKeys.length; i += 1) {
    const key = partKeys[i];
    const root = String((Array.isArray(partRoots) && partRoots[i]) || itemRoot || "").toLowerCase();
    // Root-scoped only: bare part keys (part_barrel_02_a) collide across heavy/AR pools
    // and paste Wide Disk / Heat Exchange onto franken Order ARs.
    const row = (root && perkByPart.get(`${root}::${key}`))
      || (!root ? perkByPart.get(key) : null);
    if (!row) continue;
    const isShiny = /shiny/i.test(key);
    const isNamingWinner = Boolean(
      namingKey
      && key === namingKey
      && (namingIndex < 0 || i === namingIndex)
      && (!namingRoot || root === namingRoot)
    );
    const isNamingFamily = isNamingWinner || partMatchesNamingUnique(key, root);
    const isUniqueCarrier = /spinning_blade|hopscotch|triplebypass|conflux|roulette|star_helix|kindread|mantra/i.test(key);
    for (const line of row.red || []) {
      const clean = sanitizePerkPreviewText(line);
      if (!clean) continue;
      if (isShiny) {
        if (!shinyRed.includes(clean)) shinyRed.push(clean);
        continue;
      }
      // In-game cards show one flavor line from the naming unique — not every franken barrel's red.
      if (isNamingFamily) {
        if (!namingRed.includes(clean)) namingRed.push(clean);
        continue;
      }
      if (isUniqueCarrier && !namingKey && !namingUnique) {
        if (!uniqueCarrierRed.includes(clean)) uniqueCarrierRed.push(clean);
      }
    }
    for (const line of row.desc || []) {
      const clean = sanitizePerkPreviewText(line);
      if (clean && !desc.includes(clean)) desc.push(clean);
    }
  }
  // Prefer shiny overlay, then naming-unique red, then unique-carrier red when no naming hit.
  for (const line of shinyRed) {
    if (!red.includes(line)) red.push(line);
  }
  for (const line of namingRed) {
    if (!red.includes(line)) red.push(line);
  }
  if (!namingRed.length) {
    for (const line of uniqueCarrierRed) {
      if (!red.includes(line)) red.push(line);
    }
  }
  const perk_lines = [...red, ...desc];
  return { red, desc, perk_lines };
}

function resolveFromHuman(human, ctx = {}) {
  const out = emptyCard();
  const text = String(human || "").trim();
  if (!text) return out;
  const header = text.match(/^\s*(\d+)\s*,/);
  if (!header) return out;
  const typeId = Number(header[1]);
  const typeIdIndex = ctx.typeIdIndex || buildTypeIdIndex(ctx.gzoPartsMap);
  const typeRow = typeIdIndex.get(typeId);
  const info = typeInfoFromLabel(typeRow ? typeRow.label : "");
  const itemType = info.type || "";
  const manufacturer = info.manufacturer || "";
  const characterClass = info.character_class || "";
  const { names: partNames, keys: partKeys, roots: partRoots } = partNamesFromHuman(text, typeIdIndex);
  const legitByKey = ctx.legitByKey || buildLegitPartIndex(ctx.legitRules);
  const partMetaByKey = ctx.partMetaByKey || new Map();
  const namingTables = ctx.namingTables || new Map();
  const npHit = GUN_TYPES.has(itemType)
    ? pickWeaponTitle(partKeys, partRoots, ctx)
    : pickBestNpNameHit(partKeys, legitByKey, info.set, partRoots);
  const npName = npHit ? npHit.name : "";
  const slugUnique = uniqueDisplayFromPartNames(partNames);
  // Enhancements: cores like part_core_jak_leaper slug to perk names (Leaper); title comes
  // from EnhancementNaming* tables instead.
  let uniqueName = itemType === "Enhancement" ? "" : (npName || slugUnique);
  const tags = collectPartTags(partKeys, legitByKey, partMetaByKey, info.set, partRoots);
  const licensedDiagnostics = {};
  const licensedPrefix = GUN_TYPES.has(itemType)
    ? pickLicensedPartPrefix(manufacturer, tags, namingTables, licensedDiagnostics)
    : "";
  // OakWeaponNamingStrategy uses assembled attribute thresholds and explicit
  // name priorities. The previous body-tag counter produced plausible but wrong
  // words (Strong Kitty / Globalist Mantra / Anisotropic Conflux).
  const statPrefix = "";
  let rarity = pickRarityFromParts(partKeys, partNames, legitByKey, info.set, partRoots);
  if (
    !rarity
    && partNames.some((n) => /(?:^|\.)part_firmware_/i.test(leafPartName(n)))
  ) {
    rarity = "Legendary";
  }
  if (!rarity && /shiny_/i.test(text)) rarity = "Pearlescent";
  if (!rarity && uniqueName && /part_barrel_\d+_/i.test(partKeys.join(" "))) {
    rarity = "Legendary";
  }
  const element = guessDamageTypeFromPartNames(partNames);
  const fallback = fallbackDisplayName(manufacturer, itemType, characterClass, info.set);
  let display = "";
  if (GUN_TYPES.has(itemType)) {
    display = composeWeaponDisplayName(licensedPrefix, statPrefix, uniqueName, fallback);
  } else {
    const gearName = composeGearDisplayName(itemType, partKeys, partMetaByKey, info.set, ctx, partRoots);
    if (gearName) {
      display = gearName;
      if (itemType === "Enhancement") uniqueName = gearName;
      else if (/spinning\s*blade/i.test(gearName)) uniqueName = "Spinning Blade";
      else if (/\bhopscotch\b/i.test(gearName)) uniqueName = "Hopscotch";
      else if (/triple\s*bypass/i.test(gearName)) uniqueName = "Triple Bypass";
    } else {
      display = composeWeaponDisplayName("", "", uniqueName || npName || slugUnique, fallback);
      if (!uniqueName) uniqueName = npName || slugUnique;
    }
  }
  const perks = collectPerks(partKeys, ctx.perkByPart || new Map(), info.set, partRoots, {
    namingPartKey: npHit ? npHit.key : "",
    namingPartRoot: npHit ? npHit.root : "",
    namingPartIndex: npHit ? npHit.index : -1,
    namingUnique: uniqueName || npName || "",
    legitByKey
  });
  out.type_id = String(typeId);
  out.set = info.set || "";
  out.manufacturer = manufacturer;
  out.item_type = itemType;
  out.type = itemType;
  const titleType = npHit && ctx.perkByPart?.get(`${npHit.root}::${npHit.key}`)?.item_type;
  if (GUN_TYPES.has(itemType) && GUN_TYPES.has(titleType)) {
    out.item_type = titleType;
    out.type = titleType;
  }
  out.character_class = characterClass;
  out.category = categoryForType(itemType);
  out.rarity = rarity;
  out.element = element;
  out.damage_type = element;
  out.display_name = display;
  out.unique_name = uniqueName;
  out.licensed_prefix = licensedPrefix;
  out.stat_prefix = statPrefix;
  if (GUN_TYPES.has(itemType)) {
    out.naming = weaponNamingStatus(info.set, ctx.rootNamingIndex || new Map(), ctx.namingStrategies || new Map());
    out.name_status = out.naming.status;
  }
  out.part_names = partNames;
  out.part_keys = partKeys;
  out.part_roots = partRoots || [];
  out.red_text = perks.red;
  out.description_lines = perks.desc;
  out.perk_lines = perks.perk_lines;
  out.human = text;
  const levelMatch = text.match(/^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*(\d+)/);
  out.level = levelMatch ? Number(levelMatch[1]) : null;
  out.dps = null;
  out.damage = null;
  out.accuracy = null;
  out.reload = null;
  out.fire_rate = null;
  out.magazine = null;
  out.crit = null;
  out.value = null;
  out.stats_ok = false;
  out.stats_source = "none";
  out.stats_blocked = [];
  out.meta_ok = Boolean(display || manufacturer || itemType || rarity);
  out.meta_source = out.meta_ok ? (uniqueName ? "offline_nexus" : "offline_gzo") : "none";
  if (ctx.statData && out.meta_ok) {
    attachStatsToCard(out, ctx.statData);
    const strategy = ctx.namingStrategies?.get(out.naming?.strategy);
    const factors = out.naming_factors;
    if (strategy && factors && out.native_naming_ready && Number.isFinite(out.damage) && Number.isFinite(out.fire_rate)
      && out.naming.required_attributes.every(row => Number.isFinite(factors[row.name]))) {
      const result = evaluateWeaponNaming(strategy,factors);
      out.stat_prefix = result.prefix;
      out.display_name = composeWeaponDisplayName(out.licensed_prefix,result.prefix,out.unique_name,display);
      out.name_status = licensedDiagnostics.ambiguous ? "partial" : "resolved";
      out.naming = {...out.naming,status:out.name_status,reason:licensedDiagnostics.ambiguous ? "conflicting_licensed_parts" : "",source:result.source,factors};
    }
  }
  return out;
}

function resolveFromPartNames(typeId, partNames, ctx = {}) {
  const typeIdIndex = ctx.typeIdIndex || buildTypeIdIndex(ctx.gzoPartsMap);
  const label = (typeIdIndex.get(Number(typeId)) || {}).label || "";
  const syntheticTable = {};
  const names = Array.isArray(partNames) ? partNames.map(String) : [];
  names.forEach((name, i) => {
    syntheticTable[String(i + 1)] = name;
  });
  const syntheticIndex = new Map(typeIdIndex);
  syntheticIndex.set(Number(typeId), { label, table: syntheticTable });
  const refs = names.map((_, i) => `{${i + 1}}`).join(" ");
  const human = `${Number(typeId)}, 0, 1, 50| 1, 1|| ${refs}|`;
  return resolveFromHuman(human, { ...ctx, typeIdIndex: syntheticIndex });
}

function mergeCardOntoEntry(entry, card, { preferResolvedName = true } = {}) {
  if (!entry || typeof entry !== "object" || !card || !card.meta_ok) return entry;
  const next = { ...entry };
  const catalogName = String(entry.display_name || entry.name || entry.summary || "").trim();
  const resolvedName = String(card.display_name || "").trim();
  const catalogLooksGeneric = !catalogName
    || /^unknown$/i.test(catalogName)
    || (card.manufacturer && catalogName === `${card.manufacturer} ${card.item_type}`.trim())
    || (card.item_type && catalogName === card.item_type);
  const offlineIsComposed = Boolean(
    card.unique_name || card.licensed_prefix || card.stat_prefix
  );
  // Prefer mined compose (unique / licensed+stat prefixes). Keep specialty catalog
  // names when the offline card is only a manufacturer+type fallback.
  const shouldReplaceName = Boolean(
    preferResolvedName
    && resolvedName
    && (offlineIsComposed || catalogLooksGeneric || !catalogName)
  );
  if (shouldReplaceName) {
    next.display_name = resolvedName;
    if (Object.prototype.hasOwnProperty.call(next, "name") || next.name != null) {
      next.name = resolvedName;
    }
  }
  if (card.rarity) next.rarity = card.rarity;
  if (card.manufacturer) next.manufacturer = card.manufacturer;
  if (card.item_type) {
    next.item_type = card.item_type;
    if (!next.type || catalogLooksGeneric) next.type = card.item_type;
  }
  if (card.character_class) next.character_class = card.character_class;
  if (card.category) next.category = card.category;
  if (card.element) {
    next.element = card.element;
    next.damage_type = card.element;
  }
  if (card.perk_lines && card.perk_lines.length) next.perk_lines = card.perk_lines.slice();
  if (card.red_text && card.red_text.length) next.red_text = card.red_text.slice();
  if (card.description_lines && card.description_lines.length) {
    next.description_lines = card.description_lines.slice();
  }
  // Phase B: copy mined combat stats when the offline evaluator produced them.
  if (card.dps != null) next.dps = card.dps;
  else next.dps = null;
  if (card.damage != null) next.damage = card.damage;
  if (card.accuracy != null) next.accuracy = card.accuracy;
  if (card.reload != null) next.reload = card.reload;
  if (card.fire_rate != null) next.fire_rate = card.fire_rate;
  if (card.magazine != null) next.magazine = card.magazine;
  if (card.crit != null) next.crit = card.crit;
  if (card.value != null) next.value = card.value;
  else next.value = null;
  if (card.stats_ok) next.stats_ok = true;
  if (card.stats_source) next.stats_source = card.stats_source;
  next.card_resolved = true;
  next.name_status = card.name_status || "";
  next.naming = card.naming || null;
  next.meta_source = card.meta_source || "offline_nexus";
  return next;
}

function readJsonIfExists(filePath) {
  try {
    if (!filePath || !fs.existsSync(filePath)) return null;
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return null;
  }
}

function defaultDataPaths(sourceRoot) {
  const root = sourceRoot || process.cwd();
  const legitItems = path.join(root, "external_app", "v22_parts_codes_fixed", "matt_editor", "LegitItems");
  const modData = path.join(root, "mod_extracted", "MattsSDKBoostingTools");
  const resources = path.join(root, "external_app", "v22_parts_codes_fixed", "resources");
  return {
    gzoPartsMap: [
      path.join(modData, "gzo_parts_map.json"),
      path.join(resources, "gzo_parts_map.json"),
      path.join(root, "docs", "data", "gzo_parts_map.json")
    ],
    legitRules: [
      path.join(modData, "legit_rules_flat.json"),
      path.join(resources, "legit_rules_flat.json")
    ],
    uiStat: [
      path.join(legitItems, "Nexus-Data-ui_stat0.json"),
      path.join(legitItems, "Nexus-Data-ui_stat4.json"),
      path.join(legitItems, "Nexus-Data-ui_stat6.json")
    ],
    inv: [
      path.join(legitItems, "Nexus-Data-inv0.json"),
      path.join(legitItems, "Nexus-Data-inv4.json"),
      path.join(legitItems, "Nexus-Data-inv6.json")
    ],
    invNamePart: [
      path.join(legitItems, "Nexus-Data-inv_name_part0.json"),
      path.join(legitItems, "Nexus-Data-inv_name_part4.json"),
      path.join(legitItems, "Nexus-Data-inv_name_part6.json")
    ],
    invNameStrategy: [
      path.join(legitItems, "Nexus-Data-inv_name_strategy0.json"),
      path.join(legitItems, "Nexus-Data-inv_name_strategy4.json"),
      path.join(legitItems, "Nexus-Data-inv_name_strategy6.json")
    ],
    gbxTables: [
      path.join(legitItems, "Nexus-Data-gbx_ue_data_table0.json"),
      path.join(legitItems, "Nexus-Data-gbx_ue_data_table4.json"),
      path.join(legitItems, "Nexus-Data-gbx_ue_data_table6.json")
    ]
  };
}

function firstExisting(paths) {
  for (const p of paths || []) {
    if (p && fs.existsSync(p)) return p;
  }
  return "";
}

function loadResolver(options = {}) {
  const defaults = defaultDataPaths(options.sourceRoot);
  const paths = { ...defaults, ...(options.paths || {}) };
  const gzoPath = options.gzoPartsMapPath || firstExisting(paths.gzoPartsMap);
  const legitPath = options.legitRulesPath || firstExisting(paths.legitRules);
  const gzoPartsMap = options.gzoPartsMap || readJsonIfExists(gzoPath) || {};
  const legitRules = options.legitRules || readJsonIfExists(legitPath) || { roots: [] };
  const typeIdIndex = buildTypeIdIndex(gzoPartsMap);
  const legitByKey = buildLegitPartIndex(legitRules);

  let perkByPart = options.perkByPart || null;
  let partMetaByKey = options.partMetaByKey || null;
  let namingTables = options.namingTables || null;
  let invNameParts = options.invNameParts || null;
  let shieldNameTable = options.shieldNameTable || null;
  let enhancementNaming = options.enhancementNaming || null;
  let classModPassiveTables = options.classModPassiveTables || null;
  const invPayloads = (options.invPaths || paths.inv || [])
    .map((p) => readJsonIfExists(p))
    .filter(Boolean);
  const gbxPayloads = (options.gbxTablePaths || paths.gbxTables || [])
    .map((p) => readJsonIfExists(p))
    .filter(Boolean);
  const namingStrategies = loadNamingStrategies((paths.invNameStrategy || [])
    .map((p) => readJsonIfExists(p)).filter(Boolean));
  const rootNamingIndex = buildRootNamingIndex(invPayloads);
  if (!perkByPart && options.loadPerks !== false) {
    const uiPayloads = (options.uiStatPaths || paths.uiStat || [])
      .map((p) => readJsonIfExists(p))
      .filter(Boolean);
    perkByPart = buildPerkIndexFromUiAndInv(uiPayloads, invPayloads);
  }
  if (!perkByPart) perkByPart = new Map();
  if (!partMetaByKey) {
    partMetaByKey = buildPartTagAndStatIndex(invPayloads);
  }
  if (!namingTables) {
    namingTables = buildWeaponNamingTables(gbxPayloads);
  }
  if (!invNameParts) {
    const invNamePayloads = (options.invNamePartPaths || paths.invNamePart || [])
      .map((p) => readJsonIfExists(p))
      .filter(Boolean);
    invNameParts = buildInvNamePartIndex(invNamePayloads);
  }
  if (!shieldNameTable) {
    shieldNameTable = buildShieldNameTable(gbxPayloads);
  }
  if (!enhancementNaming) {
    enhancementNaming = buildEnhancementNamingTables(gbxPayloads);
  }
  if (!classModPassiveTables) {
    classModPassiveTables = buildClassModPassiveNameTables(gbxPayloads);
  }

  let statData = options.statData || null;
  if (!statData && options.loadStats !== false) {
    try {
      statData = loadStatData({ sourceRoot: options.sourceRoot });
    } catch {
      statData = null;
    }
  }

  const ctx = {
    gzoPartsMap,
    legitRules,
    typeIdIndex,
    legitByKey,
    perkByPart,
    partMetaByKey,
    namingTables,
    namingStrategies,
    rootNamingIndex,
    invNameParts,
    shieldNameTable,
    enhancementNaming,
    classModPassiveTables,
    statData,
    gzoPath,
    legitPath
  };

  return {
    ctx,
    resolveFromHuman(human) {
      return resolveFromHuman(human, ctx);
    },
    resolveFromPartNames(typeId, partNames) {
      return resolveFromPartNames(typeId, partNames, ctx);
    },
    mergeCardOntoEntry,
    stats: {
      type_ids: typeIdIndex.size,
      legit_parts: legitByKey.size,
      perk_parts: perkByPart.size,
      naming_mfgs: namingTables.size,
      naming_strategies: namingStrategies.size,
      part_meta: partMetaByKey.size,
      inv_name_parts: invNameParts.size,
      shield_name_rows: shieldNameTable.size,
      attributes: statData ? statData.attributes.size : 0,
      datatables: statData ? statData.tables.size : 0,
      inv_roots: statData ? statData.invRoots.size : 0,
      gzo_path: gzoPath || "",
      legit_path: legitPath || ""
    }
  };
}

module.exports = {
  emptyCard,
  loadResolver,
  resolveFromHuman,
  resolveFromPartNames,
  mergeCardOntoEntry,
  buildTypeIdIndex,
  buildLegitPartIndex,
  buildPerkIndexFromUiAndInv,
  defaultDataPaths,
  stripUiStatFormatText,
  sanitizePerkPreviewText,
  loadStatData,
  attachStatsToCard
};
