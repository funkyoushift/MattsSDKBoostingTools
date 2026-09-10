"use strict";

// Node launches Electron using an absolute script path (also works with linked node_modules).
// EDITOR_ROOT also supports the standalone editor fork.
// The real page runs in an isolated, hidden browser: no preload, host IPC or user saves.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
if (!process.versions.electron) {
  const { spawnSync } = require("node:child_process");
  const env = { ...process.env };
  delete env.ELECTRON_RUN_AS_NODE;
  const temporaryRoot = fs.realpathSync(os.tmpdir());
  const profile = fs.mkdtempSync(path.join(temporaryRoot, "msbt-editor-page-update-"));
  env.MSBT_EDITOR_TEST_PROFILE = profile;
  let result;
  try {
    result = spawnSync(require("electron"), [__filename], { env, stdio: "inherit", windowsHide: true });
  } finally {
    // Delete only this test-created directory after Electron and its children exit.
    assert.equal(path.dirname(path.resolve(profile)), temporaryRoot);
    fs.rmSync(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  }
  if (result.error) process.stderr.write(String(result.error) + "\n");
  process.exit(result.status ?? 1);
}
const { app, BrowserWindow } = require("electron");
assert(process.env.MSBT_EDITOR_TEST_PROFILE, "Run this test with Node so it creates an isolated temporary profile");
app.setPath("userData", process.env.MSBT_EDITOR_TEST_PROFILE);

const editor = path.resolve(process.env.EDITOR_ROOT || path.join(__dirname, "../external_app/v22_parts_codes_fixed/matt_editor"));
const timeoutMs = 90000;
const blocked = new Set();
const missing = new Set();
const consoleErrors = [];
let server;
let win;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function until(code, label) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const result = await win.webContents.executeJavaScript(code);
    if (result) return result;
    await sleep(100);
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function run() {
  process.stdout.write('Editor page smoke: starting local server.\n');
  assert(fs.existsSync(path.join(editor, "index.html")), `Missing editor index: ${editor}`);
  server = http.createServer((req, res) => {
    let relative;
    try { relative = decodeURIComponent(new URL(req.url, "http://localhost").pathname); }
    catch (_) { res.writeHead(400).end(); return; }
    if (relative === "/") relative = "/index.html";
    const file = path.resolve(editor, "." + relative);
    const inside = path.relative(editor, file);
    if (inside.startsWith("..") || path.isAbsolute(inside) || /\.php$/i.test(file)) {
      // PHP discovery probes intentionally fail so the real loader uses static JSON.
      res.writeHead(404).end(); return;
    }
    fs.stat(file, (error, stat) => {
      if (error || !stat.isFile()) {
        missing.add(relative);
        res.writeHead(404).end(); return;
      }
      const mime = { ".html": "text/html", ".js": "application/javascript", ".json": "application/json", ".css": "text/css", ".png": "image/png", ".svg": "image/svg+xml", ".woff2": "font/woff2" };
      res.writeHead(200, { "Content-Type": mime[path.extname(file)] || "application/octet-stream", "Cache-Control": "no-store" });
      fs.createReadStream(file).pipe(res);
    });
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  win = new BrowserWindow({
    show: false, width: 1600, height: 1000,
    webPreferences: {
      partition: `editor-page-update-${process.pid}`,
      nodeIntegration: false, contextIsolation: true, sandbox: true,
      webSecurity: true, backgroundThrottling: false,
    },
  });
  const session = win.webContents.session;
  session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.webRequest.onBeforeRequest((details, callback) => {
    const url = new URL(details.url);
    const allowed = url.origin === origin || url.protocol === "data:" || (url.protocol === "blob:" && url.origin === origin);
    if (!allowed) blocked.add(details.url);
    callback({ cancel: !allowed });
  });
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  win.webContents.on("will-navigate", (event, url) => { if (new URL(url).origin !== origin) event.preventDefault(); });
  win.webContents.on("console-message", details => {
    if (details.level === "error") consoleErrors.push({ message: details.message, source: details.sourceId, line: details.lineNumber });
  });
  // Initialize Chromium before sending CDP commands; no editor code has run yet.
  await win.loadURL("about:blank");
  win.webContents.debugger.attach("1.3");
  await win.webContents.debugger.sendCommand("Page.enable");
  await win.webContents.debugger.sendCommand("Page.addScriptToEvaluateOnNewDocument", { source: `
    window.__editorPageErrors = [];
    window.__editorPageResources = [];
    window.addEventListener('error', event => {
      if (event.target !== window) {
        const element = event.target;
        window.__editorPageResources.push({ tag: element.tagName, url: element.src || element.href || '' });
      } else {
        window.__editorPageErrors.push({ message: event.message, source: event.filename, line: event.lineno });
      }
    }, true);
    window.addEventListener('unhandledrejection', event => {
      window.__editorPageErrors.push({ message: String(event.reason?.stack || event.reason), source: 'unhandledrejection' });
    });
    window.confirm = () => true;
    window.alert = message => { throw new Error('Unexpected alert: ' + message); };
  ` });
  await win.loadURL(origin + "/");
  process.stdout.write('Editor page smoke: page loaded; waiting for catalog.\n');
  const status = await until("window.getLegitBuilderDatasetStatus?.().loaded && window.getLegitBuilderDatasetStatus()", "native catalog");
  const catalog = await win.webContents.executeJavaScript(`(() => ({
    status: getLegitBuilderDatasetStatus(),
    classes: Object.values(CHARACTER_CLASSES).map(row => row.name),
    roots: data.rootDefinitions.filter(row => Number(row.serialIndex) === 402).map(row => row.key),
    lovelessCosmetics: NEXUS_ALL_COSMETICS.filter(id => id.startsWith('Unlockable_CorpoHacker.')).length,
    missionSets: Object.keys(NEXUS_MISSION_MANIFEST),
    localParts: (window.BL4_LOCAL_GAME_PART_SUPPLEMENT || window.MSBT_LOCAL_GAME_PART_SUPPLEMENT).length,
    hostApi: typeof window.electronAPI,
    nodeProcess: typeof window.process,
  }))()`);
  assert.equal(catalog.hostApi, "undefined");
  assert.equal(catalog.nodeProcess, "undefined");
  assert.equal(status.pack4NexusLoaded, true);
  assert(catalog.roots.some(key => key.toLowerCase() === "classmod_corpohacker"));
  assert.deepEqual(catalog.classes.sort(), ["Amon", "C4sh", "Harlowe", "Loveless", "Rafa", "Vex"]);
  assert.equal(catalog.lovelessCosmetics, 127);
  assert.equal(catalog.localParts, 7417);
  assert(catalog.missionSets.includes("missionset_dlc_viola"));
  await until("document.querySelector('#rootsContent .manufacturer-header[data-manufacturer=\"classmods\"]') !== null", "class mod category UI");
  await win.webContents.executeJavaScript(`(() => {
    document.querySelector('button[onclick="switchTab(\\'legit-builder-tab\\')"]').click();
    document.querySelector('#rootsContent .manufacturer-header[data-manufacturer="classmods"]').click();
  })()`);
  const rootText = await until("document.querySelector('#rootsContent [data-root-key=\"classmod_corpohacker\"]')?.textContent", "Loveless class mod UI");
  assert(rootText.includes("Loveless"), "Loveless must render in the actual builder");

  const ui = await win.webContents.executeJavaScript(`(() => {
    const fixture = {
      state: {
        character_class: 'Char_CorpoHacker',
        experience: [
          { type: 'Character', level: 60, points: 1234567 },
          { type: 'Specialization', level: 400, points: 7123456789 },
          { type: 'VaultCard5', level: 12, points: 8765 },
        ],
        inventory: { sentinel: 'synthetic inventory preserved' },
      },
      missions: { local_sets: { missionset_main_prologue: { sentinel: 'base game preserved' } } },
    };
    document.querySelector('button[onclick="switchTab(\\'save-editor-tab\\')"]').click();
    setSuppressYamlAnimations(true);
    setYamlTextareaValue(jsyaml.dump(fixture));
    renderEditValues();
    unlockPresetControls();
    const ids = ['preset-input-character-level', 'preset-input-specialization-level', 'preset-input-character-xp', 'preset-input-specialization-xp'];
    const controls = Object.fromEntries(ids.map(id => {
      const input = document.getElementById(id);
      if (!input) throw new Error('Missing actual XP/level input: ' + id);
      return [id, { max: input.max, value: input.value, disabled: input.disabled }];
    }));
    const buttons = Array.from(document.querySelectorAll('button[onclick]')).filter(button =>
      ['Complete', 'Reset'].some(action => ['providence', 'bp5'].some(zone =>
        button.getAttribute('onclick').includes("missionEditor" + action + "Zone('" + zone + "')"))));
    return { controls, buttons: buttons.map(button => button.textContent.trim()) };
  })()`);
  assert.equal(ui.controls["preset-input-character-level"].max, "70");
  assert.equal(ui.controls["preset-input-specialization-level"].max, "701");
  assert.equal(ui.controls["preset-input-character-xp"].value, "1234567");
  assert.equal(ui.controls["preset-input-specialization-xp"].value, "7123456789");
  assert(Object.values(ui.controls).every(control => !control.disabled));
  assert.equal(ui.buttons.length, 4, "Both new zones must have real complete/reset buttons");
  await win.webContents.executeJavaScript(`(() => {
    const input = document.getElementById('preset-input-character-level');
    input.value = '70'; input.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  await until("getYamlDataFromTextarea()?.state?.experience?.[0]?.level === 70", "character level input handler");
  await win.webContents.executeJavaScript(`(() => {
    const input = document.getElementById('preset-input-specialization-level');
    input.value = '701'; input.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  await until("getYamlDataFromTextarea()?.state?.experience?.[1]?.level === 701", "specialization level input handler");
  let saved = await win.webContents.executeJavaScript("getYamlDataFromTextarea()");
  assert.deepEqual(saved.state.experience.map(row => row.points), [1234567, 7123456789, 8765]);
  await win.webContents.executeJavaScript(`(() => {
    const input = document.getElementById('preset-input-character-xp');
    input.value = '0'; input.dispatchEvent(new Event('change', { bubbles: true }));
  })()`);
  saved = await win.webContents.executeJavaScript("getYamlDataFromTextarea()");
  assert.deepEqual(saved.state.experience.map(row => [row.level, row.points]), [[70, 0], [701, 7123456789], [12, 8765]]);

  for (const zone of ["providence", "bp5"]) {
    await win.webContents.executeJavaScript(`Array.from(document.querySelectorAll('button[onclick]')).find(button => button.getAttribute('onclick').includes("missionEditorCompleteZone('${zone}')")).click()`);
    await until(`Object.keys(getYamlDataFromTextarea()?.missions?.local_sets || {}).some(key => ${zone === "bp5" ? "key === 'missionset_dlc_viola'" : "/harmonica/.test(key)"})`, `${zone} complete button`);
  }
  const complete = await win.webContents.executeJavaScript("getYamlDataFromTextarea()");
  assert.equal(complete.missions.local_sets.missionset_main_prologue.sentinel, "base game preserved");
  assert.equal(complete.state.inventory.sentinel, "synthetic inventory preserved");
  for (const zone of ["providence", "bp5"]) {
    await win.webContents.executeJavaScript(`Array.from(document.querySelectorAll('button[onclick]')).find(button => button.getAttribute('onclick').includes("missionEditorResetZone('${zone}')")).click()`);
    await until(`!Object.keys(getYamlDataFromTextarea()?.missions?.local_sets || {}).some(key => ${zone === "bp5" ? "key === 'missionset_dlc_viola'" : "/harmonica/.test(key)"})`, `${zone} reset button`);
  }
  saved = await win.webContents.executeJavaScript("getYamlDataFromTextarea()");
  assert.equal(saved.missions.local_sets.missionset_main_prologue.sentinel, "base game preserved");
  assert.deepEqual(saved.state.experience.map(row => [row.level, row.points]), [[70, 0], [701, 7123456789], [12, 8765]]);
  await sleep(500);
  const errors = await win.webContents.executeJavaScript("({ runtime: __editorPageErrors, resources: __editorPageResources })");
  assert.deepEqual(errors.runtime, [], `Browser runtime errors: ${JSON.stringify(errors.runtime)}`);
  const requiredFailures = errors.resources.filter(row => row.tag === "SCRIPT" || row.tag === "LINK").filter(row => new URL(row.url).origin === origin);
  assert.deepEqual(requiredFailures, [], `Local scripts/styles failed: ${JSON.stringify(requiredFailures)}`);
  // The loader probes an optional shard absent from this native build in three layouts.
  const missingData = [...missing].filter(url => /\.(?:js|json|css)$/i.test(url) && !url.endsWith('/Nexus-Data-skilltrees_data6.json'));
  assert.deepEqual(missingData, [], `Missing local scripts/data: ${JSON.stringify(missingData)}`);
  assert.deepEqual([...missing].filter(url => url.includes('/corpo_hacker_icons/')), [], "New Loveless icons must load locally");
  const unexpectedConsoleErrors = consoleErrors.filter(row => !(row.message.startsWith('Error loading Monaco Editor:') && [...blocked].some(url => url.includes('/monaco-editor@'))));
  assert.deepEqual(unexpectedConsoleErrors, [], `Unexpected console errors: ${JSON.stringify(unexpectedConsoleErrors)}`);
  process.stdout.write(`PASS editor full page: ${catalog.status.fileCount} native tables, Loveless root402 / 127 cosmetics, six classes, XP input preservation, Providence/BP5 complete/reset.\n`);
  const imageWarnings = errors.resources.filter(row => row.tag === "IMG");
  const localImageWarnings = imageWarnings.filter(row => new URL(row.url).origin === origin);
  process.stdout.write(`Isolated network: ${blocked.size} remote URLs blocked; ${imageWarnings.length} image warnings (${localImageWarnings.length} local, zero Loveless icons); ${consoleErrors.length} expected Monaco console errors; zero runtime errors.\n`);
}

const watchdog = setTimeout(() => { console.error("Editor page test exceeded its overall time limit"); app.exit(1); }, timeoutMs * 2);
app.whenReady().then(run).then(() => finish(0), async error => {
  console.error(error.stack || error);
  if (win && !win.isDestroyed()) {
    try { console.error(JSON.stringify(await win.webContents.executeJavaScript("({ errors: window.__editorPageErrors, resources: window.__editorPageResources, status: window.getLegitBuilderDatasetStatus?.() })"))); } catch (_) { /* original error is primary */ }
  }
  console.error(JSON.stringify({ missing: [...missing], consoleErrors, blocked: [...blocked] }));
  await finish(1);
});

async function finish(code) {
  clearTimeout(watchdog);
  if (win && !win.isDestroyed()) win.destroy();
  if (server) await new Promise(resolve => server.close(resolve));
  app.exit(code);
}
