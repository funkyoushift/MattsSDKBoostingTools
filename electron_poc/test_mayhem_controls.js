"use strict";
const {app, BrowserWindow} = require("electron");
const assert = require("node:assert/strict");
const path = require("node:path");
app.disableHardwareAcceleration();
app.whenReady().then(async () => {
  const win = new BrowserWindow({show:false, width:1280, height:1000,
    webPreferences:{partition:`mayhem-${process.pid}`}});
  for (const mode of ["workspace", "classic"]) {
    await win.loadFile(path.join(__dirname, "renderer.html"), {query:{nosplash:"1", workspace:mode}});
    const result = await win.webContents.executeJavaScript(`(async () => {
      bridgeStatus = async () => {};
      const calls = [];
      runAction = async (action, payload) => {calls.push({action,payload});return {ok:true};};
      state.selectedTarget = "1|Papa_615_Bear";
      if (window.MsbtWorkspace?.enabled) window.MsbtWorkspace.open("boosting", "challenges");
      else window.switchTab("boosting");
      const button = document.getElementById("mayhemBoostBtn");
      const input = document.getElementById("mayhemBoostRank");
      const initial = input.value;
      button.disabled = false;
      button.click();
      input.value = "7"; button.click();
      const rect = button.getBoundingClientRect();
      return {initial, calls, visible:rect.width > 0 && rect.height > 0,
        scope:button.closest("section").textContent.includes("current lobby"),
        hostOnly:button.dataset.hostOnly};
    })()`);
    assert.equal(result.initial, "20");
    assert(result.visible && result.scope && result.hostOnly === "1", JSON.stringify(result));
    assert.deepEqual(result.calls, [20,7].map(mayhem_rank => ({action:"mayhem_boost",
      payload:{mayhem_rank,target_player:"1|Papa_615_Bear"}})));
    console.log(mode + ": Mayhem target, rank and scope passed");
  }
  win.destroy(); app.quit();
}).catch(error => {console.error(error); app.exit(1);});
