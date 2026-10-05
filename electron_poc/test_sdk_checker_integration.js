const assert = require('assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');
const {app, ipcMain, BrowserWindow} = require('electron');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'msbt-checker-'));
app.setPath('userData', path.join(temp,'userdata'));
global.fetch = async () => { throw Error('Checker test is offline'); };
const handlers = new Map();
const original = ipcMain.handle.bind(ipcMain);
ipcMain.handle = (name, fn) => { handlers.set(name, fn); original(name, fn); };
require('./main');
app.whenReady().then(async () => {
  const win = BrowserWindow.getAllWindows()[0];
  win.hide();
  const sdk = path.join(__dirname,'../MattsSDKBoostingTools.sdkmod');
  const steam=path.join(temp,'Steam','sdk_mods'), epic=path.join(temp,'Epic','sdk_mods');
  for (const folder of [steam,epic]) {
    fs.mkdirSync(folder,{recursive:true});
    const exe=path.join(folder,'../OakGame/Binaries/Win64/Borderlands4.exe');
    fs.mkdirSync(path.dirname(exe),{recursive:true}); fs.writeFileSync(exe,'fixture');
  }
  fs.writeFileSync(path.join(steam,'MattsSDKBoostingTools.sdkmod'),'old steam');
  fs.copyFileSync(sdk,path.join(epic,'MattsSDKBoostingTools.sdkmod'));
  const check=handlers.get('app:getVersionInfo');
  const wrong=await check(null,steam), matching=await check(null,epic);
  assert.equal(wrong.installedSdkmod.sdkModsPath,steam);
  assert.equal(wrong.installedSdkmod.matchesBundled,false);
  assert.equal(matching.installedSdkmod.matchesBundled,true);
  assert.equal((await check(null,path.join(temp,'missing'))).installedSdkmod.matchesBundled,false);
  // Copying current bytes changes on-disk status, but cannot certify the running game.
  fs.copyFileSync(sdk,path.join(steam,'MattsSDKBoostingTools.sdkmod'));
  const after=await check(null,steam);
  assert.equal(after.installedSdkmod.matchesBundled,true);
  if (after.sdkTarget.running) assert.notEqual(after.loadedSdk.status,'current');
  const rendered=await win.webContents.executeJavaScript(`(() => {
    renderVersionInfo(${JSON.stringify({...wrong,loadedSdk:{status:'unverified',message:'Running SDK unverified'}})});
    return {text:els.installedSdkStatus.textContent, css:els.installedSdkStatus.className,path:els.installedSdkPath.textContent};
  })()`);
  assert.match(rendered.text,/differs/); assert.match(rendered.text,/unverified/);
  assert.match(rendered.css,/warning/); assert.ok(rendered.path.includes(steam));
  console.log('PASS real main IPC and renderer: Steam/Epic hash separation, unavailable path, refresh after install, no false loaded confirmation');
  win.destroy(); app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
