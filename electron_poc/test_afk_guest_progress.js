// Actual renderer: independent guest counts, safe names, mode and queue labels.
const assert = require('assert');
const path = require('path');
const {app, BrowserWindow} = require('electron');
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false,webPreferences:{sandbox:false,partition:`afk-guests-${process.pid}`}});
  await win.loadFile(path.join(__dirname,'renderer.html'),{query:{nosplash:'1'}});
  const result = await win.webContents.executeJavaScript(`(() => {
    bridgeStatus = async () => {};
    const guest = (name, submitted) => ({name,step:'loot',delivery:{players:[{submitted,total:500}]}});
    window.msbtAfkRender({afk_lobby:{enabled:true,config:{concurrent_guests:true},
      active_guests:[guest('<img src=x>',120),guest('Second',430),guest('Third',500)],
      queued:['<img src=x>','Second','Loading'],history:[]}});
    const box = document.getElementById('afkGuestProgress');
    const concurrent = {text:box.textContent,values:[...box.querySelectorAll('progress')].map(p=>p.value),
      images:box.querySelectorAll('img').length,queue:document.getElementById('afkQueue').textContent};
    window.msbtAfkRender({afk_lobby:{enabled:true,config:{},current:{name:'Solo',step:'loot'},queued:['Loading'],history:[]}});
    const sequential = {text:box.textContent,bars:box.querySelectorAll('progress').length};
    window.msbtAfkRender({afk_lobby:{enabled:false,config:{},history:[]}});
    return {concurrent,sequential,stopped:box.textContent};
  })()`);
  assert.deepEqual(result.concurrent.values,[120,430,500]);
  assert.equal(result.concurrent.images,0);
  assert.equal(result.concurrent.queue,'Waiting: Loading');
  assert.match(result.concurrent.text,/Concurrent AFK/);
  assert.match(result.concurrent.text,/500\/500/);
  assert.match(result.concurrent.text,/Waiting for settlement/);
  assert.match(result.sequential.text,/Sequential AFK/);
  assert.match(result.sequential.text,/Solo: loot/);
  assert.equal(result.sequential.bars,0);
  assert.equal(result.stopped,'AFK stopped');
  console.log('PASS independent guest progress, queue, safe names, legacy mode and stale-row clearing');
  win.destroy();app.exit(0);
}).catch(error=>{console.error(error);app.exit(1);});
