const assert = require('node:assert/strict');
const path = require('node:path');
const {app, BrowserWindow} = require('electron');
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false, webPreferences:{partition:`afk-store-${process.pid}`}});
  await win.loadFile(path.join(__dirname, 'renderer.html'), {query:{nosplash:'1'}});
  await win.webContents.executeJavaScript(`(async () => {
    const config = {guaranteed_codes: '@URepeated\\n'.repeat(650000), codes:'@UPool', saved_at:123};
    await window.msbtAfkConfigStore.save(config);
  })()`);
  await win.reload();
  await new Promise(resolve => win.webContents.once('did-finish-load', resolve));
  const result = await win.webContents.executeJavaScript(`(async () => {
    const config = await window.msbtAfkConfigStore.load();
    return {count:config.guaranteed_codes.split('\\n').length-1, pool:config.codes, stamp:config.saved_at};
  })()`);
  assert.deepEqual(result, {count:650000,pool:'@UPool',stamp:123});
  await win.webContents.session.clearStorageData();
  console.log('PASS large AFK lists survive page reload with duplicates intact');
  win.destroy(); app.quit();
}).catch(error => {console.error(error);app.exit(1);});
