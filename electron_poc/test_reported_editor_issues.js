"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const os = require("node:os");
const editor = path.resolve(__dirname, "../external_app/v22_parts_codes_fixed");

async function saveTests() {
  const source = fs.readFileSync(path.join(editor, "matt_editor/js/item-editor/ui/legit-theme.js"), "utf8");
  function definition(name) {
    const start = source.indexOf(`        async function ${name}(`);
    const end = source.indexOf("\n        }", start);
    assert(start >= 0 && end > start);
    return source.slice(start, end + "\n        }".length);
  }
  for (const embedded of [true, false]) {
    for (const action of ["encryptSaveFile", "overwriteExistingSave"]) {
      const messages = [], writes = [], downloads = [];
      const context = vm.createContext({
        console: { log() {}, warn() {}, error() {} }, Blob, Uint8Array, atob, performance, DEBUG: false,
        confirm: () => true,
        window: {
          IS_ELECTRON_APP: true, // the host sets this even in a standalone browser
          saveEditorState: { originalFileName: "1.sav", originalFilePath: "C:/test/1.sav" },
          MsbtEditorPrefs: {
            inMsbtFrame: () => embedded,
            writeSavBlob: async (blob, opts) => { writes.push(opts); throw new Error("Permission denied test"); },
          },
        },
        document: {
          getElementById: () => ({ value: "76561198000000000" }),
          createElement: () => ({ click: () => downloads.push(true) }),
          body: { appendChild() {}, removeChild() {} },
        },
        URL: { createObjectURL: () => "blob:test", revokeObjectURL() {} },
        getYamlTextareaValue: () => "state: {}",
        getSaveApiBaseUrl: () => "/mock-encrypt",
        showSaveStatus: (_id, message, ok) => messages.push({ message, ok }),
        setSaveProcessingState: value => { context.window.saveEditorState.isProcessing = value; },
        fetch: async () => ({ ok: true, headers: { get: () => "application/json" }, json: async () => ({ success: true, encrypted: "dGVzdA==" }) }),
      });
      vm.runInContext(definition(action), context);
      await context[action]();
      assert.equal(context.window.saveEditorState.isProcessing, false);
      if (embedded) {
        assert.equal(writes.length, 1);
        assert.equal(downloads.length, 0, "desktop write failure must not silently download instead");
        assert(messages.at(-1).message.includes("Permission denied test"));
        assert.equal(messages.at(-1).ok, false);
      } else {
        assert.equal(writes.length, 0, "standalone editor must not request a nonexistent parent bridge");
        assert.equal(downloads.length, 1);
      }
    }
  }
}

async function desktopWriteTest() {
  const source = fs.readFileSync(path.join(__dirname, "main.js"), "utf8");
  const start = source.indexOf('ipcMain.handle("app:mattEditorSaveFile"');
  const end = source.indexOf("\n});", start) + 4;
  let handler;
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), "msbt-save-write-"));
  const target = path.join(folder, "1.sav");
  try {
    const context = vm.createContext({
      ipcMain: { handle: (_name, fn) => { handler = fn; } },
      fs: require("node:fs/promises"), path, Buffer,
      normalizePathValue: value => String(value),
      loadMattEditorPrefsData: async () => ({ data: {} }),
      steamIdFromSavePath: () => "",
      rememberMattEditorPrefs: async data => ({ data }),
      MATT_EDITOR_SAVE_MAX_BYTES: 48 * 1024 * 1024,
    });
    vm.runInContext(source.slice(start, end), context);
    fs.writeFileSync(target, "before");
    const bytes = Buffer.from([0, 1, 2, 128, 255]);
    const result = await handler({}, { overwrite: true, overwritePath: target, base64: bytes.toString("base64") });
    assert.equal(result.ok, true);
    assert.equal(result.path, target);
    assert.deepEqual(fs.readFileSync(target), bytes);
    // A file used as a parent directory forces a genuine filesystem error.
    const failure = await handler({}, { overwrite: true, overwritePath: path.join(target, "2.sav"), base64: bytes.toString("base64") });
    assert.equal(failure.ok, false);
    assert.deepEqual(fs.readFileSync(target), bytes);
  } finally {
    assert.equal(path.dirname(path.resolve(folder)), path.resolve(os.tmpdir()));
    fs.rmSync(folder, { recursive: true, force: true });
  }
}

