"use strict";
const assert = require("node:assert/strict");
const {collectItemSources, resolveAspect, resolveStatDefinition, assembleItemDefinitions} = require("./native_item_sources");
const data = {invRoots: new Map([
  ["weapon", {root:{aspects:[{source:"base"}]}, parts:new Map()}],
  ["ord_ar", {root:{basetype:"inv'Weapon'", aspects:[{source:"order"}]},parts:new Map([["grip",{aspects:[{source:"grip"}]}]])}],
  ["foreign", {root:{aspects:[{source:"must-not-import-foreign-host"}]},parts:new Map([["damage",{aspects:[{source:"damage"}]}]])}]
])};
const result = collectItemSources(data, {set:"ORD_AR", partKeys:["damage","grip","damage"],partRoots:["foreign","ord_ar","foreign"]});
assert.deepEqual(result.errors, []);
assert.deepEqual(result.sources.map(s=>s.id), ["weapon","ord_ar","foreign.damage","ord_ar.grip","foreign.damage"]);
const aspects = new Map([
  ["fire",{behavior:{damage:{constant:"100",postscale:"2"},firerate:"4"}}],
  ["ar",{parent:"inv_aspect'fire'",behavior:{damage:{postscale:"3"}}}]
]);
assert.deepEqual(resolveAspect({parent:"inv_aspect'ar'",behavior:{firerate:"7"}},aspects).behavior,
  {damage:{constant:"100",postscale:"3"},firerate:"7"});
assert.throws(()=>resolveAspect({parent:"inv_aspect'missing'"},aspects),/Missing inherited/);
aspects.set("loop",{parent:"inv_aspect'loop'"});
assert.throws(()=>resolveAspect({parent:"inv_aspect'loop'"},aspects),/cycle/);
const stats = new Map([
  ["weapon",{attributes:{attribute:[{damage:{definition:"attribute'weapon_damage'",stat:"damage",stattoattributemodifierscalar:{constant:"0.075"}}}]}}],
  ["order_weapon",{parent:"inv_stat'weapon'",attributes:{attribute:[{damage:{basemultiplier:{constant:"1.2"}}}]}}]
]);
const resolved = resolveStatDefinition("order_weapon",stats);
assert.deepEqual(resolved.lineage,["weapon","order_weapon"]);
assert.deepEqual(resolved.attributes.get("damage"),{definition:"attribute'weapon_damage'",stat:"damage",stattoattributemodifierscalar:{constant:"0.075"},basemultiplier:{constant:"1.2"}});
assert.equal(stats.get("weapon").attributes.attribute[0].damage.basemultiplier,undefined);
data.invAspects = new Map([["accuracy", {
  battributeeffecttemplateset: "true",
  attributeeffecttemplate: {modifiervalue:{datatablevalue:{datatable:"gbx_ue_data_table'Weights'",rowname:"Sniper"}}},
  attributeeffects:[{modifiervalue:{datatablevalue:{datatable:"gbx_ue_data_table'Weights'",rowname:"Sniper",columnname:"Spread"}}}]
}]]);
data.invStats = stats;
Object.assign(data.invRoots.get("weapon").root,{stats:"inv_stat'weapon'",uistats:["ui_stat'dps'"]});
Object.assign(data.invRoots.get("ord_ar").root,{stats:"inv_stat'order_weapon'",namingstrategydef:"inv_name_strategy'Order'",
  aspects:[{parent:"inv_aspect'accuracy'",attributeeffecttemplate:{modifiervalue:{datatablevalue:{rowname:"AssaultRifle"}}}}]});
const assembled = assembleItemDefinitions(data,{set:"ord_ar",partKeys:["damage","damage"],partRoots:["foreign","foreign"]});
assert.deepEqual(assembled.errors,[]);
assert.equal(assembled.statKey,"order_weapon");
assert.equal(assembled.namingStrategy,"order");
assert.deepEqual(assembled.stats.lineage,["weapon","order_weapon"]);
assert.equal(assembled.aspects.filter(a=>a.source==="foreign.damage").length,2);
const weights = assembled.aspects.find(a=>a.source==="ord_ar").definition;
assert.deepEqual(weights.attributeeffects[0].modifiervalue.datatablevalue,
  {datatable:"gbx_ue_data_table'Weights'",rowname:"AssaultRifle",columnname:"Spread"});
