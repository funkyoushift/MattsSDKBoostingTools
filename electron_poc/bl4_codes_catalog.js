"use strict";

const crypto = require("crypto");
const fs = require("fs/promises");
const path = require("path");

const RESOURCE_FILES = {
  lootlemon: "MattsSDKBoostingTools_lootlemon_codes.json",
  custom: "custom_bl4_codes.json",
  gzo: "MattsSDKBoostingTools_gzo_codes.json"
};

const DEFAULT_RESOURCE_DIR = path.resolve(__dirname, "..", "external_app", "v22_parts_codes_fixed", "resources");
const GZO_CODES_URL = "https://save-editor.be/GZO/Borderlands4/Codes.html";
const GZO_CATALOG_URL = "https://save-editor.be/GZO/Borderlands4/codes/api.php?action=catalog";
const GZO_CACHE_VERSION = 6;
const GZO_SERIAL_RE = /@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{\/}~]{12,}/g;

function text(value) {
  return String(value ?? "").trim();
}

function compactKey(value) {
  return text(value).toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function unique(values) {
  const seen = new Set();
  const out = [];
  for (const value of values) {
    const label = text(value);
    if (!label) continue;
    const key = label.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(label);
  }
  return out.sort((a, b) => a.localeCompare(b));
}

function toArray(value) {
  if (Array.isArray(value)) {
    return value.map(text).filter(Boolean);
  }
  const raw = text(value);
  if (!raw) return [];
  return raw.split(/[;,|]/g).map(text).filter(Boolean);
}

function hasValue(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim() !== "";
  return true;
}

function field(raw, ...keys) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return "";
  const lowered = new Map(Object.entries(raw).map(([key, value]) => [String(key).toLowerCase(), value]));
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(raw, key) && hasValue(raw[key])) return raw[key];
    const lowerValue = lowered.get(String(key).toLowerCase());
    if (hasValue(lowerValue)) return lowerValue;
  }
  return "";
}

function validSerial(value) {
  return /^@U[!-~]+$/.test(text(value));
}

function normalizeWebUrl(value, baseUrl = GZO_CODES_URL) {
  const raw = text(value);
  if (!raw) return "";
  try {
    return new URL(raw, baseUrl).toString();
  } catch {
    return raw;
  }
}

function stableId(prefix, raw, serial) {
  const rawId = text(raw.id || raw.uuid || raw.key);
  if (rawId) return `${prefix}:${compactKey(rawId) || crypto.createHash("sha1").update(rawId).digest("hex").slice(0, 16)}`;
  return `${prefix}:${crypto.createHash("sha1").update(`${prefix}|${serial}`).digest("hex").slice(0, 16)}`;
}

function normalizeTitle(value, fallback = "") {
  const raw = text(value);
  return raw || fallback;
}

function normalizeType(raw) {
  const value = normalizeTitle(raw);
  const key = compactKey(value);
  const map = {
    class_mod: "Class Mods",
    class_mods: "Class Mods",
    classmod: "Class Mods",
    classmods: "Class Mods",
    assault_rifle: "Assault Rifle",
    assault_rifles: "Assault Rifle",
    ar: "Assault Rifle",
    smg: "SMG",
    sniper: "Sniper Rifle",
    sniper_rifle: "Sniper Rifle",
    sniper_rifles: "Sniper Rifle",
    shotgun: "Shotgun",
    shotguns: "Shotgun",
    pistol: "Pistol",
    pistols: "Pistol",
    grenade: "Grenade",
    grenades: "Grenade",
    ordnance: "Ordnance",
    shield: "Shield",
    shields: "Shield",
    repkit: "Repkit",
    repkits: "Repkit",
    enhancement: "Enhancement",
    enhancements: "Enhancement",
    firmware: "Firmware",
    firmwares: "Firmware"
  };
  return map[key] || value;
}

function normalizeRarity(raw) {
  const value = normalizeTitle(raw);
  const key = compactKey(value);
  const map = {
    legendary: "Legendary",
    pearl: "Pearlescent",
    pearlescent: "Pearlescent",
    epic: "Epic",
    rare: "Rare",
    uncommon: "Uncommon",
    common: "Common"
  };
  return map[key] || value;
}

function normalizeListing(raw, fallback) {
  const value = normalizeTitle(raw, fallback);
  const key = compactKey(value);
  if (key === "custom_static") return "Custom Static";
  if (key === "lootlemon") return "Lootlemon";
  if (key === "gzo") return "GZO";
  if (key === "modded") return "Modded";
  return value;
}

