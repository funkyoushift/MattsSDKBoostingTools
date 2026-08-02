/**
 * Capture Discord media with tight crops around + QM buttons.
 * Usage (from electron_poc): npx electron ../tools/capture_discord_screenshots.js
 */
const { app, BrowserWindow, ipcMain } = require("electron");
const fs = require("fs");
const path = require("path");

const ELECTRON_ROOT = path.resolve(__dirname, "..", "electron_poc");
const OUT_DIR = path.resolve(__dirname, "..", "releases", "discord_media");

const SHOTS = [
  {
    tab: "boosting",
    file: "06-boosting-qm-pins.png",
    note: "Boosting + QM close-up",
    waitMs: 900,
    selectors: ["#giveCurrencyBtn", "#maxCurrencyBtn", "#maxEridiumBtn"],
    pad: 28
  },
  {
    tab: "serial-tools",
    file: "07-serial-bookmarks-qm.png",
    note: "Serial Bookmarks gold + QM close-up",
    waitMs: 1000,
    selectors: ["#bookmarkQmSelectedBtn", "#bookmarkQmAllBtn", "#bookmarkQmNonhostBtn"],
    pad: 40,
    after: `
      const tip = document.querySelector('.qm-serial-pin-row');
      if (tip && tip.nextElementSibling) tip.nextElementSibling.scrollIntoView({ block: 'nearest' });
    `
  },
  {
    tab: "bl4-codes",
    file: "08-bl4-codes-qm.png",
    note: "BL4 Codes gold + QM close-up",
    waitMs: 1100,
    selectors: ["#bl4QmSelectedBtn", "#bl4QmAllBtn", "#bl4QmNonhostBtn"],
    pad: 40
  },
  {
    tab: "boosting",
    file: "06b-boosting-serial-qm.png",
    note: "Serial give + QM close-up",
    waitMs: 800,
    selectors: ["[data-boost-serial-mode='selected']", "[data-boost-serial-mode='all']", "[data-boost-serial-mode='nonhost']"],
    pad: 36
  },
  {
    tab: "quick-menu",
    file: "05-quick-menu-editor.png",
    note: "Quick Menu editor overview",
    waitMs: 700,
    full: true
  },
  {
    tab: "updates",
    file: "09-updates-install-sdkmod.png",
    note: "Updates / install SDK mod",
    waitMs: 700,
    full: true
  }
];

function stubIpc() {
  const ok = async () => ({ ok: true });
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
          { id: "shot-1", name: "Demo Pearl", group: "Showcase", serial: "@Udemo0001", note: "" },
          { id: "shot-2", name: "Demo Legendary", group: "Showcase", serial: "@Udemo0002", note: "" }
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

async function seedQuickMenu(win) {
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
      if (typeof selectQuickMenuSlot === "function") selectQuickMenuSlot(0);
      if (typeof renderQuickMenuEditor === "function") renderQuickMenuEditor();
      if (typeof installQuickMenuAddButtons === "function") installQuickMenuAddButtons();
      document.querySelectorAll(".qm-add-button, .qm-pin-button").forEach((btn) => {
        btn.style.outline = "3px solid #ffe08a";
        btn.style.boxShadow = "0 0 0 4px rgba(255, 176, 61, 0.55)";
        btn.style.transform = "scale(1.05)";
      });
      return true;
    })();
  `);
}

async function boundsForSelectors(win, selectors, pad) {
  return win.webContents.executeJavaScript(`
    (() => {
      const selectors = ${JSON.stringify(selectors)};
      const pad = ${Number(pad) || 24};
      const nodes = [];
      for (const sel of selectors) {
        document.querySelectorAll(sel).forEach((n) => nodes.push(n));
        // Also include nearby + QM siblings in the same wrap/row.
        document.querySelectorAll(sel).forEach((n) => {
          const wrap = n.closest('.qm-action-wrap, .button-row, .qm-serial-pin-row');
          if (wrap) wrap.querySelectorAll('.qm-add-button, .qm-pin-button').forEach((b) => nodes.push(b));
        });
      }
      if (!nodes.length) return null;
      let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
      for (const node of nodes) {
        node.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
        const r = node.getBoundingClientRect();
        left = Math.min(left, r.left);
        top = Math.min(top, r.top);
        right = Math.max(right, r.right);
        bottom = Math.max(bottom, r.bottom);
      }
      const dpr = window.devicePixelRatio || 1;
      return {
        x: Math.max(0, Math.floor((left - pad) * dpr)),
        y: Math.max(0, Math.floor((top - pad) * dpr)),
        width: Math.max(40, Math.ceil((right - left + pad * 2) * dpr)),
        height: Math.max(40, Math.ceil((bottom - top + pad * 2) * dpr))
      };
    })();
  `);
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
  await seedQuickMenu(win);
  await sleep(400);

  for (const shot of SHOTS) {
    await win.webContents.executeJavaScript(`
      (() => {
        if (typeof switchTab === 'function') switchTab(${JSON.stringify(shot.tab)});
        else {
          const btn = document.querySelector('.tab-bar [data-tab="${shot.tab}"]');
          if (btn) btn.click();
        }
        if (typeof installQuickMenuAddButtons === 'function') installQuickMenuAddButtons();
        document.querySelectorAll('.qm-add-button, .qm-pin-button').forEach((btn) => {
          btn.style.outline = '3px solid #ffe08a';
          btn.style.boxShadow = '0 0 0 4px rgba(255, 176, 61, 0.55)';
        });
        ${shot.after || ""}
        return true;
      })();
    `);
    await sleep(shot.waitMs || 700);

    let image;
    if (shot.full) {
      image = await win.capturePage();
    } else {
      const rect = await boundsForSelectors(win, shot.selectors || [], shot.pad || 28);
      if (!rect) {
        console.warn(`No bounds for ${shot.file}; capturing full page`);
        image = await win.capturePage();
      } else {
        image = await win.capturePage(rect);
      }
    }
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
