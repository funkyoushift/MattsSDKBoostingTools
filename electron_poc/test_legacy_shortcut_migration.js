'use strict';
const assert=require('assert/strict');
const path=require('path');
const {migrateLegacyShortcut,newer,SHORTCUT_NAME}=require('./legacy_shortcut_migration');
function fixture() {
 const env={APPDATA:'C:\\User\\Roaming',LOCALAPPDATA:'C:\\User\\Local'};
 const old='C:\\User\\Local\\Programs\\MSBT\\app\\MattsSDKBoostingTools.exe';
 const exe='C:\\Program Files\\MSBT\\MattsSDKBoostingTools.exe';
 const shortcut=path.win32.join(env.APPDATA,'Microsoft','Windows','Start Menu','Programs',SHORTCUT_NAME);
 const files=new Map([[shortcut,Buffer.from('original shortcut')]]);let writes=0,reads=0;
 const link={target:old,cwd:path.win32.dirname(old),args:'--custom-option',icon:'C:\\custom.ico',iconIndex:2,description:'My tools'};
 const io={existsSync:p=>files.has(p),statSync:()=>({isFile:()=>true}),readFileSync:(p)=>{if(p.endsWith('package.json'))return JSON.stringify({name:'matts-sdk-boosting-tools',version:p.startsWith(path.win32.dirname(old))?'2.40.1':'2.41.2'});if(!files.has(p))throw Error('Missing fixture file '+p);return files.get(p);},mkdirSync:()=>{},mkdtempSync:p=>p+'unique',writeFileSync:(p,b)=>{files.set(p,Buffer.from(b));}};
 const shell={readShortcutLink:()=>{reads++;return {...link};},writeShortcutLink:(p,op,options)=>{writes++;assert.equal(p,shortcut);assert.equal(op,'update');Object.assign(link,options);files.set(p,Buffer.from('updated shortcut'));return true;}};
 const options={app:{isPackaged:true,getVersion:()=> '2.41.2',getPath:()=> 'C:\\User\\data'},shell,io,env,platform:'win32',executable:exe};
 return {options,files,link,old,exe,shortcut,writes:()=>writes,reads:()=>reads};
}
let f=fixture(),r=migrateLegacyShortcut(f.options);
assert.equal(r.status,'migrated');assert.equal(f.writes(),1);assert.equal(f.link.target,f.exe);assert.equal(f.link.args,'--custom-option');assert.equal(f.link.icon,'C:\\custom.ico');assert.equal(f.link.cwd,path.win32.dirname(f.exe));assert.equal(f.files.get(r.backup).toString(),'original shortcut');assert.equal(JSON.parse(f.files.get(r.receipt)).status,'migrated');
for(const change of [f=>f.link.target='C:\\Other\\tool.exe',f=>f.options.app.getVersion=()=> '2.40.0',f=>f.options.executable=f.old,f=>f.options.platform='linux',f=>f.options.app.isPackaged=false]) {f=fixture();change(f);assert.equal(migrateLegacyShortcut(f.options).status,'skipped');assert.equal(f.writes(),0);}
f=fixture();const read=f.options.io.readFileSync;f.options.io.readFileSync=p=>p.endsWith('package.json')?JSON.stringify({name:'other',version:'1.0.0'}):read(p);assert.equal(migrateLegacyShortcut(f.options).status,'skipped');assert.equal(f.writes(),0);
for(const oldVersion of ['2.41.2','2.42.0','unverified']) {f=fixture();const read=f.options.io.readFileSync;f.options.io.readFileSync=p=>p.endsWith('package.json')&&p.startsWith(path.win32.dirname(f.old))?JSON.stringify({name:'matts-sdk-boosting-tools',version:oldVersion}):read(p);assert.equal(migrateLegacyShortcut(f.options).status,'skipped');assert.equal(f.writes(),0);}
f=fixture();f.files.delete(f.shortcut);assert.equal(migrateLegacyShortcut(f.options).status,'skipped');assert.equal(f.writes(),0);
f=fixture();const original=f.options.io.readFileSync;let count=0;f.options.io.readFileSync=p=>p===f.shortcut&&++count===2?Buffer.from('concurrent edit'):original(p);r=migrateLegacyShortcut(f.options);assert.equal(r.status,'skipped');assert.match(r.reason,/changed/);assert.equal(f.writes(),0);
f=fixture();f.options.shell.writeShortcutLink=()=>false;r=migrateLegacyShortcut(f.options);assert.equal(r.status,'failed');assert.match(r.reason,/rejected/);assert.equal(f.files.get(r.receipt).toString().includes('failed'),true);assert.equal(f.link.target,f.old);
f=fixture();f.options.io.writeFileSync=()=>{throw Error('Backup disk full');};r=migrateLegacyShortcut(f.options);assert.equal(r.status,'failed');assert.equal(f.writes(),0);
assert.equal(newer('2.41.2','2.41.2'),false);assert.equal(newer('2.41.2','unknown'),false);
console.log('PASS bounded shortcut identity, newer-only migration, original backup, preserved custom fields, concurrent changes and write failures');
