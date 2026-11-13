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
// Shell expands short user-directory names, including target/cwd/icon and the
// destination returned after writing. Resolve only registered existing paths.
function aliases(f) {
 const canonical=p=>path.win32.normalize(p).toLowerCase();
 const known=new Map();
 const add=(alias,physical)=>{known.set(canonical(alias),physical);known.set(canonical(physical),physical);};
 const oldAlias=f.old.replace('User','USER~1'),newAlias=f.exe.replace('Program Files','PROGRA~1');
 for(const [alias,physical] of [[oldAlias,f.old],[path.win32.dirname(oldAlias),path.win32.dirname(f.old)],[newAlias,f.exe]])add(alias,physical);
 const resolve=p=>{const result=known.get(canonical(p));if(!result)throw Error('ENOENT unverified alias');return result;};
 // Production prefers realpathSync.native; ensure that branch is covered.
 f.options.io.realpathSync=()=>{throw Error('native resolver should be preferred');};
 f.options.io.realpathSync.native=resolve;
 return {oldAlias,newAlias};
}
f=fixture();let alias=aliases(f);f.link.target=alias.oldAlias;f.link.cwd=path.win32.dirname(alias.oldAlias);f.link.icon=alias.oldAlias;
const writeAlias=f.options.shell.writeShortcutLink;f.options.shell.writeShortcutLink=(...args)=>{const written=writeAlias(...args);f.link.target=alias.newAlias;return written;};
r=migrateLegacyShortcut(f.options);assert.equal(r.status,'migrated',JSON.stringify(r));assert.equal(f.link.cwd,path.win32.dirname(f.exe));assert.equal(f.link.icon,f.exe);assert.equal(f.files.get(r.backup).toString(),'original shortcut');
f=fixture();alias=aliases(f);f.options.executable=alias.oldAlias;assert.equal(migrateLegacyShortcut(f.options).status,'skipped');assert.equal(f.writes(),0);
for(const target of ['C:\\User\\Local\\Programs\\Other\\app\\MattsSDKBoostingTools.exe','C:\\UNKNOWN~1\\Local\\Programs\\MSBT\\app\\MattsSDKBoostingTools.exe']) {
 f=fixture();aliases(f);f.link.target=target;r=migrateLegacyShortcut(f.options);assert.equal(r.status,'skipped');assert.equal(f.writes(),0);assert.equal(r.actualTarget,target);
}
assert.equal(newer('2.41.2','2.41.2'),false);assert.equal(newer('2.41.2','unknown'),false);
console.log('PASS bounded shortcut identity, newer-only migration, original backup, preserved custom fields, concurrent changes and write failures');
