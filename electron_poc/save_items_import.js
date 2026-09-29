const yaml = require('js-yaml');
const crypto = require('node:crypto');
const schema = yaml.FAILSAFE_SCHEMA.extend(['scalar','sequence','mapping'].map(kind => new yaml.Type('!', {kind,multi:true,construct:data=>data})));
function extract(text) {
 if(Buffer.byteLength(text,'utf8')>48*1024*1024)throw Error('Decoded save exceeds 48 MB.');
 const doc=yaml.load(text,{schema,json:false}),state=doc?.state;
 if(!state?.inventory)throw Error('Choose a character save containing inventory, not a profile save.');
 const items=[],counts={Backpack:0,Equipped:0};let visited=0;
 function walk(node,section,ancestors=new Set(),depth=0){
  if(!node||typeof node!=='object')return;
  if(++visited>500000||depth>30||ancestors.has(node))throw Error('Invalid inventory structure.');
  const next=new Set(ancestors);next.add(node);
  for(const [key,value] of Object.entries(node)){
   if(key==='serial'&&typeof value==='string'&&value){
    if(!/^@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{/}~]+$/.test(value))throw Error('An inventory entry has an invalid item code. Nothing was imported.');
    items.push({serial:value,section,name:section+' item '+(++counts[section])});
   }else if(value&&typeof value==='object')walk(value,section,next,depth+1);
  }
 }
 walk(state.inventory.items?.backpack,'Backpack');walk(state.inventory.equipped_inventory?.equipped,'Equipped');
 if(!items.length)throw Error('No backpack or equipped item codes were found.');
 const name=String(state.char_name||'Character').trim();
 const level=(state.experience||[]).find(x=>x.type==='Character')?.level;
 return {name,level:level==null?'':String(level),suggestedFolder:(name+(level==null?'':' - Level '+level)).slice(0,180),backpack:items.filter(x=>x.section==='Backpack').length,equipped:items.filter(x=>x.section==='Equipped').length,items};
}
function merge(previous,preview,{mode,folder,skipDuplicates=false}){
 folder=String(folder||'').trim();
 if(!folder||folder.length>180||folder.split('/').some(x=>!x.trim()||['.','..'].includes(x.trim())))throw Error('Enter a folder name of 1–180 characters.');
 const existing=new Set([...(previous.folders||[]),...previous.bookmarks.map(x=>x.group)]);
 if(mode==='existing'&&!existing.has(folder))throw Error('Choose an existing folder.');
 if(mode!=='existing'&&mode!=='new')throw Error('Choose a destination.');
 if(mode==='new'&&existing.has(folder))throw Error('That folder already exists. Choose Add to existing folder or a different name.');
 const seen=new Set(previous.bookmarks.filter(x=>x.group===folder).map(x=>x.serial));
 const added=[],now=new Date().toISOString();
 for(const item of preview.items){if(skipDuplicates&&seen.has(item.serial))continue;seen.add(item.serial);added.push({id:'bm_'+crypto.randomUUID(),name:item.name,serial:item.serial,group:folder,source:'Save import: '+item.section,created_at:now,updated_at:now});}
 return {data:{version:1,bookmarks:[...previous.bookmarks,...added],folders:[...new Set([...(previous.folders||[]),folder])]},imported:added.length,skipped:preview.items.length-added.length,destination:folder};
}
module.exports={extract,merge};