function normalizeMattmab(raw) {
  const value = normalizeTitle(raw);
  const key = compactKey(value);
  if (!key) return "UNCHECKED";
  if (["pass", "passed", "legit", "valid"].includes(key)) return "PASS";
  if (["fail", "failed", "modded", "invalid"].includes(key)) return "FAIL";
  if (["error", "parse_error", "exception"].includes(key)) return "ERROR";
  if (["unchecked", "not_checked", "unknown"].includes(key)) return "UNCHECKED";
  return value.toUpperCase();
}

function normalizeClassification(raw, tags) {
  const value = normalizeTitle(raw);
  const key = compactKey(value);
  if (key === "modded") return "Modded";
  if (key === "legit") return "Legit";
  if (tags.some((tag) => compactKey(tag) === "modded")) return "Modded";
  return value;
}

function decodedIdentity(raw) {
  const value = raw.decoded_identity;
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return { ...value };
  }
  return {};
}

function collectGzoTags(raw) {
  const tags = [];
  for (const key of ["tags", "tag", "labels", "categories", "meta", "notes"]) {
    const value = field(raw, key);
    if (Array.isArray(value)) tags.push(...value.map(text).filter(Boolean));
    else if (value && typeof value === "object") tags.push(...Object.values(value).map(text).filter(Boolean));
    else if (hasValue(value)) tags.push(text(value));
  }
  return tags;
}

function classifyGzoTags(tags) {
  const all = tags.join(" ").toLowerCase();
  const typeMap = [
    ["class mod", "Class Mods"],
    ["classmod", "Class Mods"],
    ["weapon", "Weapons"],
    ["shield", "Shield"],
    ["grenade", "Ordnance"],
    ["repkit", "Repkit"],
    ["enhancement", "Enhancement"],
    ["firmware", "Firmware"]
  ];
  const out = { type: "", rarity: "", manufacturer: "" };
  const typeMatch = typeMap.find(([needle]) => all.includes(needle));
  if (typeMatch) out.type = typeMatch[1];
  for (const rarity of ["Pearlescent", "Legendary", "Epic", "Rare", "Uncommon", "Common"]) {
    if (all.includes(rarity.toLowerCase())) {
      out.rarity = rarity;
      break;
    }
  }
  for (const manufacturer of ["C4SH", "Atlas", "COV", "Daedalus", "Hyperion", "Jakobs", "Maliwan", "Order", "Ripper", "Tediore", "Torgue", "Vladof"]) {
    if (all.includes(manufacturer.toLowerCase())) {
      out.manufacturer = manufacturer;
      break;
    }
  }
  return out;
}

function normalizeGzoRow(raw, inheritedListing = "") {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const serial = text(field(raw, "base85", "Base85", "serial", "code", "value"));
  if (!validSerial(serial)) return null;
  const tags = collectGzoTags(raw);
  const classified = classifyGzoTags(tags);
  const listing = normalizeListing(
    field(raw, "targetListing", "listing", "destination", "bucket", "folder", "legitOrModded", "list", "category") || inheritedListing,
    "GZO"
  );
  const type = normalizeType(field(raw, "type", "itemType") || classified.type);
  return {
    id: "",
    name: normalizeTitle(field(raw, "name", "displayName", "title", "itemName"), "GZO Serial"),
    serial,
    listing,
    category: normalizeType(field(raw, "category", "type", "itemType") || classified.type || "BL4 Codes"),
    type,
    rarity: normalizeRarity(field(raw, "rarity") || classified.rarity),
    manufacturer: normalizeTitle(field(raw, "manufacturer", "maker") || classified.manufacturer),
    creator: normalizeTitle(field(raw, "creator", "author", "creatorName", "owner")),
    source: "GZO",
    url: normalizeWebUrl(field(raw, "websiteUrl", "url", "link", "pageUrl") || GZO_CODES_URL),
    image_url: normalizeWebUrl(field(raw, "image", "image_url", "imageUrl", "thumbnail", "screenshot", "screenshot_url", "photo", "picture")),
    deserialized: text(field(raw, "deserialized", "human", "decoded", "decodedSerial", "human_serial")),
    mattmab_validator: normalizeTitle(field(raw, "mattmab_validator", "validator", "validation", "mattmabResult", "result")),
    mattmab_validator_detail: normalizeTitle(field(raw, "mattmab_validator_detail", "validatorDetail", "detail")),
    tags: unique([...tags, "gzo"])
  };
}

