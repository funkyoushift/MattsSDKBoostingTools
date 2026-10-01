import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const response=await fetch('https://save-editor.be/GZO/Borderlands4/codes/api.php?action=catalog',{signal:AbortSignal.timeout(60000)});
if(!response.ok)throw Error('GZO catalog HTTP '+response.status);
const catalog=await response.json(),images={},conflicts=new Map();
for(const row of [...catalog.legit,...catalog.modded]){
 if(typeof row.base85!=='string'||!row.base85.startsWith('@U'))continue;
 let image='';
 if(row.image){const url=new URL(row.image.replace(/%(?![0-9a-f]{2})/ig,'%25'),'https://save-editor.be/GZO/Borderlands4/');if(url.protocol==='https:'&&url.hostname==='save-editor.be'&&url.pathname.startsWith('/GZO/'))image=url.href;}
 const key=crypto.createHash('sha256').update(row.base85).digest('hex'),name=typeof row.name==='string'?row.name.trim().slice(0,180):'';
 if(!images[key])images[key]={url:image,name,creator:row.creator,source:'https://save-editor.be/GZO/Borderlands4/Codes.html'};
 else {const old=images[key],conflict=conflicts.get(key)||new Set();for(const [field,value] of [['url',image],['name',name],['creator',row.creator]]){if(old[field]&&value&&old[field]!==value)conflict.add(field);else if(!old[field])old[field]=value;}conflicts.set(key,conflict);}
}
for(const [key,fields] of conflicts)for(const field of fields)images[key][field]='';
for(const [key,row] of Object.entries(images))if(!row.url&&!row.name)delete images[key];
const payload=JSON.stringify({builtAt:new Date().toISOString(),match:'SHA-256 of exact case-sensitive serial; conflicting titles or images omitted independently',images});
await fs.writeFile(new URL('./gzo-images.json',import.meta.url),payload);
if(process.argv[2])await fs.writeFile(process.argv[2],payload);
console.log(JSON.stringify({entries:Object.keys(images).length,images:Object.values(images).filter(x=>x.url).length,titles:Object.values(images).filter(x=>x.name).length}));
