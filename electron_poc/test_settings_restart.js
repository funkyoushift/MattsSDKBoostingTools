"use strict";
// Two independent Electron processes, real main/preload/renderer and disk IPC.
// Network is offline so the test cannot apply saved actions to a running game.
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");

if (!process.versions.electron) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "msbt-restart-"));
  try {
    for (const phase of ["save", "restore", "unchecked"]) {
      const result = spawnSync(require("electron"), [__filename, phase, dir], { encoding: "utf8", timeout: 90000 });
      process.stdout.write(result.stdout || "");
      process.stderr.write(result.stderr || "");
      assert.strictEqual(result.status, 0, `${phase}: ${result.error || "test failed"}`);
    }
    console.log("PASS: settings survive two complete app exits and restarts, including unchecked values");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
} else {
  const { app, BrowserWindow, ipcMain } = require("electron");
  const phase = process.argv[2];
  app.setPath("userData", process.argv[3]);
  global.fetch = async () => { throw new Error("Persistence test: network offline"); };
  const loaded = new Set();
  const handle = ipcMain.handle.bind(ipcMain);
  ipcMain.handle = (channel, listener) => handle(channel, async (...args) => {
    const result = await listener(...args);
    if (channel.startsWith("app:load")) loaded.add(channel);
    return result;
  });
  require("./main");
  app.whenReady().then(async () => {
    const win = BrowserWindow.getAllWindows()[0];
    win.hide();
    const deadline = Date.now() + 60000;
    while (!loaded.has("app:loadRaritySettings") || !loaded.has("app:loadMovementSettings")) {
      assert.ok(Date.now() < deadline, "startup settings did not load");
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    await new Promise(resolve => setTimeout(resolve, 250));
    const result = await win.webContents.executeJavaScript(`(async () => {
      const phase = ${JSON.stringify(phase)};
      if (phase === "save") {
        els.movementSpeedScale.value = "1.75";
        els.movementIndividualJumpGoals.checked = true;
        els.movementZeroVaultOnApply.checked = true;
        els.movementAutoApplySaved.checked = true;
        await saveMovementSettings();
        setRarityPreset({common:0,uncommon:7,rare:15,epic:28,legendary:63,pearlescent:91});
        els.rarityRememberPreset.checked = true;
        await saveRaritySettings();
        await startMainTutorial({force:true});
        walkthroughNodes().dontShow.checked = true;
        await endWalkthrough({skipped:true});
        setBootWelcomeDismissed(true);
        return {ok:true};
      }
      await maybeStartWalkthrough();
      const result = {
        movement:currentMovementPreset(), auto:els.movementAutoApplySaved.checked,
        rarity:currentRarityPreset(), remember:els.rarityRememberPreset.checked,
        welcome:isBootWelcomeDismissed(), tourActive:walkthroughState.active,
        tourPreference:walkthroughState.dontShowAgain
      };
      if (phase === "restore") {
        els.movementAutoApplySaved.checked = false;
        await saveMovementSettings();
        els.rarityRememberPreset.checked = false;
        await saveRaritySettings();
      }
      return result;
    })()`);
    if (phase !== "save") {
      assert.strictEqual(result.movement.speedScale, "1.75");
      assert.strictEqual(result.movement.individualJumpGoals, true);
      assert.strictEqual(result.movement.zeroVaultOnApply, true);
      assert.strictEqual(result.auto, phase === "restore");
      assert.strictEqual(result.remember, phase === "restore");
      if (phase === "restore") assert.strictEqual(result.rarity.legendary, 63);
      assert.strictEqual(result.welcome, true);
      assert.strictEqual(result.tourActive, false);
      assert.strictEqual(result.tourPreference, true);
    }
    console.log(`PASS app ${phase}: ${JSON.stringify(result)}`);
    win.close();
  }).catch(error => { console.error(error); app.exit(1); });
}