function walkGzoJson(value, out, seen, inheritedListing = "") {
  if (Array.isArray(value)) {
    for (const child of value) walkGzoJson(child, out, seen, inheritedListing);
    return;
  }
  if (!value || typeof value !== "object") return;
  const listing = normalizeListing(
    field(value, "targetListing", "listing", "destination", "bucket", "folder", "legitOrModded", "list") || inheritedListing,
    "GZO"
  );
  const row = normalizeGzoRow(value, listing);
  if (row && !seen.has(row.serial.toLowerCase())) {
    seen.add(row.serial.toLowerCase());
    out.push(row);
  }
  for (const child of Object.values(value)) walkGzoJson(child, out, seen, listing);
}

function parseGzoCatalogText(body) {
  const out = [];
  const seen = new Set();
  try {
    walkGzoJson(JSON.parse(body), out, seen, "");
  } catch {
    for (const match of body.matchAll(GZO_SERIAL_RE)) {
      const serial = text(match[0]);
      if (!validSerial(serial) || seen.has(serial.toLowerCase())) continue;
      seen.add(serial.toLowerCase());
      out.push({
        id: "",
        name: "GZO Serial",
        serial,
        listing: "GZO",
        category: "BL4 Codes",
        type: "",
        rarity: "",
        manufacturer: "",
        creator: "",
        source: "GZO",
        url: GZO_CODES_URL,
        image_url: "",
        deserialized: "",
        mattmab_validator: "",
        mattmab_validator_detail: "",
        tags: ["gzo"]
      });
    }
  }
  return out;
}

function normalizeCodeEntry(raw, defaults) {
  if (!raw || typeof raw !== "object") return null;
  const serial = text(raw.serial || raw.code || raw.base85);
  if (!validSerial(serial)) return null;
  const tags = unique([
    ...toArray(raw.tags),
    ...toArray(raw.extra_tags),
    defaults.tag,
    raw.creator,
    raw.source,
    raw.listing
  ]);
  const source = normalizeTitle(raw.source, defaults.source);
  const listing = normalizeListing(raw.listing || raw.listing_name || raw.source, defaults.listing || source);
  const type = normalizeType(raw.type || raw.category || raw.item_type || raw.gear_type || raw.decoded_type);
  const manufacturer = normalizeTitle(raw.manufacturer || raw.mfr || raw.manu);
  const rarity = normalizeRarity(raw.rarity || raw.quality);
  const classification = normalizeClassification(raw.classification || raw.validation || raw.mattmab_classification, tags);
  const mattmab = normalizeMattmab(raw.mattmab_validator || raw.mattmab_result || raw.mattmab || raw.validation_result);
  const identity = decodedIdentity(raw);

  return {
    id: stableId(defaults.prefix, raw, serial),
    name: normalizeTitle(raw.name || raw.title || raw.label, "Unnamed Code"),
    serial,
    source,
    listing,
    category: normalizeType(raw.category || raw.item_category || raw.group || type),
    type,
    manufacturer,
    rarity,
    creator: normalizeTitle(raw.creator || raw.author),
    classification,
    mattmab_validator: mattmab,
    mattmab_validator_detail: text(raw.mattmab_validator_detail || raw.mattmab_detail || raw.validation_detail),
    url: text(raw.url || raw.lootlemon_url || raw.link),
    image_url: normalizeWebUrl(raw.image_url || raw.imageUrl || raw.image || raw.thumbnail || raw.screenshot || raw.screenshot_url || raw.photo || raw.picture || raw.img),
    deserialized: text(raw.deserialized || raw.human || raw.decoded || raw.decoded_serial || raw.human_serial),
    tags,
    notes: text(raw.notes || raw.description || raw.comment),
    decoded_identity: identity,
    raw_id: text(raw.id || raw.uuid || raw.key),
    source_file: defaults.file
  };
}

async function readJsonFileOptional(fullPath, warnings, label, options = {}) {
  try {
    const raw = await fs.readFile(fullPath, "utf8");
    return JSON.parse(raw);
  } catch (error) {
    if (error && error.code === "ENOENT") {
      if (!options.optional) warnings.push(`${label} is not bundled.`);
      return null;
    }
    warnings.push(`${label} could not be read: ${error.message}`);
    return null;
  }
}

async function readJsonOptional(resourceDir, file, warnings, options = {}) {
  return readJsonFileOptional(path.join(resourceDir, file), warnings, file, options);
}

function entriesFromJson(json) {
  if (Array.isArray(json)) return json;
  if (json && Array.isArray(json.entries)) return json.entries;
  if (json && Array.isArray(json.codes)) return json.codes;
  if (json && typeof json === "object") {
    return Object.values(json).filter((value) => value && typeof value === "object" && !Array.isArray(value));
  }
  return [];
}

