'use strict';
const fs = require('fs');
const path = require('path');
const {createHash} = require('crypto');
const SHORTCUT_NAME = 'Borderlands 4 Modding Tools - Powered by Funk.lnk';
const PACKAGE_NAME = 'matts-sdk-boosting-tools';
function samePath(a,b) {return typeof a==='string' && typeof b==='string' && path.win32.resolve(a).toLowerCase()===path.win32.resolve(b).toLowerCase();}
function newer(a,b) {
  if(!/^\d+\.\d+\.\d+$/.test(a)||!/^\d+\.\d+\.\d+$/.test(b)) return false;
  const aa=a.split('.').map(Number),bb=b.split('.').map(Number);
  for(let i=0;i<3;i++) if(aa[i]!==bb[i])return aa[i]>bb[i];
  return false;
}
// Only the one known per-user Start Menu link is eligible. No installations or
// profiles are removed; the original link and an operation receipt are retained.
function migrateLegacyShortcut({app,shell,io=fs,env=process.env,platform=process.platform,executable=process.execPath}) {
  if(platform!=='win32'||!app.isPackaged) return {status:'skipped',reason:'Packaged Windows startup only'};
  if(!env.APPDATA||!env.LOCALAPPDATA) return {status:'skipped',reason:'User application paths unavailable'};
  const legacy=path.win32.join(env.LOCALAPPDATA,'Programs','MSBT','app','MattsSDKBoostingTools.exe');
  const shortcut=path.win32.join(env.APPDATA,'Microsoft','Windows','Start Menu','Programs',SHORTCUT_NAME);
  const result={status:'skipped',shortcut};
  let receipt,record;
  const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
  try {
    if(!path.win32.isAbsolute(executable)||path.win32.basename(executable).toLowerCase()!=='mattssdkboostingtools.exe'||samePath(executable,legacy)) return {...result,reason:'Running copy is not a different MSBT executable'};
    if(!io.statSync(executable).isFile()) return {...result,reason:'Running executable missing'};
    if(!io.existsSync(shortcut)) return {...result,reason:'Known user shortcut is absent'};
    const initial=io.readFileSync(shortcut);
    const link=shell.readShortcutLink(shortcut);
    if(!samePath(link.target,legacy)) return {...result,reason:'Shortcut does not target canonical legacy installation'};
    const oldPackage=JSON.parse(io.readFileSync(path.win32.join(path.win32.dirname(legacy),'resources','app.asar','package.json'),'utf8'));
    const currentPackage=JSON.parse(io.readFileSync(path.win32.join(path.win32.dirname(executable),'resources','app.asar','package.json'),'utf8'));
    if(oldPackage.name!==PACKAGE_NAME||currentPackage.name!==PACKAGE_NAME||currentPackage.version!==app.getVersion()||!newer(app.getVersion(),oldPackage.version)) return {...result,reason:'Application identity or strictly newer version not verified'};
    const backupRoot=path.join(app.getPath('userData'),'update-shortcut-backups');
    io.mkdirSync(backupRoot,{recursive:true});
    const folder=io.mkdtempSync(path.join(backupRoot,'migration-'));
    const backup=path.join(folder,SHORTCUT_NAME);
    io.writeFileSync(backup,initial,{flag:'wx'});
    receipt=path.join(folder,'receipt.json');
    record={...result,status:'prepared',backup,oldTarget:link.target,newTarget:executable,oldVersion:oldPackage.version,newVersion:app.getVersion(),originalSha256:hash(initial)};
    const save=()=>io.writeFileSync(receipt,JSON.stringify(record,null,2)+'\n');save();
    // Recheck the exact bytes and destination immediately before mutation.
    if(hash(io.readFileSync(shortcut))!==record.originalSha256||!samePath(shell.readShortcutLink(shortcut).target,legacy)) {
      record.status='skipped';record.reason='Shortcut changed before migration';save();return {...record,receipt};
    }
    const options={...link,target:executable};
    if(samePath(link.cwd,path.win32.dirname(legacy))) options.cwd=path.win32.dirname(executable);
    if(samePath(link.icon,legacy)) options.icon=executable;
    if(!shell.writeShortcutLink(shortcut,'update',options)) throw Error('Windows rejected shortcut update');
    if(!samePath(shell.readShortcutLink(shortcut).target,executable)) throw Error('Shortcut destination verification failed');
    record.status='migrated';save();return {...record,receipt};
  } catch(error) {
    const failure={...(record || result),status:'failed',reason:String(error.message||error),receipt};
    if(receipt) {try {io.writeFileSync(receipt,JSON.stringify(failure,null,2)+'\n');}catch {}}
    return failure;
  }
}
module.exports={SHORTCUT_NAME,samePath,newer,migrateLegacyShortcut};
