'use strict';
// Run with the packaged Electron executable and ELECTRON_RUN_AS_NODE=1.
// Refuse development-tree resolution; validate the full required dependency graph.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]);
const errors=[],seen=new Set();
function inside(file){return file.startsWith(root+path.sep);}
function findPackage(from,name){
 for(const base of Module._nodeModulePaths(from)){
  const p=path.join(base,name,'package.json');if(inside(p)&&fs.existsSync(p))return p;
 }
 throw Error('Missing packaged dependency '+name+' required by '+path.relative(root,from));
}
function walk(file){
 if(seen.has(file))return;seen.add(file);
 const p=JSON.parse(fs.readFileSync(file,'utf8'));
 for(const name of Object.keys(p.dependencies||{})){
  if(p.optionalDependencies?.[name])continue;
  try{walk(findPackage(path.dirname(file),name));}catch(e){errors.push(e.message);}
 }
}
walk(path.join(root,'package.json'));
const req=Module.createRequire(path.join(root,'package.json'));
// Do not allow a missing dependency to escape the artifact under test.
const resolve=Module._resolveFilename;
Module._resolveFilename=function(name,parent,...args){
 const file=resolve.call(this,name,parent,...args);
 if(parent?.filename?.startsWith(root+path.sep)&&!Module.isBuiltin(name)&&!inside(file))throw Error('Dependency escaped package: '+name+' -> '+file);
 return file;
};
(async()=>{
 for(const name of Object.keys(req('./package.json').dependencies)){
  if(name==='gridstack')continue; // Browser bundle, not the package's ESM Node entry point.
  try{req(name);}catch(e){errors.push(name+': '+e.message);}
 }
 try{
  const png=await req('qrcode').toDataURL('https://www.funkyoushift.com/MattsSDKBoostingTools/mobile-install.html');
  assert.ok(png.startsWith('data:image/png;base64,'));
  assert.equal(Buffer.from(png.split(',')[1],'base64').subarray(1,4).toString(),'PNG');
 }catch(e){errors.push('QR generation: '+e.message);}
 try{assert.equal(req('js-yaml').load('value: 42').value,42);}catch(e){errors.push('YAML: '+e.message);}
 const html=fs.readFileSync(path.join(root,'renderer.html'),'utf8');
 for(const match of html.matchAll(/(?:src|href)=["']([^"']+)["']/g)){
  const ref=match[1];if(/^(?:[a-z]+:|#|\/\/)/i.test(ref))continue;
  const file=path.resolve(root,ref.split(/[?#]/)[0]);
  if(!inside(file)||!fs.existsSync(file))errors.push('Missing renderer asset: '+ref);
 }
 console.log(JSON.stringify({ok:errors.length===0,packages:seen.size,errors},null,2));
 process.exitCode=errors.length?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
