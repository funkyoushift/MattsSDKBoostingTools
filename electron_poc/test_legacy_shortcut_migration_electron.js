'use strict';
// Native Electron shell fixture: creates links only inside a disposable temp tree.
const fs=require('fs');
const path=require('path');
const os=require('os');
const assert=require('assert/strict');
const {migrateLegacyShortcut,sameExistingPath,SHORTCUT_NAME}=require('./legacy_shortcut_migration');
function guardedRoot(temp) {
 if(!temp||path.dirname(path.resolve(temp))!==path.resolve(os.tmpdir())||!path.basename(temp).startsWith('msbt-shortcut-test-'))throw Error('Unexpected fixture cleanup path');
 return temp;
}
if(process.versions.electron) {
 const {app,shell}=require('electron');
 const temp=guardedRoot(process.argv[2]);
 for(const [name,folder] of [['userData','electron-userdata'],['crashDumps','electron-crashes']]) {
  const directory=path.join(temp,folder);fs.mkdirSync(directory,{recursive:true});app.setPath(name,directory);
 }
 app.whenReady().then(async()=>{
  const env={APPDATA:path.join(temp,'Roaming'),LOCALAPPDATA:path.join(temp,'Local')};
  const legacy=path.join(env.LOCALAPPDATA,'Programs','MSBT','app','MattsSDKBoostingTools.exe');
  const executable=path.join(temp,'new-install','MattsSDKBoostingTools.exe');
  for(const [exe,version] of [[legacy,'2.40.1'],[executable,'2.41.2']]){
   const resources=path.join(path.dirname(exe),'resources');fs.mkdirSync(resources,{recursive:true});
   const source=path.join(temp,'package-source-'+version);fs.mkdirSync(source);
   const identity={name:'matts-sdk-boosting-tools',version};
   fs.writeFileSync(path.join(source,'package.json'),JSON.stringify(identity));
   fs.writeFileSync(exe,'fixture only; never executable');
   const archive=path.join(resources,'app.asar');
   await require('@electron/asar').createPackage(source,archive);
   assert(require('original-fs').statSync(archive).isFile(),'Fixture must contain a physical ASAR archive');
   // Exercise Electron's real archive-aware reads used by production migration.
   assert.deepEqual(JSON.parse(fs.readFileSync(path.join(archive,'package.json'),'utf8')),identity);
  }
  const shortcut=path.join(env.APPDATA,'Microsoft','Windows','Start Menu','Programs',SHORTCUT_NAME);fs.mkdirSync(path.dirname(shortcut),{recursive:true});
  assert(shell.writeShortcutLink(shortcut,'create',{target:legacy,cwd:path.dirname(legacy),args:'--fixture',description:'preserve fixture description',icon:process.execPath,iconIndex:0}));
  const before=fs.readFileSync(shortcut);
  const initialLink=shell.readShortcutLink(shortcut);
  assert(sameExistingPath(initialLink.target,legacy),JSON.stringify({actualTarget:initialLink.target,expectedTarget:legacy}));
  const result=migrateLegacyShortcut({app:{isPackaged:true,getVersion:()=> '2.41.2',getPath:()=>path.join(temp,'userdata')},shell,env,executable});
  assert.equal(result.status,'migrated',JSON.stringify({...result,initialTarget:initialLink.target,expectedTarget:legacy}));assert.deepEqual(fs.readFileSync(result.backup),before);
  const after=shell.readShortcutLink(shortcut);assert(sameExistingPath(after.target,executable),JSON.stringify({actualTarget:after.target,expectedTarget:executable}));assert.equal(after.args,'--fixture');assert(sameExistingPath(after.icon,process.execPath));assert.equal(after.description,'preserve fixture description');
  console.log('PASS native Electron shortcut update, preserved fields and exact original backup');
 app.exit(0);
 }).catch(error=>{console.error(error);app.exit(1);});
} else {
 (async()=>{
  if(process.platform!=='win32'){console.log('SKIP native Windows shortcut fixture');return;}
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-shortcut-test-'));
  try {
   const binary=process.env.ELECTRON_BINARY || require('electron');
   const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;
   await new Promise((resolve,reject)=>{
    const child=require('child_process').spawn(binary,[__filename,temp],{env,stdio:'inherit',windowsHide:true});
    let launchError;child.once('error',error=>{launchError=error;});
    child.once('close',(code,signal)=>launchError?reject(launchError):code===0?resolve():reject(Error('Native shortcut fixture exited '+code+' signal '+signal)));
   });
  } finally {
   // The Electron process has exited, releasing its cached ASAR file handles.
   guardedRoot(temp);fs.rmSync(temp,{recursive:true,force:true});
   assert(!fs.existsSync(temp),'Fixture cleanup did not remove its disposable root');
  }
  console.log('PASS native shortcut fixture exited and disposable root removed');
 })().catch(error=>{console.error(error);process.exitCode=1;});
}
