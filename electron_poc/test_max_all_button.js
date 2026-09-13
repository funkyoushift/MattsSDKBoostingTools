"use strict";
const assert = require("assert");
const path = require("path");
const { app, BrowserWindow } = require("electron");

app.whenReady().then(async () => {
  const win = new BrowserWindow({ show: false, webPreferences: { sandbox: false, partition: `max-all-${process.pid}` } });
  await win.loadFile(path.join(__dirname, "renderer.html"), { query: { nosplash: "1" } });
  const results = await win.webContents.executeJavaScript(`(async () => {
    const calls = [];
    window.msbt = { bridgeRequest: async (request) => {
      calls.push(request);
      return { ok: true, data: { ok: true, ok_count: request.payload.payload.party_indices.length, fail_count: 0 } };
    } };
    bridgeStatus = async () => {};
    state.players = [{index:0,name:"Host"},{index:1,name:"Guest"}];
    state.hostPlayerIndex = 0;
    state.selectedTarget = "1|Guest";
    const button = document.querySelector('[data-action="max_all"]');
    const originalHandler = runBoostActionButton;
    let lastClick;
    runBoostActionButton = (node) => (lastClick = originalHandler(node));
    const scopes = [];
    for (const scope of ["local", "selected", "all", "nonhost"]) {
      state.publicBoostScope = scope;
      button.click();
      if (!lastClick) throw new Error("Max All click handler is not wired");
      const result = await lastClick;
      scopes.push({scope, result, request:calls.at(-1), disabled:button.disabled});
    }
    state.publicBoostScope = "selected";
    state.selectedTarget = "9|Gone";
    const beforeMissing = calls.length;
    const missing = await runMaxAllScoped();
    const missingCalls = calls.length - beforeMissing;
    state.publicBoostScope = "local";
    let complete;
    window.msbt.bridgeRequest = (request) => { calls.push(request); return new Promise(resolve => { complete = resolve; }); };
    const pending = runMaxAllScoped();
    const disabledDuring = button.disabled;
    const beforeDuplicate = calls.length;
    const duplicate = await runMaxAllScoped();
    const duplicateCalls = calls.length - beforeDuplicate;
    complete({ok:true,data:{ok:true,queued:true,message:"Queued for game tick"}});
    const queued = await pending;
    window.msbt.bridgeRequest = async () => { throw new Error("Connection refused"); };
    const failure = await runMaxAllScoped();
    return {scopes,missing,missingCalls,disabledDuring,duplicate,duplicateCalls,queued,failure,
      failureText:els.boostOutput.textContent,disabledAfter:button.disabled};
  })()`);
  for (const [i, indices] of [[0,[0]],[1,[1]],[2,[0,1]],[3,[1]]]) {
    const row = results.scopes[i];
    assert.deepStrictEqual(row.request.payload.payload.party_indices, indices, row.scope);
    assert.strictEqual(row.request.payload.action, "max_all");
    assert.strictEqual(row.result.ok, true);
    assert.strictEqual(row.disabled, false);
  }
  assert.strictEqual(results.missing.ok, false);
  assert.strictEqual(results.missingCalls, 0);
  assert.strictEqual(results.disabledDuring, true);
  assert.strictEqual(results.duplicateCalls, 0);
  assert.strictEqual(results.queued.message, "Queued for game tick");
  assert.strictEqual(results.queued.okCount, undefined);
  assert.strictEqual(results.failure.ok, false);
  assert.match(results.failureText, /Connection refused/);
  assert.strictEqual(results.disabledAfter, false);
  console.log("PASS Max All button: four scopes, actual click wiring, missing target, duplicate guard, queued response, visible connection failure");
  win.destroy();
  app.exit(0);
}).catch(error => { console.error(error); app.exit(1); });