assert.equal(data.invAspects.get("accuracy").attributeeffects[0].modifiervalue.datatablevalue.rowname,"Sniper");

// Exercise the file reader too: a DLC reference cannot erase a concrete base
// row, and nested dependency entries must keep their item's scope.
const fs = require("fs"), os = require("os"), path = require("path");
const {loadStatData} = require("./serial_card_stats");
const directory = fs.mkdtempSync(path.join(os.tmpdir(),"msbt-native-inputs-"));
try {
  const write = (name,table,entries)=>fs.writeFileSync(path.join(directory,name),JSON.stringify({[table]:{records:[{entries}]}}));
  write("Nexus-Data-attribute0.json","attribute",[{damage:{attribute:"damage",value:{constant:"10"}}}]);
  write("Nexus-Data-attribute4.json","attribute",[{damage:{attribute:"damage"}}]);
  write("Nexus-Data-inv0.json","inv",[{ord_ar:{inv:"ord_ar",__dep_entries:[{grip:{aspects:[{source:"nested"}]}}]}}]);
  write("Nexus-Data-gbx_ue_data_table0.json","gbx_ue_data_table",[{defaults_test:{row_struct:"Asset'/Game/DefaultStruct.DefaultStruct'",data:[
    {row_name:"default",row_value:{}},{row_name:"zero",row_value:{Scale:0}},
    {row_name:"float",row_value:{Scale:1.09}},{row_name:"missing",row_value:{Other:4}}
  ]}}]);
  fs.writeFileSync(path.join(directory,"native_table_row_defaults.json"),JSON.stringify({definitions:{"asset'/game/defaultstruct.defaultstruct'":{
    defaults:{Scale_12_0123456789ABCDEF0123456789ABCDEF:1},properties:[{Name:"Scale_12_0123456789ABCDEF0123456789ABCDEF",Type:"FloatProperty"}]
  }}}));
  const loaded=loadStatData({legitItemsPath:directory});
  assert.equal(loaded.attributes.get("damage").value.constant,"10");
  assert.equal(loaded.invRoots.get("ord_ar").parts.get("grip").aspects[0].source,"nested");
  const {getDatatableCell} = require("./serial_card_stats");
  assert.equal(getDatatableCell(loaded.tables,"defaults_test","default","Scale"),1);
  assert.equal(getDatatableCell(loaded.tables,"defaults_test","zero","Scale"),0,"authored zero overrides native default");
  assert.equal(getDatatableCell(loaded.tables,"defaults_test","float","Scale"),Math.fround(1.09));
  assert.equal(getDatatableCell(loaded.tables,"defaults_test","missing","Unextracted"),null,"missing input must not be fabricated");
} finally {
  const temporaryRoot = path.resolve(os.tmpdir()) + path.sep;
  if (!path.resolve(directory).startsWith(temporaryRoot) || !path.basename(directory).startsWith("msbt-native-inputs-"))
    throw new Error("Temporary test directory escaped its intended location");
  fs.rmSync(directory,{recursive:true,force:true});
}

const sourceRoot=path.resolve(__dirname,"..");
const resolver=require("./serial_card_resolve").loadResolver({sourceRoot});
const shippedData=loadStatData({sourceRoot});
const fixtures=require("./fixtures/item_cards/mixed_order_user.json");
for (const [index,expectedCount] of [[1,412],[6,189],[11,181]]) {
  const card=resolver.resolveFromHuman(fixtures[index].human);
  const inputs=assembleItemDefinitions(shippedData,{set:card.set,partKeys:card.part_keys,partRoots:card.part_roots});
  assert.deepEqual(inputs.errors,[],`fixture ${index} has missing definitions`);
  assert.equal(inputs.sources.filter(s=>s.kind==="part").length,expectedCount);
  assert.deepEqual(inputs.sources.filter(s=>s.kind==="item").map(s=>s.id),["weapon","weapon_ar","ord_ar"]);
  assert.equal(inputs.statKey,"order_weapon");
  const accuracy=inputs.aspects.find(a=>a.definition.inv_aspect==="weapon_ui_acc_weights");
  assert.ok(accuracy,"inherited native accuracy weights must be present");
  assert.equal(accuracy.definition.attributeeffects[0].modifiervalue.datatablevalue.rowname,"AssaultRifle");
}
console.log("Native data traversal passed: inherited sources, ordered duplicate/cross-set parts, nested overrides, cycles, keyed stat patches.");
