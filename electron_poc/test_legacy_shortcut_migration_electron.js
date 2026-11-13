'use strict';
// Native Electron shell fixture: creates links only inside a disposable temp tree.
const {app,shell}=require('electron');
const fs=require('fs');
const path=require('path');
const os=require('os');
const assert=require('assert/strict');
const {migrateLegacyShortcut,SHORTCUT_NAME}=require('./legacy_shortcut_migration');
app.whenReady().then(()=>{
 if(process.platform!=='win32'){console.log('SKIP native Windows shortcut fixture');app.exit(0);return;}
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-shortcut-test-'));
 try {
  const env={APPDATA:path.join(temp,'Roaming'),LOCALAPPDATA:path.join(temp,'Local')};
  const legacy=path.join(env.LOCALAPPDATA,'Programs','MSBT','app','MattsSDKBoostingTools.exe');
  const executable=path.join(temp,'new-install','MattsSDKBoostingTools.exe');
  for(const [exe,version] of [[legacy,'2.40.1'],[executable,'2.41.2']]){
   const pkg=path.join(path.dirname(exe),'resources','app.asar','package.json');fs.mkdirSync(path.dirname(pkg),{recursive:true});
   fs.writeFileSync(exe,'fixture only; never executable');fs.writeFileSync(pkg,JSON.stringify({name:'matts-sdk-boosting-tools',version}));
  }
  const shortcut=path.join(env.APPDATA,'Microsoft','Windows','Start Menu','Programs',SHORTCUT_NAME);fs.mkdirSync(path.dirname(shortcut),{recursive:true});
  assert(shell.writeShortcutLink(shortcut,'create',{target:legacy,cwd:path.dirname(legacy),args:'--fixture',description:'preserve fixture description',icon:process.execPath,iconIndex:0}));
  const before=fs.readFileSync(shortcut);
  const result=migrateLegacyShortcut({app:{isPackaged:true,getVersion:()=> '2.41.2',getPath:()=>path.join(temp,'userdata')},shell,env,executable});
  assert.equal(result.status,'migrated',JSON.stringify(result));assert.deepEqual(fs.readFileSync(result.backup),before);
  const after=shell.readShortcutLink(shortcut);assert.equal(after.target,executable);assert.equal(after.args,'--fixture');assert.equal(after.icon,process.execPath);assert.equal(after.description,'preserve fixture description');
  console.log('PASS native Electron shortcut update, preserved fields and exact original backup');
 } finally {if(path.dirname(path.resolve(temp))!==path.resolve(os.tmpdir())||!path.basename(temp).startsWith('msbt-shortcut-test-'))throw Error('Unexpected fixture cleanup path');fs.rmSync(temp,{recursive:true,force:true});}
 app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
