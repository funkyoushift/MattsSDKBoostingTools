"use strict";
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");
const { app, BrowserWindow } = require("electron");
const { loadBl4Catalog } = require("./bl4_codes_catalog");
app.whenReady().then(async () => {
  const fixture = process.argv[2]
    ? JSON.parse(fs.readFileSync(process.argv[2], "utf8"))
    : await loadBl4Catalog(path.resolve(__dirname, "../external_app/v22_parts_codes_fixed/resources"));
  const win = new BrowserWindow({ show: false, webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false } });
  win.webContents.session.webRequest.onBeforeRequest({ urls: ["http://*/*", "https://*/*"] }, (_details, callback) => callback({ cancel: true }));
  await win.loadFile(path.join(__dirname, "renderer.html"), { query: { nosplash: "1" } });
  const result = await win.webContents.executeJavaScript(`(async () => {
    const data = ${JSON.stringify(fixture)};
    // Simulate the card resolver replacing character-specific catalog types.
    // No game, network, inventory or settings calls are made by this test.
    resolveOfflineCardMap = async serials => new Map(serials.map(serial => [serial,
      {meta_ok:true,item_type:'Classmod'}]));
    enrichVisibleBl4CardsOffline = async () => {};
    acceptBl4CatalogResult(data);
    state.bl4SearchQuery = '';
    setBl4ListingSection('Modded');
    const counts = {};
    for (const character of ['Amon','Vex','Harlowe']) {
      els.bl4TypeFilter.value = character;
      els.bl4TypeFilter.dispatchEvent(new Event('change'));
      const before = filteredBl4Entries().length;
      if (!before) throw new Error(character + ': empty before cards load');
      const mods = state.bl4Entries.filter(row => gzoForm().isClassmodCatalogItem(row));
      const updated = new Map((await enrichBl4EntriesOffline(mods)).map(row=>[row.id,row]));
      state.bl4Entries = state.bl4Entries.map(row=>updated.get(row.id)||row);
      renderBl4Codes({preserveSearchFocus:true});
      const after = filteredBl4Entries().length;
      if (after !== before) throw new Error(character + ': lost matches after cards load');
      counts[character] = after;
    }
    return {total:state.bl4Entries.length,counts};
  })()`);
  assert.ok(result.total > 0);
  win.destroy();
  console.log("PASS actual catalog dropdown UI before/after card loading", JSON.stringify(result));
  app.exit(0);
}).catch(error => { console.error(error); app.exit(1); });
