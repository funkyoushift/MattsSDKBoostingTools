"use strict";

const assert = require("assert");
const path = require("path");
const { loadResolver } = require("./serial_card_resolve");

function main() {
  const sourceRoot = path.resolve(__dirname, "..");
  const resolver = loadResolver({ sourceRoot });
  assert.ok(resolver.stats.type_ids > 0, "expected gzo type ids");
  assert.ok(resolver.stats.legit_parts > 0, "expected legit_rules parts");
  assert.ok(resolver.stats.perk_parts > 0, "expected ui_stat perk parts");
  assert.ok(resolver.stats.naming_mfgs > 0, "expected weapon naming tables");

  // Lootlemon Zipper human (type 2 = DAD_PS); part 54 = legendary Zipgun, part 1 = barrel zipgun.
  const zipperHuman = "2, 0, 1, 60| 2, 2010|| {54} {2} {4} {3} {5} {1} {62} {63} {13} {25} {42}|";
  const zipper = resolver.resolveFromHuman(zipperHuman);
  assert.strictEqual(zipper.meta_ok, true);
  assert.ok(
    /\bZipper\b/.test(zipper.display_name),
    `expected Zipper in display, got ${zipper.display_name}`
  );
  assert.strictEqual(zipper.unique_name, "Zipper");
  assert.strictEqual(zipper.rarity, "Legendary");
  assert.strictEqual(zipper.manufacturer, "Daedalus");
  assert.strictEqual(zipper.item_type, "Pistol");
  assert.ok(Number.isFinite(zipper.dps) && zipper.dps > 0, `expected Zipper DPS from mined graph, got ${zipper.dps}`);
  assert.ok(Number.isFinite(zipper.damage) && zipper.damage > 0, `expected Zipper damage, got ${zipper.damage}`);
  assert.ok(Number.isFinite(zipper.fire_rate) && zipper.fire_rate > 0, `expected Zipper fire rate, got ${zipper.fire_rate}`);
  assert.ok(Number.isFinite(zipper.reload) && zipper.reload > 0, `expected Zipper reload, got ${zipper.reload}`);
  assert.ok(Number.isFinite(zipper.magazine) && zipper.magazine > 0, `expected Zipper mag, got ${zipper.magazine}`);
  assert.ok(Number.isFinite(zipper.value) && zipper.value > 0, `expected Zipper sell from attr_calc_price*, got ${zipper.value}`);
  assert.ok(Number.isFinite(zipper.accuracy), "accuracy resolves from inherited InventoryStatsContainer weights");
  assert.ok(
    zipper.perk_lines.some((line) => /shot caller|Prison Rules|Critical Damage/i.test(line)),
    `expected Zipper perk/red text, got ${JSON.stringify(zipper.perk_lines)}`
  );

  const silverHuman = "2, 0, 1, 60| 2, 1895|| {84} {2} {3} {4} {83} {60} {62} {68} {14} {26} {30} {31} {42} {76} {77}|";
  const silver = resolver.resolveFromHuman(silverHuman);
  assert.strictEqual(silver.meta_ok, true);
  assert.ok(
    /silver\s*sliver/i.test(silver.display_name),
    `expected Silver Sliver display, got ${silver.display_name}`
  );
  assert.strictEqual(silver.rarity, "Legendary");
  assert.strictEqual(silver.manufacturer, "Daedalus");

  const generic = resolver.resolveFromPartNames(2, ["part_barrel_01", "base_comp_02_uncommon"]);
  assert.strictEqual(generic.meta_ok, true);
  assert.ok(generic.display_name, "generic fallback name");
  assert.ok(!generic.unique_name || generic.display_name === generic.unique_name || generic.display_name.includes("Daedalus") || generic.display_name.includes("S23") || generic.display_name.includes("Bonn"));

  const merged = resolver.mergeCardOntoEntry(
    { display_name: "Daedalus Pistol", rarity: "Unknown", serial: "@Utest", meta_source: "gzo_guess" },
    zipper
  );
  assert.ok(/\bZipper\b/.test(merged.display_name), `merged should keep Zipper lore name, got ${merged.display_name}`);
  assert.strictEqual(merged.rarity, "Legendary");
  assert.ok(Number.isFinite(merged.dps) && merged.dps > 0, `merged should keep mined DPS, got ${merged.dps}`);
  assert.ok(Number.isFinite(merged.value) && merged.value > 0, `merged should keep mined sell, got ${merged.value}`);
  assert.strictEqual(merged.card_resolved, true);

  // Catalog name without unique should keep catalog when resolve has no unique? Zipper has unique.
  const keepCatalog = resolver.mergeCardOntoEntry(
    { name: "Catalog Special", serial: "@Utest2" },
    { ...generic, unique_name: "", licensed_prefix: "", stat_prefix: "", display_name: "Daedalus Pistol", meta_ok: true }
  );
  assert.strictEqual(keepCatalog.name, "Catalog Special");

  // Recorded game target: native assembled modifiers select Extolled.
  // {11:82} supplies the pearl composition, not the title. Roulette's actual
  // naming aspect on its barrel must win over the composition's generated label.
  const rouletteSerial = [
    "@Ugb)KvFnkbUWIxbV7F4K4B`Q&gN>ri}m8e7/YEg$ui+YD@hpLClhuVj_hnk0qhl+=ahl+",
    ">lhYEu#Hq-/72UQBy2NepH2XzPa3N;HA3l$Fa3zZUe%RrNol9G~=l9G~=;9=~47{2H2GCe(>f3M{*{O$fu(P?-7D}C45WjehK"
  ].join("");
  const rouletteHuman = [
    "4, 0, 1, 60| 2, 2002|| {11:82} {2} {6} {4} {4} {4} {4} {4} {4} {4} {4} {4} {5} {3} {84} {55} {54} ",
    "{58} {60} {61} {59} {57} {56} {56} {56} {56} {62} {16} {2:13} {22} {31} {34} {30} {32} {28} {27} ",
    "{39} {41} {40} {48} {47} {68} {299:[9 9 9 9 9 9 9 9 9 9]}| \"c\", \"Cosmetics_Weapon_Shiny_Roulette\"|"
  ].join("");
  assert.ok(rouletteSerial.startsWith("@U"), "expected Matt @U serial");
  const roulette = resolver.resolveFromHuman(rouletteHuman);
  assert.strictEqual(roulette.meta_ok, true);
  assert.strictEqual(
    roulette.display_name,
    "Zealous Extolled Roulette",
    `expected game/NCS title, got ${roulette.display_name} (unique=${roulette.unique_name} licensed=${roulette.licensed_prefix} stat=${roulette.stat_prefix} parts=${JSON.stringify(roulette.part_keys.slice(0, 8))})`
  );
  assert.strictEqual(roulette.unique_name, "Roulette");
  assert.strictEqual(roulette.licensed_prefix, "Zealous");
  assert.strictEqual(roulette.stat_prefix, "Extolled");
  assert.strictEqual(roulette.name_status, "resolved");
  assert.strictEqual(roulette.naming.strategy, "namestrat_ord");
  assert.strictEqual(roulette.manufacturer, "Order");
  assert.strictEqual(roulette.item_type, "Pistol");
  assert.ok(
    !/eigenburst/i.test(roulette.display_name),
    "composition must not replace the actual barrel title"
  );
  assert.ok(
    roulette.part_keys.includes("part_barrel_02_roulette"),
    `expected roulette barrel in parts, got ${JSON.stringify(roulette.part_keys)}`
  );
  assert.ok(
    roulette.part_keys.includes("comp_05_legendary_eigenburst"),
    "typed reference must retain the actual foreign composition"
  );
  assert.strictEqual(roulette.rarity, "Pearlescent");
  // Formula smoke check only: assembled mixed-part values have not been
  // validated against the game. Do not freeze the old filtered-part outputs.
  assert.ok(Number.isFinite(roulette.damage) && roulette.damage > 0);
  assert.ok(Number.isFinite(roulette.fire_rate) && roulette.fire_rate > 0);
  assert.ok(Number.isFinite(roulette.accuracy));

  // Classmod: shared part keys (leg_body_04) must stay root-scoped — Kindread ≠ Cooler.
  const kindreadHuman = "254, 0, 1, 60| 2, 2543|| {53} {13} {258} {279} {321} {213} {182} {216} {150} {234:[6 58]}|";
  const kindread = resolver.resolveFromHuman(kindreadHuman);
  assert.strictEqual(kindread.display_name, "Bonded Kindread Spirits");
  assert.strictEqual(kindread.unique_name, "Kindread Spirits");
  assert.ok(
    /girl and a cat on a broom/i.test((kindread.red_text || []).join(" ")),
    `expected Kindread red text, got ${JSON.stringify(kindread.red_text)}`
  );
  assert.ok(
    !/voodoo/i.test((kindread.red_text || []).join(" ")),
    "must not attach Cooler robodealer red text via shared part keys"
  );

  // Shield / ordnance / enhancement: InventoryNamingAspect prefix+title(+ShieldNameTable / EnhancementNaming*).
  const shieldFull = resolver.resolveFromPartNames(287, [
    "comp_05_legendary_hopscotch",
    "part_body_hopscotch",
    "part_ra_missile_swarm_primary",
    "part_ra_missile_swarm_primary",
    "part_ra_armor_segment_primary"
  ]);
  assert.strictEqual(shieldFull.display_name, "Barrage Barrage Scaled Hopscotch");

  const ordnanceFull = resolver.resolveFromPartNames(267, [
    "comp_05_spinning_blade",
    "part_spinning_blade",
    "part_stat_05_elemental_power",
    "part_stat_07_nuke",
    "part_stat_05_jak_oversized"
  ]);
  assert.strictEqual(ordnanceFull.display_name, "Ancient Atomic Augmented Spinning Blade");

  let enhTypeId = 0;
  for (const [id, row] of resolver.ctx.typeIdIndex.entries()) {
    if (/jak_enhancement/i.test(row.label)) {
      enhTypeId = id;
      break;
    }
  }
  assert.ok(enhTypeId, "jak_enhancement type id");
  const hefty = resolver.resolveFromPartNames(enhTypeId, [
    "part_core_jak_leaper",
    "part_core_jak_piercer",
    "part_core_jak_sequencer",
    "part_stat_weapon_magsize",
    "part_stat_weapon_firerate",
    "part_stat_weapon_accuracy"
  ]);
  assert.strictEqual(hefty.display_name, "Hefty");
  assert.ok(!/^Leaper$/i.test(hefty.display_name));

  // Matt equipped @U goldens (deserialized humans). Cross-set colon tokens + ShieldNameTable /
  // EnhancementNaming / prefixpartlist — keep Roulette + Kindread regressions above green.
  const fs = require("fs");
  const pathMod = require("path");
  const mattRows = JSON.parse(
    fs.readFileSync(pathMod.join(__dirname, "fixtures/item_cards/equipped.json"), "utf8")
  );
  const mattHuman = (slot) => {
    const row = mattRows.find((r) => r.slot === slot);
    assert.ok(row && row.human, `missing matt human for ${slot}`);
    return row.human;
  };

  const mattW1 = resolver.resolveFromHuman(mattHuman("W1"));
  assert.ok(/\bStar Helix\b/i.test(mattW1.display_name), `W1 expected Star Helix, got ${mattW1.display_name}`);
  // Game target remains Synchonized; do not certify a guessed stat prefix.
  assert.strictEqual(mattW1.name_status, "partial");
  assert.strictEqual(mattW1.stat_prefix, "");
  // This @U has legendary comp + generic barrels only (no part_barrel_02_star_helix).
  // Thermal Convection/Heat Sink previously leaked via bare part_barrel_01_b from bor_hw — that was wrong.
  assert.ok(
    !(mattW1.perk_lines || []).some((line) => /Thermal Convection|Wide Disk|Heat Exchange/i.test(line)),
    `W1 must not attach bor_hw bare-key secondaries, got ${JSON.stringify(mattW1.perk_lines)}`
  );
  assert.ok(
    (mattW1.perk_lines || []).some((line) => /Hyperion-Licensed Grip/i.test(line)),
    `W1 expected Hyperion grip from part_grip_04_hyp, got ${JSON.stringify(mattW1.perk_lines)}`
  );

  const mattW2 = resolver.resolveFromHuman(mattHuman("W2"));
  assert.strictEqual(mattW2.display_name, "Zealous Extolled Roulette");

  const mattW3 = resolver.resolveFromHuman(mattHuman("W3"));
  assert.ok(/\bKitty\b/i.test(mattW3.display_name), `W3 expected Kitty, got ${mattW3.display_name}`);
  assert.ok(!/Linebacker/i.test(mattW3.display_name), "W3 must not prefer Linebacker over TOR_PS Kitty barrel");
  assert.strictEqual(mattW3.licensed_prefix, "Debauched");
  assert.strictEqual(mattW3.stat_prefix, "Vibrating");
  assert.strictEqual(mattW3.name_status, "resolved");

  const mattShield = resolver.resolveFromHuman(mattHuman("Shield"));
  assert.strictEqual(mattShield.display_name, "Barrage Barrage Scaled Hopscotch");

  const mattOrd = resolver.resolveFromHuman(mattHuman("Ordnance"));
  assert.strictEqual(mattOrd.display_name, "Ancient Atomic Augmented Spinning Blade");
  assert.ok(/I'll take that/i.test((mattOrd.red_text || []).join(" ")), `ordnance red, got ${JSON.stringify(mattOrd.red_text)}`);

  const mattRep = resolver.resolveFromHuman(mattHuman("Repkit"));
  assert.strictEqual(mattRep.display_name, "Triple Bypass");
  assert.ok(/ride eternal/i.test((mattRep.red_text || []).join(" ")), `repkit shiny red, got ${JSON.stringify(mattRep.red_text)}`);
  assert.ok(!/Nope, not today/i.test((mattRep.red_text || [])[0] || ""), "shiny warpaint red should precede Triple Bypass Nope");

  const mattEnh = resolver.resolveFromHuman(mattHuman("Enhancement"));
  assert.strictEqual(mattEnh.display_name, "Hefty");
  assert.ok(!/Ladykiller|Leaper/i.test(mattEnh.display_name));

  const mattCm = resolver.resolveFromHuman(mattHuman("Classmod"));
  assert.strictEqual(mattCm.display_name, "Bonded Kindread Spirits");

  // W4 unique Conflux + Accelerated licensed stay. Leftover: game Nadir vs mined Anisotropic
  // (body_mod points = reloadspeed×accuracy); nucleus vs self-indulgent when both legendary
  // barrels are present (ui_stat maps nucleus to complex_root, self-indulgent to conflux).
  const mattW4 = resolver.resolveFromHuman(mattHuman("W4"));
  assert.ok(/\bConflux\b/i.test(mattW4.display_name), `W4 expected Conflux, got ${mattW4.display_name}`);
  assert.strictEqual(mattW4.licensed_prefix, "Accelerated");
  assert.ok(!/Eigenburst/i.test(mattW4.display_name));

  // Franken VLA_SM + MAL_SG Mantra list (backpack[759] last Maliwan-slot delivery, 507 chars).
  // Root bugs: SM suffix → SMG; cross-set `{10:[62…]}` must import part_barrel_02_mantra
  // (not treat 10 as on-item shield → Flap/Other).
  const mantraSerial = fs.readFileSync(pathMod.join(__dirname, "fixtures/item_cards/mantra_serial.txt"), "utf8").trim();
  const mantraHuman = fs.readFileSync(pathMod.join(__dirname, "fixtures/item_cards/mantra_human.txt"), "utf8").trim();
  assert.ok(mantraSerial.startsWith("@U") && mantraSerial.length === 507, "Mantra canary @U length");
  assert.ok(/^22,/.test(mantraHuman), "Mantra canary typeId 22 VLA_SM");
  const mantra = resolver.resolveFromHuman(mantraHuman);
  assert.strictEqual(mantra.unique_name, "Mantra");
  assert.strictEqual(mantra.item_type, "SMG");
  assert.strictEqual(mantra.manufacturer, "Vladof");
  assert.strictEqual(mantra.category, "Guns");
  // Recorded game prefix is Wasted, but both borg/tor mags exist in the real
  // serial. Until native selection is implemented, don't invent Affixed.
  assert.strictEqual(mantra.licensed_prefix, "");
  assert.strictEqual(mantra.name_status, "partial");
  assert.ok(/\bMantra\b/.test(mantra.display_name), `expected Mantra display, got ${mantra.display_name}`);
  assert.ok(!/^Flap$/i.test(mantra.display_name), "must not resolve body_flap as unique");
  assert.ok(
    mantra.part_keys.includes("part_barrel_02_mantra"),
    `expected Mantra barrel from MAL_SG list, got ${JSON.stringify(mantra.part_keys.slice(0, 12))}`
  );
  assert.ok(
    (mantra.red_text || []).some((line) => /Punch your way to self-actualization/i.test(line)),
    `expected mined Mantra red text, got ${JSON.stringify(mantra.red_text)}`
  );
  assert.ok(Number.isFinite(mantra.dps) && mantra.dps > 0, `expected SMG DPS after type fix, got ${mantra.dps}`);

  // GUID-suffixed UE column names (FireRate_Value_36_<guid>) must map to mined firerate_value.
  const gmrSparse = resolver.resolveFromHuman("15, 0, 1, 60| 2, 2000|| {1} {2} {3} {4} {5}|");
  assert.ok(/\bG\.?M\.?R\.?\b/i.test(gmrSparse.display_name), `expected G.M.R., got ${gmrSparse.display_name}`);
  assert.ok(Number.isFinite(gmrSparse.damage) && gmrSparse.damage > 0, `GMR damage, got ${gmrSparse.damage}`);
  assert.ok(Number.isFinite(gmrSparse.fire_rate) && gmrSparse.fire_rate > 0, `GMR fire_rate via GUID column map, got ${gmrSparse.fire_rate}`);

  // TED thrown mags only dependencytag licensed_ted — must not invent ORD -Vested.
  // Kickballer-style: borg_mag addtag + TED thrown deps → default×borg_mag = Prosperous.
  const kickballerPath = pathMod.join(__dirname, "fixtures/item_cards/kickballer.json");
  if (fs.existsSync(kickballerPath)) {
    const kickRows = JSON.parse(fs.readFileSync(kickballerPath, "utf8"));
    const kick = kickRows.find((r) => /Kickballer/i.test(String(r.label || r.gzo_name || "")) && r.human)
      || kickRows.find((r) => String(r.human || "").includes("2, 82||") && r.human);
    if (kick && kick.human) {
      const kickCard = resolver.resolveFromHuman(kick.human);
      assert.strictEqual(kickCard.unique_name, "Ichor", "typed MAL_HW Ichor barrel, not the legacy guessed Gmr label");
      assert.notStrictEqual(
        kickCard.licensed_prefix,
        "Vested",
        "TED thrown mag dependencytags must not invent Vested"
      );
      assert.strictEqual(
        kickCard.licensed_prefix,
        "Zealous",
        `typed Jakobs license plus borg magazine, got ${kickCard.licensed_prefix}`
      );
      assert.strictEqual(kickCard.stat_prefix, "Extolled");
      assert.strictEqual(kickCard.name_status, "resolved");
    }
  }

  const meathead = resolver.resolveFromPartNames(390, ["comp_meathead_chaingun"]);
  assert.strictEqual(meathead.item_type, "Heavy Gun Ordnance");
  assert.strictEqual(meathead.category, "Guns");

  const { sanitizePerkPreviewText } = require("./serial_card_resolve");
  assert.strictEqual(sanitizePerkPreviewText("Every {mod}th shot"), "");
  assert.ok(!/\{mod\}/i.test(sanitizePerkPreviewText("Angel's Share - Every {mod}th shot") || ""));
  assert.strictEqual(
    sanitizePerkPreviewText(
      "Stalker - Grants a {mod1} Chance for shots to be a Critical Hit, and refunds {mod2} Ammo on Critical Hit"
    ),
    "Stalker"
  );
  assert.strictEqual(
    sanitizePerkPreviewText(
      "Big Name Hunter - When Zoomed In, Damage increases by {mod1}, Shot Cost increases by {mod2}, and Fire Rate decreases by {mod3}"
    ),
    "Big Name Hunter"
  );

  // Franken ORD_AR with GMR + Rowan barrels: one naming flavor, no bor_hw Wide Disk bare-key bleed,
  // and multi-{mod} unique titles kept (Stalker / Big Name Hunter).
  const frankenRows = JSON.parse(
    fs.readFileSync(pathMod.join(__dirname, "fixtures/item_cards/franken.json"), "utf8")
  );
  const frankenGmrRow = frankenRows.find((r) => r.label === "Gmr" && r.human);
  assert.ok(frankenGmrRow && frankenGmrRow.human, "franken Gmr human");
  const frankenGmr = resolver.resolveFromHuman(frankenGmrRow.human);
  assert.ok(
    !/Wide Disk|Heat Exchange|Compound -/i.test((frankenGmr.description_lines || []).join(" ")),
    `franken must not attach bor_hw bare secondaries, got ${JSON.stringify(frankenGmr.description_lines)}`
  );
  const frankenFlavors = (frankenGmr.red_text || []).filter((line) =>
    /inheritor of grace|dream of darkness/i.test(line)
  );
  assert.ok(
    frankenFlavors.length <= 1,
    `franken red must be naming-unique only, got ${JSON.stringify(frankenGmr.red_text)}`
  );
  assert.ok(
    (frankenGmr.description_lines || []).some((line) => /Stalker|Big Name Hunter/i.test(line)),
    `franken expected Kickballer-table unique titles from barrel ui_stats, got ${JSON.stringify(frankenGmr.description_lines)}`
  );

  console.log("PASS serial_card_resolve Zipper/Silver/Roulette/Kindread/Shield/Ordnance/Hefty/Matt@U offline card components (full gun naming remains unresolved)");
  console.log(JSON.stringify({
    zipper: {
      display_name: zipper.display_name,
      unique_name: zipper.unique_name,
      rarity: zipper.rarity,
      manufacturer: zipper.manufacturer,
      item_type: zipper.item_type,
      element: zipper.element,
      perk_lines: zipper.perk_lines.slice(0, 2)
    },
    silver: {
      display_name: silver.display_name,
      rarity: silver.rarity
    },
    roulette: {
      display_name: roulette.display_name,
      unique_name: roulette.unique_name,
      licensed_prefix: roulette.licensed_prefix,
      stat_prefix: roulette.stat_prefix,
      rarity: roulette.rarity,
      part_keys_head: roulette.part_keys.slice(0, 10)
    },
    kindread: {
      display_name: kindread.display_name,
      unique_name: kindread.unique_name,
      red_text: kindread.red_text.slice(0, 1)
    },
    matt: {
      W1: mattW1.display_name,
      W2: mattW2.display_name,
      W3: mattW3.display_name,
      W4: mattW4.display_name,
      Shield: mattShield.display_name,
      Ordnance: mattOrd.display_name,
      Repkit: { name: mattRep.display_name, red: mattRep.red_text[0] },
      Enhancement: mattEnh.display_name,
      Classmod: mattCm.display_name
    },
    shieldFull: shieldFull.display_name,
    ordnanceFull: ordnanceFull.display_name,
    hefty: hefty.display_name,
    stats: resolver.stats
  }, null, 2));
}

main();
