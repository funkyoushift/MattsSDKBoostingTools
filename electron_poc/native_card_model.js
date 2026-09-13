"use strict";
(function(root) {
  const art = "coui://uiresources/_shared/assets/";
  const icons = {damage:"wpn_dmg",accuracy:"wpn_prmry_accuracy",reload:"wpn_prmry_reload_time",fire_rate:"wpn_prmry_fire_rate",magazine:"wpn_prmry_mag_size",crit:"wpn_scndry_crit_hit_dmg",damage_radius:"wpn_scndry_dmg_radius",shot_cost:"wpn_scndry_ammo_per_shot"};
  const types = {"Assault Rifle":"weap_assault",Pistol:"weap_pistol",Shotgun:"weap_shotgun",SMG:"weap_smg",Sniper:"weap_sniper","Heavy Gun Ordnance":"heavy_weapon_torgue_rocket_launcher","Heavy Weapon":"heavy_weapon_torgue_rocket_launcher",Shield:"energy_shield",Enhancement:"enhancement",Repkit:"rep_kit",Ordnance:"grenade_tediore"};
  const elements = {Shock:"electric",Fire:"fire",Cryo:"cryo",Corrosive:"corrosive",Radiation:"radiation"};
  const number = value => Number.isFinite(value) ? Number(value).toLocaleString("en-US",{maximumFractionDigits:1}) : "—";
  function compact(value) {
    if (!Number.isFinite(value)) return "—";
    if (Math.abs(value)>=1e7) return number(Math.round(value/1e6))+"M";
    if (Math.abs(value)>=1e4) return number(Math.round(value/1e3))+"k";
    return number(value);
  }
  function toNativeCardModel(entry) {
    const rarity = {Pearlescent:"pearl",Legendary:"legendary",Epic:"epic",Rare:"rare",Uncommon:"uncommon",Common:"common"}[entry.rarity] || "common";
    const primary = ["damage","accuracy","reload","fire_rate","magazine"].filter(key=>Number.isFinite(entry[key])).map(key=>({
      ident:key,image:art+`ico_ui_art_item_stats/ico_ui_art_${icons[key]}.png`,comparison:"",
      value: key === "damage" ? compact(entry.damage)+(entry.projectile_count>1 ? " x "+number(entry.projectile_count) : "")
        : key === "accuracy" ? number(entry.accuracy)+"%" : key === "reload" ? number(entry.reload)+"s"
        : key === "fire_rate" ? number(entry.fire_rate)+"/s" : compact(entry.magazine)
    }));
    const tertiary = ["crit","damage_radius","shot_cost"].filter(key=>Number.isFinite(entry[key]) && entry[key] > (key === "shot_cost" ? 1 : 0)).map(key=>({
      image:art+`ico_ui_art_item_stats/ico_ui_art_${icons[key]}.png`,comparison:"",
      value:key === "crit" ? "+"+number(entry[key])+"%" : number(entry[key])+(key === "damage_radius" ? "cm" : "/Shot")
    }));
    const red = Array.isArray(entry.red_text) ? entry.red_text : [];
    const descriptions = [...new Set((entry.description_lines || entry.perk_lines || []).filter(line=>line && !red.includes(line)))];
    const secondary = entry.native_secondary || descriptions.map(value=>({image:art+"ico_ui_art_discovery/ico_misc_legendaries.png",value,comparison:""}));
    const element = elements[entry.element || entry.damage_type] || "";
    const model = {
      abbreviated:false,bannertype:"",bannertext:"",itemtype:"weapon",itembasetype:"weapon",
      rarityident:rarity,manufacturer:String(entry.manufacturer || "").toLowerCase(),showlevel:entry.level!=null,
      leveltoolow:false,level:entry.level == null ? "" : "Lvl "+entry.level,
      thumbnailicon:types[entry.item_type] ? art+`ico_ui_art_item_card_type/ico_art_item_card_${types[entry.item_type]}.png` : "",
      name:String(entry.display_name || entry.card_name || entry.name || "Item"),showrarity:true,whiteheader:entry.item_type || "",
      headline:{value:compact(entry.dps),loc_text:"DPS",comparison:""},hasheadline:Number.isFinite(entry.dps),
      horizontalsplit:false,cardisflipped:false,primaryactive:!!primary.length,tertiaryactive:!!tertiary.length,
      secondaryactive:!!secondary.length,textstatsactive:false,firmwarevisible:false,legendarystatvisible:false,
      mousepositioned:false,compare:false,comparemode:false,showglyphs:false,glyphs:[],
      redtext:red.join("\n"),showprice:Number.isFinite(entry.value),price:number(entry.value),
      showelement1:!!element,showelement2:false,damagetype1:element,damagetype2:"",
      elementtext:entry.element_text || "",secondelementtext:"",elementswapdelay:4,itemcardshowdelay:0,
      text_stat_entries:[],primary_stat_entries:primary,tertiary_stat_entries:tertiary,secondary_stat_entries:secondary
    };
    const itemType = {Shield:"shield",Ordnance:"gadget",Repkit:"repair_kit",Enhancement:"enhancement",Classmod:"classmod","Class Mod":"classmod"}[entry.item_type];
    if (itemType) {
      model.itemtype = itemType;model.itembasetype = itemType;
      model.hasheadline = false;model.headline = {value:"",loc_text:"",comparison:""};
      model.primary_stat_entries=[];model.tertiary_stat_entries=[];
      model.primaryactive=false;model.tertiaryactive=false;
      const equipment=entry.native_equipment;
      if(equipment) {
        const groups=equipment.groups || {};
        model.whiteheader=equipment.type_label;
        model.thumbnailicon=equipment.thumbnail || model.thumbnailicon;
        model.primary_stat_entries=groups.primary || [];
        model.secondary_stat_entries=groups.secondary || [];
        model.tertiary_stat_entries=groups.tertiary || [];
        model.text_stat_entries=(groups.text || []).map(row=>({...row,loc_text:row.value}));
        model.primaryactive=!!model.primary_stat_entries.length;
        model.secondaryactive=!!model.secondary_stat_entries.length;
        model.tertiaryactive=!!model.tertiary_stat_entries.length;
        model.textstatsactive=!!model.text_stat_entries.length;
        model.elementtext=(groups.element || []).map(row=>row.value).join(" | ");
        if(itemType === "classmod")model.extendedpassives=model.primary_stat_entries.length>3;
        if(groups.headline?.length) {model.headline=groups.headline[0];model.hasheadline=true;}
        // Keep the resolver's selected red text until native mixed-part selection
        // is proven; do not concatenate several mutually exclusive red lines.
        model.redtext=red[0] || groups.redtext?.[0]?.value || "";
      }
    }
    return model;
  }
  if (typeof module !== "undefined" && module.exports) module.exports = {toNativeCardModel,compact};
  else root.MSBTNativeCard = {toNativeCardModel,compact};
})(typeof window !== "undefined" ? window : globalThis);
