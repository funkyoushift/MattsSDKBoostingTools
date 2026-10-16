/**
 * One-off Electron screenshot helper for Discord release media.
 * Usage (from electron_poc): npx electron ../tools/capture_discord_screenshots.js
 */
const { app, BrowserWindow, ipcMain } = require("electron");
const fs = require("fs");
const path = require("path");

const ELECTRON_ROOT = path.resolve(__dirname, "..", "electron_poc");
const OUT_DIR = path.resolve(__dirname, "..", "releases", "discord_media");

const SHOTS = [
  {
    tab: "quick-menu",
    file: "05-quick-menu-editor.png",
    waitMs: 900,
    note: "Quick Menu editor tab"
  },
  {
    tab: "boosting",
    file: "06-boosting-qm-pins.png",
    waitMs: 900,
    note: "Boosting tab with + QM pins",
    after: `
      const pin = document.querySelector('#giveCurrencyBtn')?.parentElement?.querySelector('.qm-add, button') 
        || Array.from(document.querySelectorAll('button')).find((b) => b.textContent.trim() === '+ QM');
      const anchor = document.getElementById('giveCurrencyBtn') || pin;
      if (anchor) anchor.scrollIntoView({ block: 'center', behavior: 'instant' });
    `
  },
  {
    tab: "serial-tools",
    file: "07-serial-bookmarks-qm.png",
    waitMs: 900,
    note: "Serial Bookmarks gold + QM buttons",
    after: `
      const el = document.getElementById('bookmarkQmSelectedBtn');
      if (el) el.scrollIntoView({ block: 'center', behavior: 'instant' });
    `
  },
  {
    tab: "bl4-codes",
    file: "08-bl4-codes-qm.png",
    waitMs: 1200,
    note: "BL4 Codes gold + QM buttons",
    after: `
      const el = document.getElementById('bl4QmSelectedBtn');
      if (el) el.scrollIntoView({ block: 'center', behavior: 'instant' });
    `
  },
  {
    tab: "updates",
    file: "09-updates-install-sdkmod.png",
    waitMs: 700,
    note: "Updates / install SDK mod"
  }
];