if (!process.versions.electron) {
  Promise.all([saveTests(), desktopWriteTest()]).then(() => {
    const { spawnSync } = require("node:child_process");
    const env = { ...process.env };
    delete env.ELECTRON_RUN_AS_NODE;
    const profile = fs.mkdtempSync(path.join(os.tmpdir(), "msbt-reported-editor-"));
    env.MSBT_REPORTED_EDITOR_PROFILE = profile;
    const result = spawnSync(require("electron"), [__filename], { env, stdio: "inherit", windowsHide: true });
    assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
    fs.rmSync(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
    process.exit(result.status ?? 1);
  }).catch(error => { console.error(error); process.exit(1); });
} else {
  const { app, BrowserWindow } = require("electron");
  assert(process.env.MSBT_REPORTED_EDITOR_PROFILE);
  app.setPath("userData", process.env.MSBT_REPORTED_EDITOR_PROFILE);
  let win;
  app.whenReady().then(async () => {
    win = new BrowserWindow({ show: false, width: 1100, height: 800, webPreferences: { offscreen: true, backgroundThrottling: false, nodeIntegration: false, contextIsolation: true } });
    win.webContents.session.webRequest.onBeforeRequest((details, callback) => callback({ cancel: /^https?:/.test(details.url) }));
    await win.loadFile(path.join(editor, "matt_editor/index.html"));
    const js = code => win.webContents.executeJavaScript(code);
    await js(`window.__sent=[]; window.confirm=()=>true;
      window.fetch=async (url, opts)=>{
        if(url==='/msbt/deliver') { __sent.push(JSON.parse(opts.body)); return {ok:true,json:async()=>({ok:true,message:'Accepted test delivery'})}; }
        return {ok:true,json:async()=>({ok:true,status:{players:[]}})};
      }; void 0;`);
    await js(fs.readFileSync(path.join(editor, "matt_editor_adapter.js"), "utf8"));
    await js(`new Promise(resolve=>setTimeout(resolve,700))`);
    const serialA = "@Uaaaaaaaaaaaaaaaaaaaaaaaaa";
    const serialB = "@Ubbbbbbbbbbbbbbbbbbbbbbbbb";
    async function send(serial) {
      await js(`document.getElementById('finalOutputBase85').value=${JSON.stringify(serial)};
        document.querySelector('[data-msbt-deliver-mode="all"]').click();`);
      await js(`new Promise(resolve=>setTimeout(resolve,50))`);
    }
    await send(serialA);
    await send(serialB); // .value assignment deliberately emits no input/change event
    assert.deepEqual(await js("__sent.map(row=>row.serial)"), [serialA, serialB]);
    assert.equal(await js("document.getElementById('msbt-serial-preview').textContent.includes('@U')"), false);
    await js(`document.getElementById('msbt-delivery-toggle').click()`);
    assert.equal(await js("document.getElementById('msbt-delivery-content').hidden"), true);
    assert.equal(await js("localStorage.getItem('msbt-delivery-collapsed')"), "true");
    await js(`document.getElementById('msbt-delivery-toggle').click()`);
    assert.equal(await js("document.getElementById('msbt-delivery-content').hidden"), false);
    await js(`new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`);
    const out = path.resolve(__dirname, "../output/reported-issues");
    fs.mkdirSync(out, { recursive: true });
    fs.writeFileSync(path.join(out, "delivery-expanded.png"), (await win.webContents.capturePage()).toPNG());
    await js(`document.getElementById('msbt-delivery-toggle').click()`);
    await js(`new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))`);
    fs.writeFileSync(path.join(out, "delivery-minimized.png"), (await win.webContents.capturePage()).toPNG());
    console.log("Reported editor issues: 4 save-path cases, real temporary-file overwrite/failure, consecutive sends and minimize passed.");
    app.exit(0);
  }).catch(error => { console.error(error); app.exit(1); });
}
