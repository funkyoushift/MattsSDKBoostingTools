"use strict";
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const {app, BrowserWindow} = require("electron");
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "msbt-focus-"));
app.setPath("userData", profile);
global.fetch = async () => { throw Error("Focus regression: network disabled"); };
setTimeout(() => { console.error("Focus regression timed out"); app.exit(1); }, 20000).unref();
require("./main");
app.whenReady().then(async () => {
  const panel = BrowserWindow.getAllWindows()[0];
  if (panel.webContents.isLoading()) await new Promise(resolve => panel.webContents.once("did-finish-load", resolve));
  const helper = new BrowserWindow({show:false, frame:false, width:546, height:1200,
    webPreferences:{offscreen:true, sandbox:true, contextIsolation:true}});
  await helper.loadURL("about:blank");
  // Enumeration order is not an ownership contract. Exercise the helper-first case.
  const enumerate = BrowserWindow.getAllWindows;
  BrowserWindow.getAllWindows = () => [helper, panel];
  await panel.webContents.executeJavaScript(`(async () => {
    ensureLiveSdkReady = async () => ({ok:true});
    bridgeAction = async () => ({data:{ok:true,message:'Test delivery accepted'}});
    startSerialDeliveryProgressWatch = () => {};
    bl4SelectedEntries = () => [{id:'fixture',name:'Fixture',serial:'@UTest'}];
    bl4ValidSerialEntries = rows => rows;
    els.bl4OverrideLevel.value = 'false';
    document.querySelector('[data-bl4-send-mode="local"]').click();
    await new Promise(resolve => setTimeout(resolve, 50));
    document.getElementById('bl4InlineConfirmOk').click();
    await new Promise(resolve => setTimeout(resolve, 200));
  })()`);
  assert.strictEqual(helper.isVisible(), false, "Catalog Send must not show the hidden card-capture window");
  assert.strictEqual(panel.isVisible(), true, "Catalog panel remains visible");
  await panel.webContents.executeJavaScript("cancelBl4InlineDelivery()");
  await new Promise(resolve => setTimeout(resolve, 100));
  assert.strictEqual(helper.isVisible(), false, "Catalog Cancel must not show the hidden helper");
  BrowserWindow.getAllWindows = enumerate;
  helper.destroy(); panel.destroy();
  console.log("PASS real catalog Send/Confirm/Cancel IPC keeps offscreen helper hidden");
  app.exit(0);
}).catch(error => {console.error(error); app.exit(1);});
