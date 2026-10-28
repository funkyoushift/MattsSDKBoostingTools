const assert=require('assert/strict');
const fs=require('fs');
const os=require('os');
const path=require('path');
const {app,ipcMain,BrowserWindow}=require('electron');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-update-ipc-'));
app.setPath('userData',path.join(temp,'userdata'));
const tag='v2.41.0';
const names=[`MSBT-Installer-${tag}-linux-x64.AppImage`,`MSBT-Portable-${tag}-linux-x64.tar.gz`];
global.fetch=async url=>{
  assert.equal(url,'https://api.github.com/repos/funkyoushift/MattsSDKBoostingTools/releases/latest');
  return {ok:true,json:async()=>({tag_name:tag,assets:names.map(name=>({name,size:123,digest:'sha256:'+'a'.repeat(64),browser_download_url:`https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/${tag}/${name}`}))})};
};
const handlers=new Map(),original=ipcMain.handle.bind(ipcMain);
ipcMain.handle=(name,fn)=>{handlers.set(name,fn);original(name,fn);};
require('./main');
app.whenReady().then(async()=>{
  BrowserWindow.getAllWindows().forEach(win=>win.hide());
  const result=await handlers.get('app:checkUpdates')(null,'');
  assert.equal(result.ok,true,result.message);
  assert.equal(result.remote.package_version,'2.41.0');
  assert.equal(result.updateAvailable,true);
  assert.match(result.electronInstallerUrl,/linux-x64\.AppImage$/);
  assert.match(result.manualZipUrl,/linux-x64\.tar\.gz$/);
  assert(!result.latestUrl.endsWith('.exe'));
  console.log('PASS actual Linux update IPC reads GitHub API and returns platform-specific download links');
  app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
