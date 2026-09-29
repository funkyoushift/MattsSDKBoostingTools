const assert=require('assert/strict'),fs=require('fs');const {extract,merge}=require('./save_items_import');
const text=`state:
  char_name: Test Rafa
  experience:
    - type: Character
      level: 70
  tags: !tags [foo]
  inventory:
    items:
      backpack:
        a: {serial: '@Uabc'}
        b: {serial: '@Uabc'}
      lost_loot:
        a: {serial: '@ULost'}
    equipped_inventory:
      equipped:
        a: {serial: '@Uequip'}
`;
const data=extract(text);assert.equal(data.backpack,2);assert.equal(data.equipped,1);assert.equal(data.level,'70');assert.equal(data.suggestedFolder,'Test Rafa - Level 70');
const previous={version:1,bookmarks:[{id:'x',group:'Mine',serial:'@Uabc'}],folders:['Mine']};
assert.equal(merge(previous,data,{mode:'existing',folder:'Mine'}).imported,3);
assert.equal(merge(previous,data,{mode:'existing',folder:'Mine',skipDuplicates:true}).imported,1);
assert.equal(merge(previous,data,{mode:'new',folder:'New',skipDuplicates:true}).imported,2);
assert.throws(()=>merge(previous,data,{mode:'new',folder:'Mine'}));assert.equal(previous.bookmarks.length,1);
assert.throws(()=>extract('state: {}'));assert.throws(()=>extract(text.replace('@Uabc','bad code')));
const {spawnSync}=require('child_process'),path=require('path');const helper=path.resolve(__dirname,'../external_app/v22_parts_codes_fixed/matt_editor_blcrypt.js');
for(const id of ['76561198894205533','0123456789abcdef0123456789abcdef']){
 const call=payload=>{const r=spawnSync(process.execPath,[helper],{input:JSON.stringify(payload),encoding:'utf8'});assert.equal(r.status,0);return JSON.parse(r.stdout);};
 const encrypted=call({command:'encrypt',steamid:id,yaml_content:text});assert.equal(encrypted.success,true);
 const decoded=call({command:'decrypt',steamid:id,sav_data:encrypted.sav_data||encrypted.encrypted});assert.equal(decoded.success,true);assert.deepEqual(extract(decoded.yaml_content),data);
}
console.log('PASS YAML scope, exact duplicates, destination validation, and local Steam/Epic encrypted save round trips');
