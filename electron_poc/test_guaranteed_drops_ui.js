"use strict";
const assert = require("assert");
const path = require("path");
const { app, BrowserWindow } = require("electron");
const root = process.env.MSBT_TEST_APP_ROOT || __dirname;

app.whenReady().then(async () => {
  const win = new BrowserWindow({ show: false, webPreferences: { sandbox: false, partition: `drop-rate-${process.pid}` } });
  await win.loadFile(path.join(root, "renderer.html"), { query: { nosplash: "1" } });
  const result = await win.webContents.executeJavaScript(`(async () => {
    const requests = [];
    let active = false;
    let rejectEnable = false;
    const weights = {common:1,uncommon:1,rare:1,epic:1,legendary:1,pearlescent:1};
    const status = () => ({ok:true,rarity_weights:weights,rarity_revision:12,
      drop_rate:{active,owned:active,conflict:false,last_error:"",persisted:false}});
    bridgeStatus = async () => {};
    window.msbt = {bridgeRequest:async (request) => {
      requests.push(request);
      if (request.method === "GET") return {ok:true,data:status()};
      const action = request.payload.action;
      if (action === "drop_rate_on" && rejectEnable) return {ok:true,data:{ok:false,message:"Unsupported game build"}};
      if (action === "drop_rate_on") active = true;
      if (action === "drop_rate_off") active = false;
      return {ok:true,data:{ok:true,message:action,active,owned:active}};
    }};
    state.players = [{index:0,name:"Host"},{index:1,name:"Guest"}];
    state.hostPlayerIndex = 0;
    state.selectedTarget = "1|Guest";
    setRarityPreset({common:3,uncommon:8,rare:17,epic:29,legendary:73,pearlescent:91});
    const draft = currentRarityPreset();
    const original = runRarityAction;
    let pending;
    runRarityAction = (action) => (pending = original(action));
    const buttons = ["drop_rate_on", "drop_rate_off"].map(action => document.querySelector('[data-rarity-action="'+action+'"]'));
    const panels = buttons.map(button => button.closest("[data-msbt-panel]").dataset.msbtPanel);
    const observations = [];
    for (const button of buttons) {
      pending = null;
      button.click();
      if (!pending) throw new Error("Drop-rate click not wired");
      await pending;
      observations.push({text:document.getElementById("dropRateStatus").textContent,preset:currentRarityPreset()});
    }
    active = true;
    state.rarityBridgeRevision = 12;
    syncBoostingRaritySlidersFromBridge(status());
    const sameRevision = document.getElementById("dropRateStatus").textContent;
    syncDropRateStatus({});
    const oldSdk = document.getElementById("dropRateStatus").textContent;
    syncDropRateStatus({drop_rate:{}});
    const emptySdk = document.getElementById("dropRateStatus").textContent;
    syncDropRateStatus({drop_rate:{active:true,conflict:true,last_error:"Another patch changed code"}});
    const conflict = document.getElementById("dropRateStatus").textContent;
    active = false;
    rejectEnable = true;
    const failure = await runRarityAction("drop_rate_on");
    const failureOutput = els.boostOutput.textContent;
    await runRarityAction("rarity_reset");
    return {panels,draft,observations,requests,sameRevision,oldSdk,emptySdk,conflict,failure,failureOutput,
      settings:raritySettingsPayload(),active};
  })()`);
  assert.deepStrictEqual(result.panels, ["boost-rarity", "boost-rarity"]);
  assert.match(result.observations[0].text, /ON/);
  assert.match(result.observations[1].text, /OFF/);
  for (const row of result.observations) assert.deepStrictEqual(row.preset, result.draft);
  const posts = result.requests.filter(request => request.method === "POST");
  assert.deepStrictEqual(posts.map(request => request.payload.action), ["drop_rate_on", "drop_rate_off", "drop_rate_on", "rarity_reset"]);
  assert.deepStrictEqual(posts[0].payload.payload, {}, "lobby action must not inherit selected guest or rarity weights");
  assert.match(result.sameRevision, /ON/);
  assert.match(result.oldSdk, /unavailable/);
  assert.match(result.emptySdk, /unavailable/);
  assert.match(result.conflict, /code conflict.*Another patch/);
  assert.match(result.failureOutput, /Unsupported game build/);
  assert.strictEqual(result.active, false);
  assert.strictEqual(Object.hasOwn(result.settings, "drop_rate"), false);
  console.log("PASS drop-rate UI: real buttons, host-lobby payload, On/Off state, drafts preserved, unchanged revision, old SDK, conflicts and refusal; never persisted");
  win.destroy(); app.exit(0);
}).catch(error => { console.error(error); app.exit(1); });
