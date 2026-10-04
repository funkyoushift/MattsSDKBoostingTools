// Exercise the actual panel with bridge responses; never contacts the game.
const assert = require('assert');
const path = require('path');
const {app, BrowserWindow} = require('electron');
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false, webPreferences:{sandbox:false, partition:`afk-count-${process.pid}`}});
  await win.loadFile(path.join(process.env.MSBT_TEST_APP_DIR || __dirname, 'renderer.html'), {query:{nosplash:'1'}});
  const result = await win.webContents.executeJavaScript(`(async () => {
    const wait = () => new Promise(resolve => setTimeout(resolve, 50));
    const count = document.getElementById('afkRandomCount');
    const capabilities = {loot_modes:['all','random70'],random_count_supported:true,
      bulk_loot_password_required:true,guaranteed_loot_supported:true};
    const render = (enabled, config) => window.msbtAfkRender({afk_lobby:{...capabilities,enabled,config,history:[]}});
    bridgeStatus = async () => {};
    await wait();
    render(false, {});
    count.value = '500';
    // Another controller starts the lobby after this panel has connected.
    render(true, {loot:true,loot_mode:'random70',random_count:70});
    const activeCount = Number(count.value);
    const activeLocked = count.disabled;
    render(true, {loot:true,loot_mode:'random70',random_count:35});
    const updatedCount = Number(count.value);
    render(false, {});
    const calls = [];
    requestBackpackPassword = async () => 'test-only-password';
    bridgeAction = async (action, payload) => {
      calls.push({action,payload});
      if (payload.random_count > 70 && !payload.bulk_loot_password)
        return {data:{ok:false,password_required:true,password_kind:'bulk_loot'}};
      return {data:{ok:true,afk_lobby:{...capabilities,enabled:true,config:payload,history:[]}}};
    };
    for (const size of [1,35,70,71,500]) {
      render(false, {});
      count.value = String(size);
      document.getElementById('afkCodes').value = '@UTest';
      document.getElementById('afkStart').click();
      await wait();
      if (Number(count.value) !== size || !count.disabled) throw Error('Start changed count or failed: '+size);
    }
    const saved = await window.msbtAfkConfigStore.load();
    return {activeCount,activeLocked,updatedCount,calls,savedCount:saved.random_count,
      savedPassword:Object.hasOwn(saved,'bulk_loot_password')};
  })()`);
  assert.equal(result.activeCount,70,'Running panel must show effective count, not a stale saved 500');
  assert.equal(result.updatedCount,35,'Subsequent active configurations must be reflected');
  assert(result.activeLocked);
  assert.deepEqual(result.calls.map(c=>c.payload.random_count),[1,35,70,71,71,500,500]);
  assert.equal(result.calls.at(-1).payload.bulk_loot_password,'test-only-password');
  assert.equal(result.savedCount,500);
  assert.equal(result.savedPassword,false);
  console.log('PASS active count synchronization, 1/35/70/71/500, password retry and persistence');
  win.destroy();app.exit(0);
}).catch(error => {console.error(error);app.exit(1);});
