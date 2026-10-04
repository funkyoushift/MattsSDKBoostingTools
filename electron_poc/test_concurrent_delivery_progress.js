// Real renderer: general delivery rows, safe player names and stale-row cleanup.
const assert = require('assert');
const path = require('path');
const {app, BrowserWindow} = require('electron');
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false, webPreferences:{sandbox:false, partition:`delivery-${process.pid}`}});
  await win.loadFile(path.join(__dirname, 'renderer.html'), {query:{nosplash:'1'}});
  const result = await win.webContents.executeJavaScript(`(() => {
    bridgeStatus = async () => {};
    updateSerialDeliveryProgress({active:true, method:'direct', message:'Sending', players:[
      {name:'<img src=x>', submitted:120, total:500},
      {name:'Second', submitted:35, total:35},
      {name:'Third', submitted:4, total:70, error:'Player left'}]});
    const box = document.getElementById('serialDeliveryPlayers');
    const active = {text:box.textContent, bars:[...box.querySelectorAll('progress')].map(p=>p.value), images:box.querySelectorAll('img').length};
    updateSerialDeliveryProgress({active:false});
    return {active, stopped:box.textContent};
  })()`);
  assert.deepEqual(result.active.bars, [120,35,4]);
  assert.equal(result.active.images, 0);
  assert.match(result.active.text, /120\/500/);
  assert.match(result.active.text, /Waiting for settlement/);
  assert.match(result.active.text, /Stopped: Player left/);
  assert.equal(result.stopped, '');
  const {serialDeliveryFingerprint} = require('./poll_coordinator');
  assert.notEqual(serialDeliveryFingerprint({message:'Same', players:[{submitted:10, done:false}]}),
    serialDeliveryFingerprint({message:'Same', players:[{submitted:10, done:true}]}));
  console.log('PASS general per-player progress, settlement, errors, safe names, clearing and poll changes');
  win.destroy(); app.exit(0);
}).catch(error => {console.error(error); app.exit(1);});
