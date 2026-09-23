"use strict";

/**
 * GZO Codes.html search + submit mapping (live save-editor.be, fetched 2026-09-21).
 * Keep filter keys / submit POST fields aligned with GZO; card autofill is MSBT-only.
 */
(function attachGzoCodesForm(root, factory) {
  const contract = typeof module === "object" && module.exports ? require("./gzo_dlc_contract") : root.MsbtGzoDlcContract;
  const api = factory(contract);
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.MsbtGzoCodesForm = api;
})(typeof window !== "undefined" ? window : globalThis, function createGzoCodesForm(contract) {
  const GZO_MANUFACTURER_TYPES = {
    Atlas: ["Enhancement"],
    CoV: ["Enhancement"],
    Daedalus: ["Assault Rifle", "Pistol", "Shotgun", "SMG", "Repkit", "Grenade", "Shield", "Enhancement"],
    Hyperion: ["Enhancement"],
    Jakobs: ["Assault Rifle", "Pistol", "Shotgun", "Sniper", "Repkit", "Grenade", "Shield", "Enhancement"],
    Maliwan: ["Shotgun", "SMG", "Sniper", "Heavy Weapon", "Repkit", "Grenade", "Shield", "Enhancement"],
    Order: ["Assault Rifle", "Pistol", "Sniper", "Repkit", "Grenade", "Shield", "Enhancement"],
    Ripper: ["Shotgun", "SMG", "Sniper", "Heavy Weapon", "Repkit", "Grenade", "Shield", "Enhancement"],
    Tediore: ["Assault Rifle", "Pistol", "Shotgun", "Repkit", "Grenade", "Shield", "Enhancement"],
    Torgue: ["Assault Rifle", "Pistol", "Shotgun", "Heavy Weapon", "Repkit", "Grenade", "Shield", "Enhancement"],
    Vladof: ["Assault Rifle", "SMG", "Sniper", "Heavy Weapon", "Repkit", "Grenade", "Shield", "Enhancement"],
    Classmod: ["Siren", "Exo Soldier", "Gravitar", "Paladin", "C4SH", "Loveless"],
    Unknown: ["AI"]
  };

  const GZO_SEARCH_MANUFACTURERS = [
    "Atlas", "CoV", "Daedalus", "Hyperion", "Jakobs", "Maliwan",
    "Order", "Ripper", "Tediore", "Torgue", "Vladof"
  ];

  const GZO_SEARCH_TYPE_OPTIONS = [
    "Assault Rifle", "Pistol", "Shotgun", "SMG", "Sniper", "Heavy Weapon",
    "Repkit", "Grenade", "Shield", "Enhancement", "Classmod",
    "Amon", "Harlowe", "Vex", "Rafa", "C4SH", "Loveless"
  ];

  const GZO_SEARCH_RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Pearlescent"];
  const GZO_SUBMIT_RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Pearl"];

  const GZO_DLC_OPTIONS = [
    "Base Game", "Stone Demon", "Vault of the Damned", "Bounty Pack 2", "Bounty Pack 3",
    "Bounty Pack 4", "Gilded Glory", "Story Pack 1", "Harmonica", "Non-obtainable", "Mixed DLC"
  ];

  const GZO_DLC_SEARCH_OPTIONS = [
    { value: "Base Game", label: "Base Game" },
    { value: "__any_dlc__", label: "Any DLC" },
    { value: "Stone Demon", label: "Stone Demon" },
    { value: "Vault of the Damned", label: "Vault of the Damned" },
    { value: "Bounty Pack 2", label: "Bounty Pack 2" },
    { value: "Bounty Pack 3", label: "Bounty Pack 3" },
    { value: "Bounty Pack 4", label: "Bounty Pack 4" },
    { value: "Gilded Glory", label: "Gilded Glory" },
    { value: "Story Pack 1", label: "Story Pack 1" },
    { value: "Harmonica", label: "Harmonica" },
    { value: "Non-obtainable", label: "Non-obtainable" },
    { value: "Mixed DLC", label: "Mixed DLC" }
  ];

  const CLASSMOD_ITEM_TYPES = ["paladin", "gravitar", "siren", "c4sh", "exo soldier", "loveless"];
  const CLASSMOD_FILTER_TO_TYPE = {
    amon: "paladin",
    harlowe: "gravitar",
    vex: "siren",
    rafa: "exo soldier",
    c4sh: "c4sh",
    loveless: "loveless"
  };
  const CLASSMOD_TYPE_SEARCH_ALIASES = {
    paladin: ["amon", "paladin"],
    gravitar: ["harlowe", "gravitar"],
    siren: ["vex", "siren"],
    c4sh: ["cash", "c4sh", "robo dealer"],
    "exo soldier": ["rafa", "exo soldier"],
    loveless: ["loveless", "hacker", "corpo hacker"]
  };
  const SEARCH_QUERY_ALIASES = {
    amon: ["paladin"],
    paladin: ["amon"],
    harlowe: ["gravitar"],
    gravitar: ["harlowe"],
    vex: ["siren"],
    siren: ["vex"],
    raffa: ["rafa", "exo soldier"],
    raffe: ["rafa", "exo soldier"],
    rafa: ["exo soldier"],
    cash: ["c4sh"],
    c4sh: ["cash"],
    "robo dealer": ["c4sh", "cash"],
    loveless: ["hacker", "corpo hacker"],
    hacker: ["loveless"]
  };
  const CLASS_DISPLAY = {
    paladin: "Paladin",
    gravitar: "Gravitar",
    siren: "Siren",
    "exo soldier": "Exo Soldier",
    c4sh: "C4SH",
    loveless: "Loveless"
  };
  const CARD_TYPE_TO_GZO = {
    "sniper rifle": "Sniper",
    sniper: "Sniper",
    "heavy gun ordnance": "Heavy Weapon",
    "heavy weapon": "Heavy Weapon",
    ordnance: "Grenade",
    grenade: "Grenade",
    "class mods": "Classmod",
    "class mod": "Classmod",
    classmod: "Classmod",
    classmods: "Classmod"
  };
  const TYPE_ALIASES = {
    sniper: ["sniper", "sniper rifle"],
    "sniper rifle": ["sniper", "sniper rifle"],
    grenade: ["grenade", "ordnance"],
    ordnance: ["grenade", "ordnance"],
    "heavy weapon": ["heavy weapon", "heavy gun ordnance"],
    "heavy gun ordnance": ["heavy weapon", "heavy gun ordnance"],
    classmod: ["classmod", "class mod", "class mods"],
    "class mod": ["classmod", "class mod", "class mods"],
    "class mods": ["classmod", "class mod", "class mods"]
  };

  const GZO_UNSUPPORTED_FIELDS = [
    "website (Lootlemon trusted-partner instant publish)",
    "owner-edit / 24-hour edit-link panel after submit (edit URL still shown if API returns it)",
    "TackleBox Discord auto-prompt",
    "developer pending / edit-requests / leaderboard / owner comments",
    "remote nicnl deserializer (MSBT uses local serialToolsConvert)"
  ];

  function text(value) {
    return String(value == null ? "" : value).trim();
  }

  function compact(value) {
    return text(value).toLowerCase().replace(/[^a-z0-9]+/g, "");
  }

  function unique(values) {
    const seen = new Set();
    const out = [];
    for (const value of values || []) {
      const label = text(value);
      if (!label) continue;
      const key = label.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(label);
    }
    return out;
  }

  const MANUFACTURER_LOOKUP = {};
  GZO_SEARCH_MANUFACTURERS.forEach((name) => {
    MANUFACTURER_LOOKUP[compact(name)] = name;
  });
  MANUFACTURER_LOOKUP.cov = "CoV";
  MANUFACTURER_LOOKUP.classmod = "Classmod";
  MANUFACTURER_LOOKUP.classmods = "Classmod";
  MANUFACTURER_LOOKUP.unknown = "Unknown";

  function knownManufacturer(value) {
    return MANUFACTURER_LOOKUP[compact(value)] || "";
  }

  function isClassmodCatalogItem(item) {
    const itemType = text(item && item.type).toLowerCase();
    const itemCategory = text(item && item.category).toLowerCase();
    const character = text(item && item.character_class).toLowerCase();
    return (
      itemCategory === "classmod" ||
      itemCategory === "class mod" ||
      itemCategory === "class mods" ||
      itemType === "class mod" ||
      itemType === "classmod" ||
      itemType === "class mods" ||
      CLASSMOD_ITEM_TYPES.includes(itemType) ||
      CLASSMOD_ITEM_TYPES.includes(character)
    );
  }

  function classmodSearchAliases(item) {
    if (!isClassmodCatalogItem(item)) return "";
    const itemType = text(item && item.type).toLowerCase();
    const character = text(item && item.character_class).toLowerCase();
    const aliases = CLASSMOD_TYPE_SEARCH_ALIASES[itemType]
      || CLASSMOD_TYPE_SEARCH_ALIASES[character]
      || [];
    return aliases.join(" ");
  }

  function rowManufacturer(row) {
    const fromMfr = knownManufacturer(row && row.manufacturer);
    if (fromMfr) return fromMfr;
    const fromCat = knownManufacturer(row && row.category);
    if (fromCat) return fromCat;
    return "";
  }

  function rowDlcPacks(row) {
    const params = row && row.catalog_parameters && typeof row.catalog_parameters === "object"
      ? row.catalog_parameters
      : {};
    const raw = [
      row && row.dlc,
      params.dlc,
      params.content,
      row && row.content
    ];
    const packs = [];
    raw.forEach((value) => {
      if (Array.isArray(value)) packs.push(...value.map(text).filter(Boolean));
      else if (text(value)) packs.push(text(value));
    });
    return unique(packs);
  }

  function rowDlcLabel(row) {
    const packs = rowDlcPacks(row);
    if (packs.length > 1) return "Mixed DLC";
    return packs[0] || "";
  }

  function matchesItemTypeFilter(item, wantedRaw) {
    const wanted = text(wantedRaw).toLowerCase();
    if (!wanted || wanted === "all") return true;
    const itemType = text(item && item.type).toLowerCase();
    if (wanted === "class mod" || wanted === "classmod" || wanted === "class mods") {
      return isClassmodCatalogItem(item);
    }
    const mappedClassmodType = CLASSMOD_FILTER_TO_TYPE[wanted];
    if (mappedClassmodType) {
      const character = text(item && item.character_class).toLowerCase();
      return itemType === mappedClassmodType || character === mappedClassmodType;
    }
    const aliases = TYPE_ALIASES[wanted] || [wanted];
    return aliases.includes(itemType);
  }

  function matchesRarityFilter(item, wantedRaw) {
    const wanted = text(wantedRaw).toLowerCase();
    if (!wanted || wanted === "all") return true;
    const rarity = text(item && item.rarity).toLowerCase();
    if (!rarity) return false;
    if (wanted === "pearlescent" || wanted === "pearl") {
      return rarity === "pearlescent" || rarity === "pearl";
    }
    return rarity === wanted;
  }

  function matchesManufacturerFilter(item, wantedRaw) {
    const wanted = text(wantedRaw);
    if (!wanted || wanted === "All") return true;
    const category = text(item && item.category);
    const manufacturer = rowManufacturer(item);
    return category === wanted || manufacturer === wanted || knownManufacturer(category) === wanted;
  }

  function matchesDlcFilter(item, wantedRaw) {
    const wanted = text(wantedRaw);
    if (!wanted || wanted === "All") return true;
    const packs = rowDlcPacks(item);
    const label = rowDlcLabel(item);
    if (wanted === "__any_dlc__") return Boolean(label) && label !== "Base Game";
    if (wanted === "Base Game") return !label || label === "Base Game";
    if (wanted === "Mixed DLC") return label === "Mixed DLC" || packs.length > 1;
    const aliases = wanted === "Stone Demon" || wanted === "Bounty Pack 2"
      ? ["Stone Demon", "Bounty Pack 2"]
      : [wanted];
    return aliases.some((name) => packs.includes(name) || label === name);
  }

  function expandTokenTerms(token) {
    const terms = new Set();
    const raw = text(token).toLowerCase();
    if (!raw) return terms;
    terms.add(raw);
    const compactToken = compact(raw);
    if (compactToken) terms.add(compactToken);
    Object.keys(SEARCH_QUERY_ALIASES).forEach((key) => {
      const compactKey = compact(key);
      if (raw === key || raw.includes(key) || (compactKey && compactToken === compactKey)) {
        terms.add(key);
        SEARCH_QUERY_ALIASES[key].forEach((alias) => {
          terms.add(alias);
          const compactAlias = compact(alias);
          if (compactAlias) terms.add(compactAlias);
        });
      }
    });
    return terms;
  }

  function extraSearchValues(row) {
    return [
      row && row.listing,
      row && row.source,
      row && row.classification,
      row && row.serial,
      row && row.notes,
      row && row.item_level,
      row && row.mattmab_validator,
      row && row.url,
      Array.isArray(row && row.tags) ? row.tags.join(" ") : ""
    ];
  }

  function rowSearchBlob(row) {
    return [
      row && row.name,
      row && row.category,
      row && row.type,
      row && row.creator,
      row && row.rarity,
      rowManufacturer(row),
      rowDlcLabel(row),
      classmodSearchAliases(row),
      ...extraSearchValues(row)
    ].map(text).filter(Boolean).join(" ").toLowerCase();
  }

  function matchesSearchQuery(row, query) {
    const raw = text(query).toLowerCase();
    if (!raw) return true;
    const blob = rowSearchBlob(row);
    const compactBlob = compact(blob);
    const tokens = raw.split(/\s+/).filter(Boolean);
    return tokens.every((token) => {
      const terms = expandTokenTerms(token);
      for (const term of terms) {
        if (!term) continue;
        if (blob.includes(term)) return true;
        const compactTerm = compact(term);
        if (compactTerm && compactBlob.includes(compactTerm)) return true;
      }
      return false;
    });
  }

  function mergeFilterLabels(canonical, extra) {
    return unique([...(canonical || []), ...(extra || [])]);
  }

  function mergeTypeFilters() {
    return GZO_SEARCH_TYPE_OPTIONS.slice();
  }

  function mergeManufacturerFilters() {
    return GZO_SEARCH_MANUFACTURERS.slice();
  }

  function mergeRarityFilters() {
    return GZO_SEARCH_RARITIES.slice();
  }

  function mergeDlcFilters() {
    return GZO_DLC_SEARCH_OPTIONS.slice();
  }

  function typesForManufacturer(manufacturer) {
    const key = text(manufacturer);
    if (!key) return [];
    if (GZO_MANUFACTURER_TYPES[key]) return GZO_MANUFACTURER_TYPES[key].slice();
    const mapped = knownManufacturer(key);
    return mapped && GZO_MANUFACTURER_TYPES[mapped] ? GZO_MANUFACTURER_TYPES[mapped].slice() : [];
  }

  function manufacturerKeys() {
    return Object.keys(GZO_MANUFACTURER_TYPES).sort((a, b) => a.localeCompare(b));
  }

  const CATALOG_PAGE_SIZE = 25;

  function matchesListingSection(item, sectionRaw) {
    const section = text(sectionRaw).toLowerCase() || "legit";
    const listing = text(item && item.listing).toLowerCase();
    const classification = text(item && item.classification).toLowerCase();
    if (section === "modded") return listing === "modded" || classification === "modded";
    return listing !== "modded" && classification !== "modded";
  }

  function listingCounts(items) {
    const list = Array.isArray(items) ? items : [];
    return {
      legit: list.filter((row) => matchesListingSection(row, "Legit")).length,
      modded: list.filter((row) => matchesListingSection(row, "Modded")).length
    };
  }

  function voteCount(item) {
    const params = item && item.catalog_parameters && typeof item.catalog_parameters === "object"
      ? item.catalog_parameters
      : {};
    const raw = item && item.votes != null ? item.votes : params.votes;
    return Number(raw) || 0;
  }

  function sortItemsByVotes(items) {
    return (items || []).slice().sort((a, b) => {
      const diff = voteCount(b) - voteCount(a);
      if (diff) return diff;
      return text(a && a.name).localeCompare(text(b && b.name));
    });
  }

  function catalogPageSlice(sortedItems, pageRaw, pageSize) {
    const size = Number(pageSize) > 0 ? Number(pageSize) : CATALOG_PAGE_SIZE;
    const total = (sortedItems || []).length;
    const totalPages = Math.max(1, Math.ceil(total / size) || 1);
    let page = Number(pageRaw) || 1;
    if (page > totalPages) page = totalPages;
    if (page < 1) page = 1;
    const start = (page - 1) * size;
    return {
      pageItems: (sortedItems || []).slice(start, start + size),
      total,
      totalPages,
      page,
      start
    };
  }

  function rarityForSubmit(raw) {
    const value = text(raw);
    const key = value.toLowerCase();
    if (key === "pearlescent" || key === "pearl") return "Pearl";
    if (!value) return "";
    return value;
  }

  function canonicalClassType(raw) {
    const key = text(raw).toLowerCase();
    if (CLASS_DISPLAY[key]) return CLASS_DISPLAY[key];
    const mapped = CLASSMOD_FILTER_TO_TYPE[key];
    if (mapped && CLASS_DISPLAY[mapped]) return CLASS_DISPLAY[mapped];
    return "";
  }

  function gzoTypeFromCard(card) {
    if (!card || typeof card !== "object") return "";
    const itemType = text(card.item_type || card.type);
    const character = text(card.character_class);
    const classType = canonicalClassType(itemType) || canonicalClassType(character);
    if (classType) return classType;
    const mapped = CARD_TYPE_TO_GZO[itemType.toLowerCase()];
    if (mapped === "Classmod") return classType || canonicalClassType(character);
    return mapped || itemType;
  }

  function gzoCategoryFromCard(card) {
    if (!card || typeof card !== "object") return "";
    const itemType = text(card.item_type || card.type);
    const character = text(card.character_class);
    if (itemType.toLowerCase() === "ai" || character.toLowerCase() === "ai") return "Unknown";
    if (itemType.toLowerCase() === "classmod" || canonicalClassType(itemType) || canonicalClassType(character)) {
      return "Classmod";
    }
    return knownManufacturer(card.manufacturer) || text(card.manufacturer);
  }

  function notesFromCard(card) {
    if (!card || typeof card !== "object") return "";
    const lines = [];
    const listedEffects = new Set();
    const partEffects = Array.isArray(card.part_effects) ? card.part_effects : [];
    if (partEffects.length) {
      partEffects.forEach((row) => {
        const name = text(row && row.name);
        if (!name) return;
        const known = (Array.isArray(row.effects) ? row.effects : []).map(text).filter(Boolean);
        known.forEach((effect) => listedEffects.add(effect.toLowerCase()));
        lines.push(known.length ? `{${row.index || lines.length + 1}} - ${name} — ${known.join("; ")}` : `{${row.index || lines.length + 1}} - ${name}`);
      });
    } else {
      const parts = Array.isArray(card.part_names) ? card.part_names : [];
      parts.forEach((name, index) => {
        const label = text(name);
        if (label) lines.push(`{${index + 1}} - ${label}`);
      });
    }
    const red = Array.isArray(card.red_text) ? card.red_text.map(text).filter(Boolean) : [];
    red.forEach((line) => {
      if (!listedEffects.has(line.toLowerCase())) lines.push(`Red text: ${line}`);
    });
    const descs = Array.isArray(card.description_lines) ? card.description_lines.map(text).filter(Boolean) : [];
    descs.forEach((line) => {
      if (!listedEffects.has(line.toLowerCase())) lines.push(`Effect: ${line}`);
    });
    return lines.join("\n");
  }

  function submitFieldsFromCard(card, extras = {}) {
    const category = gzoCategoryFromCard(card);
    const type = gzoTypeFromCard(card);
    const types = typesForManufacturer(category);
    return {
      name: text(card && (card.display_name || card.name)),
      category,
      type,
      rarity: rarityForSubmit(card && card.rarity),
      manufacturer: rowManufacturer({ manufacturer: card && card.manufacturer, category }),
      notes: notesFromCard(card),
      dlc: text(extras.dlc) || (extras.deserialized ? detectDlc(extras.deserialized).dlc : ""),
      customType: Boolean(type && types.length && !types.includes(type))
    };
  }

  // Interpret serial part identifiers, never item-name guesses. GZO's labels
  // are a website contract; they are distinct from game stat/asset provenance.
  function detectDlc(human) {
    const raw = text(human);
    const family = raw.match(/^\s*#?\s*(\d+)\s*,/);
    const keys = new Set();
    for (const match of raw.matchAll(/\{\s*(\d+)\s*(?::\s*(\d+|\[[\d\s,]+\]))?\s*\}/g)) {
      const type = match[2] ? match[1] : family && family[1];
      if (!type) continue;
      const parts = match[2] ? match[2].match(/\d+/g) : [match[1]];
      for (const part of parts || []) keys.add(`${Number(type)}:${Number(part)}`);
    }
    const packs = unique([...keys].map(key => contract && contract.parts[key]).filter(Boolean));
    return {dlc: packs.length > 1 ? "Mixed DLC" : packs[0] || "Base Game", packs, keys: [...keys], isDlc: packs.length > 0};
  }

  function applySubmitFields(target, fields, options = {}) {
    const next = target && typeof target === "object" ? target : {};
    const overwrite = Boolean(options.overwrite);
    const mapping = {
      name: fields && fields.name,
      category: fields && fields.category,
      type: fields && fields.type,
      rarity: fields && fields.rarity,
      notes: fields && fields.notes,
      dlc: fields && fields.dlc
    };
    Object.entries(mapping).forEach(([key, value]) => {
      if (!text(value)) return;
      if (!overwrite && text(next[key])) return;
      next[key] = value;
    });
    return next;
  }

  return {
    GZO_MANUFACTURER_TYPES,
    GZO_SEARCH_MANUFACTURERS,
    GZO_SEARCH_TYPE_OPTIONS,
    GZO_SEARCH_RARITIES,
    GZO_SUBMIT_RARITIES,
    GZO_DLC_OPTIONS,
    GZO_DLC_SEARCH_OPTIONS,
    GZO_UNSUPPORTED_FIELDS,
    CATALOG_PAGE_SIZE,
    GZO_BROWSE_MANUFACTURERS: GZO_SEARCH_MANUFACTURERS,
    GZO_SUBMIT_MANUFACTURERS: Object.keys(GZO_MANUFACTURER_TYPES),
    GZO_BROWSE_DLC: GZO_DLC_SEARCH_OPTIONS,
    GZO_SUBMIT_DLC: GZO_DLC_OPTIONS,
    GZO_BROWSE_RARITIES: GZO_SEARCH_RARITIES,
    GZO_MFG_TO_TYPES: GZO_MANUFACTURER_TYPES,
    compact,
    unique,
    knownManufacturer,
    isClassmodCatalogItem,
    classmodSearchAliases,
    rowManufacturer,
    rowDlcPacks,
    rowDlcLabel,
    matchesItemTypeFilter,
    matchesRarityFilter,
    matchesManufacturerFilter,
    matchesDlcFilter,
    itemMatchesDlcFilter: matchesDlcFilter,
    expandTokenTerms,
    rowSearchBlob,
    matchesSearchQuery,
    mergeTypeFilters,
    mergeManufacturerFilters,
    mergeRarityFilters,
    mergeDlcFilters,
    typesForManufacturer,
    manufacturerKeys,
    matchesListingSection,
    listingCounts,
    voteCount,
    sortItemsByVotes,
    catalogPageSlice,
    rarityForSubmit,
    gzoTypeFromCard,
    gzoCategoryFromCard,
    notesFromCard,
    detectDlc,
    submitFieldsFromCard,
    cardToSubmitFields: submitFieldsFromCard,
    applySubmitFields
  };
});
