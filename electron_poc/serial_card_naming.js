"use strict";

// These are the game's naming instructions, distinct from the display-only
// Weapon_StatPrefix_Table. Loading a table is not evidence that we can reproduce
// the native OakWeaponNamingStrategy's assembled attribute inputs.
function loadNamingStrategies(payloads) {
  const strategies = new Map();
  for (const payload of payloads || []) {
    for (const record of payload?.inv_name_strategy?.records || []) {
      for (const entry of record.entries || []) {
        for (const [key, value] of Object.entries(entry || {})) {
          if (key.startsWith("__") || !value?.namingstrategy) continue;
          // DLC files can contain reference-only rows. They must not erase the
          // concrete strategy from the base game.
          strategies.set(key.toLowerCase(), value.namingstrategy);
        }
      }
    }
  }
  return strategies;
}

function buildRootNamingIndex(payloads) {
  const roots = new Map();
  for (const payload of payloads || []) {
    for (const record of payload?.inv?.records || []) {
      for (const entry of record.entries || []) {
        for (const [key, value] of Object.entries(entry || {})) {
          if (key.startsWith("__") || !value?.namingstrategydef) continue;
          const ref = String(value.namingstrategydef).match(/inv_name_strategy'([^']+)'/i);
          if (ref) roots.set(key.toLowerCase(), ref[1].toLowerCase());
        }
      }
    }
  }
  return roots;
}

function weaponNamingStatus(root, rootIndex, strategies) {
  const strategyId = rootIndex.get(String(root || "").toLowerCase()) || "";
  const strategy = strategies.get(strategyId);
  return {
    status: "partial",
    strategy: strategyId,
    reason: strategy
      ? "assembled_naming_attributes_unresolved"
      : "missing_naming_strategy",
    // Preserve the actual thresholds and priorities for diagnostics. Neither
    // counting tags nor comparing displayed damage to a guessed baseline is an
    // implementation of this native strategy.
    required_attributes: (strategy?.namingattributethresholds || [])
      .filter((row) => row.firstthreshold != null)
      .map((row) => ({
        name: row.attributename,
        first_threshold: Number(row.firstthreshold),
        second_threshold: row.secondthreshold == null ? null : Number(row.secondthreshold)
      }))
  };
}

function evaluateWeaponNaming(strategy, factors) {
  if (!strategy || !factors) return null;
  const thresholds = new Map((strategy.namingattributethresholds || []).map(row => [row.attributename,row]));
  const qualifies = (name, second = false) => {
    const row = thresholds.get(name), value = factors[name];
    const threshold = Number(second ? row?.secondthreshold : row?.firstthreshold);
    if (!row || !Number.isFinite(value) || !Number.isFinite(threshold)) return false;
    return Number(row.firstthreshold) < 1 ? value <= threshold : value >= threshold;
  };
  const candidates = [];
  for (const [group, second] of [["doublenames",true],["singlenames",false],["combinationnames",false]]) {
    for (const row of strategy[group] || []) {
      if (!qualifies(row.firstattributename,second)) continue;
      if (group === "combinationnames" && !qualifies(row.secondattributename)) continue;
      candidates.push(row);
    }
  }
  candidates.sort((a,b) => Number(b.namepart?.priority || 0)-Number(a.namepart?.priority || 0));
  const name = candidates[0]?.namepart?.partname || "";
  return {prefix:name.replace(/^[^,]*,\s*[0-9A-F]{32},\s*/i,""),factors,source:"native_attribute_thresholds"};
}

module.exports = { loadNamingStrategies, buildRootNamingIndex, weaponNamingStatus, evaluateWeaponNaming };