function mergeBySerial(rows) {
  const bySerial = new Map();
  for (const row of rows) {
    const key = row.serial.toLowerCase();
    const existing = bySerial.get(key);
    if (!existing) {
      bySerial.set(key, row);
      continue;
    }
    bySerial.set(key, {
      ...existing,
      ...Object.fromEntries(Object.entries(row).filter(([, value]) => {
        if (Array.isArray(value)) return value.length > 0;
        if (value && typeof value === "object") return Object.keys(value).length > 0;
        return text(value);
      })),
      tags: unique([...(existing.tags || []), ...(row.tags || [])])
    });
  }
  return Array.from(bySerial.values()).sort((a, b) => a.name.localeCompare(b.name));
}

function filterValues(entries) {
  return {
    listings: unique(entries.flatMap((entry) => [entry.listing, entry.classification])),
    types: unique(entries.map((entry) => entry.type)),
    manufacturers: unique(entries.map((entry) => entry.manufacturer)),
    rarities: unique(entries.map((entry) => entry.rarity)),
    creators: unique(entries.map((entry) => entry.creator)),
    mattmabResults: ["All", "Legit", "Modded", "Error", "Unchecked"]
  };
}

async function loadBl4Catalog(resourceDir = DEFAULT_RESOURCE_DIR, options = {}) {
  const warnings = [];
  const sources = [
    {
      key: "lootlemon",
      defaults: {
        prefix: "lootlemon",
        source: "Lootlemon",
        listing: "Lootlemon",
        tag: "lootlemon",
        file: RESOURCE_FILES.lootlemon
      }
    },
    {
      key: "gzo",
      defaults: {
        prefix: "gzo",
        source: "GZO",
        listing: "GZO",
        tag: "gzo",
        file: RESOURCE_FILES.gzo,
        optional: true
      }
    },
    {
      key: "custom",
      defaults: {
        prefix: "custom",
        source: "Custom Static",
        listing: "Custom Static",
        tag: "custom",
        file: RESOURCE_FILES.custom
      }
    }
  ];

  const counts = {};
  const normalized = [];
  for (const source of sources) {
    let json = null;
    if (source.key === "gzo" && options.gzoCachePath) {
      json = await readJsonFileOptional(options.gzoCachePath, warnings, "cached GZO catalog", { optional: true });
    }
    if (!json) {
      json = await readJsonOptional(resourceDir, source.defaults.file, warnings, { optional: Boolean(source.defaults.optional) });
    }
    const entries = entriesFromJson(json);
    counts[source.key] = entries.length;
    for (const entry of entries) {
      const row = normalizeCodeEntry(entry, source.defaults);
      if (row) normalized.push(row);
    }
  }

  const entries = mergeBySerial(normalized);
  return {
    ok: true,
    entries,
    counts: {
      ...counts,
      merged: entries.length
    },
    filters: filterValues(entries),
    warnings
  };
}

async function refreshGzoCatalog(resourceDir = DEFAULT_RESOURCE_DIR, gzoCachePath, options = {}) {
  if (!gzoCachePath) throw new Error("No writable GZO cache path was provided.");
  const fetchImpl = options.fetch || globalThis.fetch;
  if (typeof fetchImpl !== "function") throw new Error("This Electron runtime does not provide fetch.");
  const response = await fetchImpl(GZO_CATALOG_URL, {
    headers: {
      "User-Agent": "MattsBoostingToolsElectron/1.0",
      Accept: "application/json,text/plain,*/*"
    },
    cache: "no-store"
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`GZO refresh failed: HTTP ${response.status}`);
  const entries = parseGzoCatalogText(body);
  if (!entries.length) throw new Error("GZO refresh returned no valid BL4 serials.");
  const payload = {
    version: GZO_CACHE_VERSION,
    updated: Math.floor(Date.now() / 1000),
    source: GZO_CATALOG_URL,
    entries
  };
  await fs.mkdir(path.dirname(gzoCachePath), { recursive: true });
  await fs.writeFile(gzoCachePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  const catalog = await loadBl4Catalog(resourceDir, { gzoCachePath });
  return {
    ...catalog,
    refreshed: entries.length,
    cachePath: gzoCachePath,
    source: GZO_CATALOG_URL
  };
}

module.exports = {
  loadBl4Catalog,
  normalizeCodeEntry,
  refreshGzoCatalog,
  validSerial
};
