'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const source=path.resolve(process.argv[2]),artifact=path.resolve(process.argv[3]);
const {minimatch}=require(path.join(source,'electron_poc/node_modules/minimatch'));
const pkg=JSON.parse(fs.readFileSync(path.join(source,'electron_poc/package.json'),'utf8'));
const errors=[];let checked=0;
const bundled=JSON.parse(fs.readFileSync(path.join(artifact,'app.asar/package.json'),'utf8'));
if(bundled.version!==pkg.version||JSON.stringify(bundled.dependencies)!==JSON.stringify(pkg.dependencies))errors.push('Packaged version or dependency declarations differ');
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
function check(a,b){checked++;if(!fs.existsSync(b))errors.push('Missing: '+path.relative(artifact,b));else if(hash(a)!==hash(b))errors.push('Different: '+path.relative(artifact,b));}
function tree(from,to,filters=['**/*'],rel=''){
 for(const row of fs.readdirSync(path.join(from,rel),{withFileTypes:true})){
  const r=(rel?rel+'/':'')+row.name;
  if(r==='package-lock.json'||r==='package.json'||r.startsWith('build/'))continue;
  if(row.name==='node_modules'||row.name.startsWith('_tmp_')||row.isSymbolicLink())continue;
  const negatives=filters.filter(x=>x.startsWith('!')).map(x=>x.slice(1));
  if(negatives.some(x=>minimatch(r+(row.isDirectory()?'/':''),x,{dot:true})))continue;
  if(row.isDirectory()){tree(from,to,filters,r);continue;}
  if(filters.some(x=>!x.startsWith('!')&&minimatch(r,x,{dot:true})))check(path.join(from,r),path.join(to,r));
 }
}
tree(path.join(source,'electron_poc'),path.join(artifact,'app.asar'),pkg.build.files);
for(const spec of pkg.build.extraResources){const from=path.resolve(source,'electron_poc',spec.from),to=path.join(artifact,spec.to);if(fs.statSync(from).isDirectory())tree(from,to,spec.filter);else check(from,to);}
console.log(JSON.stringify({ok:!errors.length,checked,errors},null,2));process.exitCode=errors.length?1:0;
