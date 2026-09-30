"use strict";
// Real Electron lifecycle: no game, relay, user settings or credentials needed.
const assert = require('node:assert/strict');
if (!process.versions.electron) {
  const {spawnSync} = require('node:child_process');
  for (const mode of ['remote-close', 'plain-close', 'update-quit']) {
    const result = spawnSync(require('electron'), [__filename, mode], {
      encoding:'utf8', timeout:15000, windowsHide:true
    });
    assert.ifError(result.error);
    assert.equal(result.status,0, `${mode}: ${result.stderr}`);
    assert.match(result.stdout,/LIFECYCLE_EXIT_OK/);
  }
  console.log('PASS real Electron exits on X with remote on/off and updater quit.');
} else {
  const {app, BrowserWindow} = require('electron');
  const {EventEmitter} = require('node:events');
  const {createRemoteBackground} = require('./remote_background');
  let blocks=0, trays=0;
  class Tray extends EventEmitter {
    constructor(){super();trays++;}
    setToolTip(){} setContextMenu(){} destroy(){trays--;}
  }
  app.whenReady().then(()=>{
    const bg=createRemoteBackground({app,BrowserWindow,Tray,
      Menu:{buildFromTemplate:x=>x},nativeImage:{createFromPath:x=>x},
      powerSaveBlocker:{start:()=>++blocks,stop:()=>blocks--},iconPath:'test',onDisable:()=>{}});
    const win=new BrowserWindow({show:false});
    bg.bind(win);
    const mode=process.argv[2];
    bg.update({enabled:mode!=='plain-close'});
    app.on('will-quit',()=>{
      assert.equal(blocks,0);assert.equal(trays,0);
      assert.equal(BrowserWindow.getAllWindows().length,0);
      console.log('LIFECYCLE_EXIT_OK');
    });
    if(mode==='update-quit')app.quit();else win.close();
  });
}