function stubIpc() {
  const ok = async () => ({ ok: true });
  const emptyArr = async () => [];
  const emptyObj = async () => ({});
  const handlers = {
    "bridge:request": async () => ({ ok: false, message: "offline (screenshot mode)" }),
    "app:browseSdkMods": ok,
    "app:detectSdkMods": async () => ({ ok: true, path: "" }),
    "app:downloadUpdate": ok,
    "app:getVersionInfo": async () => ({
      ok: true,
      package_version: "2.0.0",
      electron_version: "2.0.0",
      sdkmod_version: "2.0.0",
      app_version: "2.0.0"
    }),
    "app:getWindowSettings": async () => ({ opacity: 1 }),
    "app:installSdkMod": ok,
    "app:quitAndInstallUpdate": ok,
    "app:checkUpdates": async () => ({ ok: true, status: "none" }),
    "app:getUserDataInfo": async () => ({ ok: true, path: OUT_DIR }),
    "app:openUserDataFolder": ok,
    "app:exportUserDataBackup": ok,
    "app:mattEditorUrl": async () => ({ ok: true, url: "" }),
    "app:serialToolsConvert": async () => ({ ok: true, output: "", message: "" }),
    "app:serialDecodeCheck": async () => ({ ok: true, output: "", message: "" }),
    "app:validatorBasic": async () => ({ ok: true, output: "", message: "" }),
    "app:validatorBulk": async () => ({ ok: true, output: "", message: "" }),
    "app:readDevSpawnerCatalog": async () => ({ ok: true, catalog: [] }),
    "app:loadDevSpawnerFavorites": async () => ({ ok: true, favorites: [] }),
    "app:saveDevSpawnerFavorites": ok,
    "app:loadSerialBookmarks": async () => ({
      ok: true,
      data: {
        version: 1,
        bookmarks: [
          {
            id: "shot-1",
            name: "Demo Pearl",
            group: "Showcase",
            serial: "@Udemo0001",
            note: "screenshot row"
          },
          {
            id: "shot-2",
            name: "Demo Legendary",
            group: "Showcase",
            serial: "@Udemo0002",
            note: ""
          }
        ]
      }
    }),
    "app:saveSerialBookmarks": ok,
    "app:loadMovementSettings": emptyObj,
    "app:saveMovementSettings": ok,
    "app:loadRaritySettings": emptyObj,
    "app:saveRaritySettings": ok,
    "app:loadBl4Catalog": async () => ({ ok: true, entries: [], source: "screenshot" }),
    "app:refreshGzoCatalog": async () => ({ ok: true, entries: [] }),
    "app:bl4PartsBreakdown": async () => ({ ok: true, parts: [] }),
    "app:submitGzoCode": ok,
    "app:readSdkLogTail": async () => ({ ok: true, text: "" }),
    "app:readResourceJson": async () => ({ ok: true, data: {} }),
    "app:saveReportFile": ok,
    "app:openExternal": ok,
    "app:setWindowOpacity": ok
  };
  for (const [channel, handler] of Object.entries(handlers)) {
    ipcMain.handle(channel, handler);
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function capture() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  stubIpc();

  const win = new BrowserWindow({
    width: 1480,
    height: 960,
    show: true,
    backgroundColor: "#101014",
    webPreferences: {
      preload: path.join(ELECTRON_ROOT, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  await win.loadFile(path.join(ELECTRON_ROOT, "renderer.html"));
  await sleep(1800);

  // Seed a realistic Quick Menu catalog/layout so + QM pins and the editor grid render.
  await win.webContents.executeJavaScript(`
    (() => {
      const catalog = Object.fromEntries([
        ["max_all", "Max All"],
        ["max_currency", "Max Currency"],
        ["max_eridium", "Max Eridium"],
        ["give_currency", "Give Currency"],
        ["set_level", "Set Level"],
        ["open_golden_chest", "Open Chest"],
        ["give_serial_selected", "Give Serial Selected"],
        ["give_serial_all", "Give Serial All"],
        ["give_serial_nonhost", "Give Serial Non-Host"],
        ["repeat_last_drop", "Repeat Last Drop"],
        ["shiny_selected", "Shinies Selected"],
        ["travel_to_map", "Travel Map"],
        ["movement_apply_all", "Apply Movement"],
        ["rarity_apply", "Apply Rarity"],
        ["spawn_itempool", "Spawn Item Pool"],
        ["uvh_boost_all", "UVH Boost All"],
        ["open_bank", "Open Bank"],
        ["devperk_0", "Give Experience"],
        ["devperk_1", "Give 1M Cash"]
      ].map(([action, basic]) => [action, { basic, assignable: true }]));
      const emptyPage = () => Array.from({ length: 12 }, () => null);
      const pages = Array.from({ length: 5 }, emptyPage);
      pages[0][0] = { action: "max_all", custom_label: "" };
      pages[0][1] = { action: "max_currency", custom_label: "Cash" };
      pages[0][2] = { action: "open_golden_chest", custom_label: "" };
      pages[0][3] = { action: "give_serial_selected", custom_label: "Pearl Drop" };
      pages[0][4] = { action: "repeat_last_drop", custom_label: "" };
      pages[0][5] = { action: "shiny_selected", custom_label: "" };
      state.quickMenuSnapshot = {
        ok: true,
        revision: 7,
        catalog,
        assignable_actions: Object.keys(catalog),
        layout: { schema_version: 1, page: 0, pages }
      };
      state.quickMenuPage = 0;
      state.quickMenuSelectedSlot = 0;
      state.quickMenuLastCommand = { action: "give_serial_selected", label: "Pearl Drop", payload: { serial_text: "@Udemo" } };
      state.quickMenuLastDrop = { action: "give_serial_selected", label: "Pearl Drop", payload: {} };
      if (typeof selectQuickMenuSlot === "function") selectQuickMenuSlot(0);
      if (typeof renderQuickMenuEditor === "function") renderQuickMenuEditor();
      if (typeof installQuickMenuAddButtons === "function") installQuickMenuAddButtons();
      if (typeof refreshQuickMenuPinPanel === "function") refreshQuickMenuPinPanel({ quiet: true });
      const status = document.getElementById("bridgeStatus");
      if (status) {
        status.textContent = "Bridge ready for Quick Menu (screenshot demo layout).";
        status.className = "status-line ok";
      }
      return true;
    })();
  `);
  await sleep(500);

  for (const shot of SHOTS) {
    await win.webContents.executeJavaScript(`
      (() => {
        if (typeof switchTab === 'function') {
          switchTab(${JSON.stringify(shot.tab)});
        } else {
          const btn = document.querySelector('.tab-bar [data-tab="${shot.tab}"]');
          if (btn) btn.click();
        }
        if (typeof installQuickMenuAddButtons === 'function') installQuickMenuAddButtons();
        ${shot.after || ""}
        return true;
      })();
    `);
    await sleep(shot.waitMs || 700);
    const image = await win.capturePage();
    const outPath = path.join(OUT_DIR, shot.file);
    fs.writeFileSync(outPath, image.toPNG());
    console.log(`Wrote ${outPath} (${shot.note})`);
  }

  await win.close();
  app.quit();
}

app.whenReady().then(capture).catch((error) => {
  console.error(error);
  app.exit(1);
});
