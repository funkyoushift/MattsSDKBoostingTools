"use strict";
const assert = require("assert");
const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { app, BrowserWindow } = require("electron");

app.whenReady().then(async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-settings-test-"));
  try {
    for (const [file, stem, flag] of [
      ["movement_settings_store", "Movement", "autoApplyOnStart"],
      ["rarity_settings_store", "Rarity", "rememberOnStart"],
      ["walkthrough_store", "Walkthrough", "dontShowAgain"]
    ]) {
      const store = require(`./${file}`);
      const dest = path.join(dir, file + ".json");
      await Promise.all(Array.from({ length: 20 }, (_, i) => store[`write${stem}Settings`](dest, {
        [flag]: i % 2 === 0, preset: { speedScale: String(i), legendary: i }, appVersion: "test"
      })));
      const read = await store[`read${stem}Settings`](dest);
      assert.strictEqual(read.ok, true);
      assert.strictEqual(read.data[flag], false, "last toggle must win");
      if (stem === "Movement") assert.strictEqual(read.data.preset.speedScale, "19");
      if (stem === "Rarity") assert.strictEqual(read.data.preset.legendary, 19);
      if (stem === "Walkthrough") assert.strictEqual(read.data.appVersion, "test");
    }
    const win = new BrowserWindow({ show: false, webPreferences: { sandbox: false, partition: `settings-${process.pid}` } });
    await win.loadFile(path.join(__dirname, "renderer.html"), { query: { nosplash: "1" } });
    await new Promise(resolve => setTimeout(resolve, 700));
    const result = await win.webContents.executeJavaScript(`(async () => {
      let saved;
      window.msbt = {
        loadRaritySettings: async () => ({ok:true,data:{updated_at:"test",rememberOnStart:true,preset:{common:0,legendary:37}}}),
        saveWalkthroughSettings: async data => { saved = data; return {ok:true,data}; },
        loadWalkthroughSettings: async () => ({ok:true,data:saved})
      };
      await loadRaritySettings();
      const before = currentRarityPreset();
      syncBoostingRaritySlidersFromBridge({rarity_revision:1,rarity_weights:{legendary:1}});
      const afterFirst = currentRarityPreset();
      syncBoostingRaritySlidersFromBridge({rarity_revision:1,rarity_weights:{legendary:1}});
      const afterPoll = currentRarityPreset();
      syncBoostingRaritySlidersFromBridge({rarity_revision:2,rarity_weights:{legendary:0.5}});
      const afterChange = currentRarityPreset();
      state.versionInfo = {appVersion:"test-v1"};
      await startMainTutorial({force:true});
      walkthroughNodes().dontShow.checked = true;
      await endWalkthrough({skipped:true});
      const dismissed = !walkthroughState.active;
      localStorage.removeItem(TUTORIAL_LS_LAST_SEEN);
      localStorage.removeItem(TUTORIAL_LS_MAIN_SEEN);
      await maybeStartWalkthrough();
      const restored = !walkthroughState.active;
      await startMainTutorial({force:true});
      const replay = walkthroughState.active && walkthroughNodes().dontShow.checked;
      await endWalkthrough({skipped:true});
      state.versionInfo = {appVersion:"test-v2"};
      await maybeStartWalkthrough();
      const update = walkthroughState.active;
      walkthroughNodes().dontShow.checked = false;
      await endWalkthrough({skipped:true});
      const optedBackIn = saved.dontShowAgain === false;
      await maybeStartWalkthrough();
      const tourReturns = walkthroughState.active;
      await endWalkthrough({skipped:true});
      setMobileAnnounceDismissed(false);
      await showMobileAnnounceModal({force:true});
      els.mobileAnnounceDontShow.checked = true;
      openMobileGatewayPanel();
      const mobileDismissed = isMobileAnnounceDismissed();
      await showMobileAnnounceModal();
      const mobileStaysHidden = els.mobileAnnounceModal.classList.contains("hidden");
      await showMobileAnnounceModal({force:true});
      const mobileChoiceRestored = els.mobileAnnounceDontShow.checked;
      els.mobileAnnounceDontShow.checked = false;
      els.mobileAnnounceDismissBtn.click();
      const mobileOptedBackIn = !isMobileAnnounceDismissed();
      return {before,afterFirst,afterPoll,afterChange,dismissed,restored,replay,update,optedBackIn,tourReturns,mobileDismissed,mobileStaysHidden,mobileChoiceRestored,mobileOptedBackIn};
    })()`);
    assert.strictEqual(result.before.legendary, 37);
    assert.strictEqual(result.afterFirst.legendary, 37);
    assert.strictEqual(result.afterPoll.legendary, 37);
    assert.strictEqual(result.afterChange.legendary, 50);
    for (const key of ["dismissed", "restored", "replay", "update", "optedBackIn", "tourReturns", "mobileDismissed", "mobileStaysHidden", "mobileChoiceRestored", "mobileOptedBackIn"]) assert.strictEqual(result[key], true, key);
    await win.loadFile(path.join(__dirname, "renderer.html"));
    const bootChoice = await win.webContents.executeJavaScript(`(async () => {
      const splash = document.getElementById("msbtBootSplash");
      const shown = Boolean(splash && !splash.classList.contains("is-done"));
      document.getElementById("bootWelcomeDontShow").checked = true;
      document.getElementById("bootWelcomeCloseBtn").click();
      await new Promise(resolve => setTimeout(resolve, 320));
      return {shown, saved:isBootWelcomeDismissed()};
    })()`);
    assert.strictEqual(bootChoice.shown, true, "boot welcome must be visible before opt-out");
    assert.strictEqual(bootChoice.saved, true, "boot welcome opt-out must be stored");
    await win.loadFile(path.join(__dirname, "renderer.html"));
    const bootRestored = await win.webContents.executeJavaScript(`(async () => {
      await new Promise(resolve => setTimeout(resolve, 320));
      const splash = document.getElementById("msbtBootSplash");
      return isBootWelcomeDismissed() && (!splash || splash.classList.contains("is-done"));
    })()`);
    assert.strictEqual(bootRestored, true, "boot welcome opt-out must survive a reload");
    win.destroy();
    console.log("PASS: concurrent saves, last toggle wins, rarity, tour, announcement and boot opt-out persistence");
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
  app.exit(0);
}).catch(error => { console.error(error); app.exit(1); });
