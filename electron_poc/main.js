const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { execFile, spawn } = require("child_process");
const { pathToFileURL } = require("url");
const { promisify } = require("util");
const {
  favoritesFilePath,
  readFavorites,
  writeFavorites
} = require("./dev_spawner_favorites_store");
const {
  bookmarksFilePath,
  readBookmarks,
  writeBookmarks
} = require("./serial_bookmarks_store");
const {
  loadBl4Catalog
} = require("./bl4_codes_catalog");

function reportFatalStartupError(kind, error) {
  const message = error && error.stack ? error.stack : String(error);
  console.error(`[MSBT Electron] ${kind}: ${message}`);
  if (process.argv.includes("--smoke")) {
    process.exit(1);
  }
}

process.on("uncaughtException", (error) => reportFatalStartupError("uncaughtException", error));
process.on("unhandledRejection", (error) => reportFatalStartupError("unhandledRejection", error));

const execFileAsync = promisify(execFile);
const SOURCE_ROOT = path.resolve(__dirname, "..");
const RESOURCE_ROOT = app.isPackaged ? process.resourcesPath : SOURCE_ROOT;
const DEFAULT_BRIDGE = "http://127.0.0.1:49774";
const LATEST_MANIFEST_URL = "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/releases/latest.json";
const SMOKE_MODE = process.argv.includes("--smoke");
const MATT_EDITOR_INDEX = path.join(
  RESOURCE_ROOT,
  "external_app",
  "v22_parts_codes_fixed",
  "matt_editor",
  "index.html"
);
const EXTERNAL_APP_DIR = path.join(RESOURCE_ROOT, "external_app", "v22_parts_codes_fixed");
const RESOURCE_DIR = path.join(EXTERNAL_APP_DIR, "resources");
const LOCAL_MANIFEST_PATH = app.isPackaged
  ? path.join(RESOURCE_ROOT, "releases", "latest.json")
  : path.join(SOURCE_ROOT, "releases", "latest.json");
const BUNDLED_SDKMOD_PATH = app.isPackaged
  ? path.join(RESOURCE_ROOT, "sdkmod", "MattsSDKBoostingTools.sdkmod")
  : path.join(SOURCE_ROOT, "MattsSDKBoostingTools.sdkmod");
const ALLOWED_RESOURCE_FILES = new Set([
  "item_pools.json",
  "travelmaps_flat.json",
  "travelstations.json",
  "version_info.json"
]);
const LOCAL_VENV_PYTHON = path.join(SOURCE_ROOT, ".venv", "Scripts", "python.exe");
const BUNDLED_PYTHON = path.join(RESOURCE_ROOT, "python", "python.exe");
const MATT_HOST_START_TIMEOUT_MS = 12000;
const SDK_LOG_CANDIDATES = [
  process.env.MSBT_UNREALSDK_LOG,
  path.join(
    process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)",
    "Steam",
    "steamapps",
    "common",
    "Borderlands 4",
    "OakGame",
    "Binaries",
    "Win64",
    "Plugins",
    "unrealsdk.log"
  ),
  path.join(
    process.env.ProgramFiles || "C:\\Program Files",
    "Steam",
    "steamapps",
    "common",
    "Borderlands 4",
    "OakGame",
    "Binaries",
    "Win64",
    "Plugins",
    "unrealsdk.log"
  )
].filter(Boolean);
const SDK_LOG_FILTER = /MattsSDKBoostingTools|ActorScriptDeployer|ASD_|dev_spawner|spawnai|ERR\||WARN\||Traceback|Exception|did not report/i;
const BL4_SDK_MODS_CANDIDATES = [
  path.join(
    process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)",
    "Steam",
    "steamapps",
    "common",
    "Borderlands 4",
    "sdk_mods"
  ),
  path.join(
    process.env.ProgramFiles || "C:\\Program Files",
    "Steam",
    "steamapps",
    "common",
    "Borderlands 4",
    "sdk_mods"
  )
].filter(Boolean);

let mattHostProcess = null;
let mattHostUrl = "";
let autoUpdater = null;
let autoUpdaterConfigured = false;
let latestUpdateState = {
  status: "idle",
  message: "No Electron updater check has run yet.",
  updateInfo: null,
  progress: null,
  error: ""
};

function updateState(patch) {
  latestUpdateState = { ...latestUpdateState, ...patch };
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send("app:updateState", latestUpdateState);
  }
}

function configureAutoUpdater() {
  if (autoUpdaterConfigured) return Boolean(autoUpdater);
  autoUpdaterConfigured = true;

  try {
    ({ autoUpdater } = require("electron-updater"));
    autoUpdater.autoDownload = false;
    autoUpdater.allowDowngrade = false;
  } catch (error) {
    updateState({
      status: "error",
      message: "Electron updater is not available in this build.",
      error: String(error && error.message ? error.message : error)
    });
    return false;
  }

  autoUpdater.on("checking-for-update", () => {
    updateState({ status: "checking", message: "Checking Electron installer updates...", error: "" });
  });
  autoUpdater.on("update-available", (info) => {
    updateState({ status: "available", message: `Electron update available: ${info && info.version ? info.version : "new version"}.`, updateInfo: info, error: "" });
  });
  autoUpdater.on("update-not-available", (info) => {
    updateState({ status: "none", message: "No Electron installer update is available.", updateInfo: info, error: "" });
  });
  autoUpdater.on("download-progress", (progress) => {
    updateState({ status: "progress", message: "Downloading Electron update...", progress, error: "" });
  });
  autoUpdater.on("update-downloaded", (info) => {
    updateState({ status: "downloaded", message: "Electron update downloaded. Restart when ready to install.", updateInfo: info, error: "" });
  });
  autoUpdater.on("error", (error) => {
    updateState({ status: "error", message: "Electron update check failed.", error: String(error && error.message ? error.message : error) });
  });

  return true;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1500,
    height: 940,
    minWidth: 1120,
    minHeight: 760,
    backgroundColor: "#090d17",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  win.loadFile(path.join(__dirname, "renderer.html"));
}

async function requestBridge({ method = "GET", path: route = "/status", payload = null, timeoutMs = 8000 }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const body = payload === null || payload === undefined ? undefined : JSON.stringify(payload);
    const response = await fetch(DEFAULT_BRIDGE + route, {
      method,
      headers: { "Content-Type": "application/json" },
      body,
      signal: controller.signal
    });
    const text = await response.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { ok: response.ok, message: text };
    }
    return { ok: response.ok, status: response.status, data };
  } catch (error) {
    return { ok: false, status: 0, data: { ok: false, message: String(error && error.message ? error.message : error) } };
  } finally {
    clearTimeout(timer);
  }
}

ipcMain.handle("bridge:request", async (_event, args) => requestBridge(args || {}));

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJsonFile(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

async function safeFileHash(filePath) {
  try {
    const { createHash } = require("crypto");
    const data = await fs.readFile(filePath);
    return createHash("sha256").update(data).digest("hex");
  } catch {
    return "";
  }
}

async function bundledSdkmodInfo() {
  const available = await fileExists(BUNDLED_SDKMOD_PATH);
  return {
    available,
    path: BUNDLED_SDKMOD_PATH,
    sha256: available ? await safeFileHash(BUNDLED_SDKMOD_PATH) : "",
    status: available ? "bundled" : "missing",
    message: available
      ? "Bundled MattsSDKBoostingTools.sdkmod is available in this app build."
      : "Bundled MattsSDKBoostingTools.sdkmod is missing from this app build."
  };
}

async function installedSdkmodInfo(destination, bundledHash = "") {
  const installed = await fileExists(destination);
  if (!installed) {
    return {
      available: false,
      path: destination,
      sha256: "",
      status: "missing",
      matchesBundled: false,
      message: "No installed MattsSDKBoostingTools.sdkmod found at this sdk_mods path."
    };
  }

  const sha256 = await safeFileHash(destination);
  const matchesBundled = Boolean(bundledHash && sha256 && sha256 === bundledHash);
  const status = matchesBundled ? "current" : bundledHash ? "different" : "detected";
  return {
    available: true,
    path: destination,
    sha256,
    status,
    matchesBundled,
    message: matchesBundled
      ? "Installed SDK mod matches the bundled Electron beta SDK mod."
      : bundledHash
        ? "Installed SDK mod differs from the bundled Electron beta SDK mod."
        : "Installed SDK mod was detected; bundled comparison is unavailable."
  };
}

async function detectInstalledSdkmodInfo(bundledHash = "") {
  for (const candidate of BL4_SDK_MODS_CANDIDATES) {
    const info = await sdkModsPathInfo(candidate, bundledHash);
    if (info.ok || (info.installedSdkmod && info.installedSdkmod.available)) {
      return { ...info.installedSdkmod, sdkModsPath: info.path };
    }
  }
  return {
    available: false,
    path: "",
    sdkModsPath: "",
    sha256: "",
    status: "not_detected",
    matchesBundled: false,
    message: "No Borderlands 4 sdk_mods folder was auto-detected."
  };
}

async function localVersionInfo() {
  let manifest = {};
  try {
    manifest = await readJsonFile(LOCAL_MANIFEST_PATH);
  } catch (error) {
    manifest = { package_version: "unknown", error: String(error && error.message ? error.message : error) };
  }
  const bundledSdkmod = await bundledSdkmodInfo();
  const installedSdkmod = await detectInstalledSdkmodInfo(bundledSdkmod.sha256);
  return {
    ok: true,
    appVersion: app.getVersion(),
    electronVersion: process.versions.electron,
    platform: process.platform,
    osRelease: os.release(),
    packageVersion: manifest.package_version || manifest.app_version || app.getVersion(),
    sdkmodVersion: manifest.sdkmod_version || "unavailable",
    resourcesVersion: manifest.resources_version || "unavailable",
    sdkRequired: manifest.sdk_required || "oak2-mod-manager v0.3",
    sdkRequiredUrl: manifest.sdk_required_url || "https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3",
    packaged: app.isPackaged,
    localManifest: manifest,
    bundledSdkmod,
    installedSdkmod,
    updateState: latestUpdateState
  };
}

ipcMain.handle("app:getVersionInfo", async () => localVersionInfo());

async function isBorderlandsRunning() {
  if (process.platform !== "win32") return false;
  try {
    const { stdout } = await execFileAsync("tasklist.exe", ["/FI", "IMAGENAME eq Borderlands4.exe", "/FO", "CSV", "/NH"], {
      windowsHide: true
    });
    return /Borderlands4\.exe/i.test(stdout || "");
  } catch {
    return false;
  }
}

function normalizeSdkModsPath(rawPath) {
  const value = String(rawPath || "").trim();
  if (!value) return "";
  return path.resolve(value);
}

async function sdkModsPathInfo(rawPath, bundledHash = "") {
  const sdkModsPath = normalizeSdkModsPath(rawPath);
  if (!sdkModsPath) return { ok: false, message: "No sdk_mods path was provided." };
  const baseName = path.basename(sdkModsPath).toLowerCase();
  if (baseName !== "sdk_mods") {
    return { ok: false, path: sdkModsPath, message: "Choose the Borderlands 4 sdk_mods folder." };
  }
  const exists = await fileExists(sdkModsPath);
  const destination = path.join(sdkModsPath, "MattsSDKBoostingTools.sdkmod");
  const bundledSha = bundledHash || (await bundledSdkmodInfo()).sha256;
  return {
    ok: exists,
    path: sdkModsPath,
    destination,
    installedSdkmod: await installedSdkmodInfo(destination, bundledSha),
    message: exists ? "sdk_mods folder found." : "sdk_mods folder does not exist."
  };
}

ipcMain.handle("app:detectSdkMods", async () => {
  for (const candidate of BL4_SDK_MODS_CANDIDATES) {
    const info = await sdkModsPathInfo(candidate);
    if (info.ok) return info;
  }
  return {
    ok: false,
    path: "",
    message: "Could not auto-detect Borderlands 4 sdk_mods. Paste or browse to the sdk_mods folder."
  };
});

ipcMain.handle("app:browseSdkMods", async () => {
  const result = await dialog.showOpenDialog({
    title: "Choose the Borderlands 4 sdk_mods folder",
    properties: ["openDirectory"]
  });
  if (result.canceled || !result.filePaths.length) {
    return { ok: false, canceled: true, message: "No sdk_mods folder selected." };
  }
  return sdkModsPathInfo(result.filePaths[0]);
});

ipcMain.handle("app:installSdkMod", async (_event, rawPath) => {
  const sourceExists = await fileExists(BUNDLED_SDKMOD_PATH);
  if (!sourceExists) {
    return { ok: false, message: "Bundled MattsSDKBoostingTools.sdkmod was not found in this app build." };
  }
  if (await isBorderlandsRunning()) {
    return { ok: false, message: "Borderlands4.exe is running. Close the game before installing or updating the SDK mod." };
  }
  const info = await sdkModsPathInfo(rawPath);
  if (!info.ok) return info;
  await fs.mkdir(info.path, { recursive: true });
  await fs.copyFile(BUNDLED_SDKMOD_PATH, info.destination);
  const bundled = await bundledSdkmodInfo();
  return {
    ok: true,
    path: info.path,
    destination: info.destination,
    sha256: await safeFileHash(info.destination),
    installedSdkmod: await installedSdkmodInfo(info.destination, bundled.sha256),
    message: "MattsSDKBoostingTools.sdkmod installed/updated. Restart Borderlands 4 if it was open."
  };
});

ipcMain.handle("app:readResourceJson", async (_event, resourceName) => {
  const name = path.basename(String(resourceName || ""));
  if (!ALLOWED_RESOURCE_FILES.has(name)) {
    return { ok: false, message: `Resource is not allowlisted: ${name}` };
  }
  try {
    const text = await fs.readFile(path.join(RESOURCE_DIR, name), "utf8");
    return { ok: true, name, data: JSON.parse(text) };
  } catch (error) {
    return { ok: false, name, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:readDevSpawnerCatalog", async () => {
  const catalogPath = path.join(__dirname, "dev_spawner_catalog.json");
  try {
    const text = await fs.readFile(catalogPath, "utf8");
    return { ok: true, data: JSON.parse(text) };
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:loadDevSpawnerFavorites", async () => {
  const filePath = favoritesFilePath(app.getPath("userData"));
  return readFavorites(filePath);
});

ipcMain.handle("app:saveDevSpawnerFavorites", async (_event, payload) => {
  const filePath = favoritesFilePath(app.getPath("userData"));
  try {
    return await writeFavorites(filePath, payload || {});
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:loadSerialBookmarks", async () => {
  const filePath = bookmarksFilePath(app.getPath("userData"));
  return readBookmarks(filePath);
});

ipcMain.handle("app:saveSerialBookmarks", async (_event, payload) => {
  const filePath = bookmarksFilePath(app.getPath("userData"));
  try {
    return await writeBookmarks(filePath, payload || {});
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:loadBl4Catalog", async () => {
  try {
    return await loadBl4Catalog(RESOURCE_DIR);
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:bl4PartsBreakdown", async (_event, serial) => {
  const code = [
    "import json, sys",
    "import external_serial_tools",
    "value = sys.stdin.read()",
    "try:",
    "    text = external_serial_tools.serial_parts_breakdown_for_value(value)",
    "    print(json.dumps({'ok': True, 'breakdown': text}))",
    "except Exception as exc:",
    "    print(json.dumps({'ok': False, 'message': str(exc), 'breakdown': ''}))"
  ].join("\n");
  return runExternalPythonJson(code, serial, 20000);
});

async function findSdkLogPath() {
  for (const candidate of SDK_LOG_CANDIDATES) {
    try {
      const stat = await fs.stat(candidate);
      if (stat.isFile()) return candidate;
    } catch {
      // Try the next common install path.
    }
  }
  return "";
}

async function readTextTail(filePath, maxBytes = 200000) {
  const handle = await fs.open(filePath, "r");
  try {
    const stat = await handle.stat();
    const length = Math.min(stat.size, maxBytes);
    const buffer = Buffer.alloc(length);
    await handle.read(buffer, 0, length, Math.max(0, stat.size - length));
    return buffer.toString("utf8");
  } finally {
    await handle.close();
  }
}

ipcMain.handle("app:readSdkLogTail", async (_event, options = {}) => {
  const logPath = await findSdkLogPath();
  if (!logPath) {
    return {
      ok: false,
      message: `unrealsdk.log was not found. Checked: ${SDK_LOG_CANDIDATES.join("; ")}`
    };
  }

  try {
    const requestedLines = Number(options && options.lines) || 140;
    const maxLines = Math.max(20, Math.min(400, requestedLines));
    const text = await readTextTail(logPath);
    const lines = text
      .split(/\r?\n/)
      .filter((line) => SDK_LOG_FILTER.test(line))
      .slice(-maxLines);
    return {
      ok: true,
      path: logPath,
      lines,
      text: lines.join("\n") || "No recent MSBT/ActorScriptDeployer log lines found."
    };
  } catch (error) {
    return {
      ok: false,
      path: logPath,
      message: String(error && error.message ? error.message : error)
    };
  }
});

ipcMain.handle("app:serialToolsConvert", async (_event, text) => {
  const code = [
    "import json, sys",
    "import external_serial_tools",
    "result = external_serial_tools.convert_serial_tool(sys.stdin.read())",
    "print(json.dumps(result))"
  ].join("\n");
  return runExternalPythonJson(code, text, 15000);
});

ipcMain.handle("app:validatorBasic", async (_event, text) => {
  const code = [
    "import json, sys",
    "import external_validator",
    "result = external_validator.validate_basic_input(sys.stdin.read())",
    "print(json.dumps(result, default=str))"
  ].join("\n");
  return runExternalPythonJson(code, text, 20000);
});

ipcMain.handle("app:validatorBulk", async (_event, text) => {
  const code = [
    "import json, sys",
    "import external_validator",
    "result = external_validator.validate_bulk_input(sys.stdin.read())",
    "print(json.dumps(result, default=str))"
  ].join("\n");
  return runExternalPythonJson(code, text, 60000);
});

function pythonCandidates() {
  const out = [];
  if (process.env.MSBT_PYTHON) out.push(process.env.MSBT_PYTHON);
  out.push(app.isPackaged ? BUNDLED_PYTHON : LOCAL_VENV_PYTHON, "python", "py");
  return Array.from(new Set(out.filter(Boolean)));
}

function runPythonSnippet(pythonExe, code, inputText = "", timeoutMs = 15000) {
  const args = pythonExe === "py" ? ["-3", "-c", code] : ["-c", code];
  const child = spawn(pythonExe, args, {
    cwd: EXTERNAL_APP_DIR,
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: true
  });

  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`Timed out running helper with ${pythonExe}. ${stderr.trim()}`.trim()));
    }, timeoutMs);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("exit", (codeNumber) => {
      clearTimeout(timer);
      if (codeNumber === 0) {
        resolve(stdout.trim());
      } else {
        reject(new Error(stderr.trim() || `Helper exited with code ${codeNumber}`));
      }
    });

    child.stdin.end(String(inputText || ""));
  });
}

async function runExternalPythonJson(code, inputText = "", timeoutMs = 15000) {
  const errors = [];
  for (const candidate of pythonCandidates()) {
    try {
      const stdout = await runPythonSnippet(candidate, code, inputText, timeoutMs);
      return JSON.parse(stdout || "{}");
    } catch (error) {
      errors.push(`${candidate}: ${error && error.message ? error.message : error}`);
    }
  }
  return { ok: false, message: errors.join("\n") };
}

function hostProcessIsAlive() {
  return mattHostProcess && mattHostProcess.exitCode === null && !mattHostProcess.killed;
}

function startHostWithPython(pythonExe) {
  const code = [
    "import sys, time",
    `sys.path.insert(0, ${JSON.stringify(EXTERNAL_APP_DIR)})`,
    "import matt_editor_host",
    "url = matt_editor_host.start_editor_host()",
    "print(url, flush=True)",
    "try:",
    "    while True:",
    "        time.sleep(3600)",
    "except KeyboardInterrupt:",
    "    pass",
    "finally:",
    "    matt_editor_host.stop_editor_host()"
  ].join("\n");
  const args = pythonExe === "py" ? ["-3", "-c", code] : ["-c", code];
  const child = spawn(pythonExe, args, {
    cwd: EXTERNAL_APP_DIR,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true
  });

  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`Timed out starting Matt editor host with ${pythonExe}. ${stderr.trim()}`.trim()));
    }, MATT_HOST_START_TIMEOUT_MS);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
      const match = stdout.match(/https?:\/\/127\.0\.0\.1:\d+\/?/);
      if (!match) return;
      clearTimeout(timer);
      mattHostProcess = child;
      mattHostUrl = match[0].endsWith("/") ? match[0] : `${match[0]}/`;
      resolve(mattHostUrl);
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });

    child.on("exit", (codeNumber, signal) => {
      if (mattHostProcess === child) {
        mattHostProcess = null;
        mattHostUrl = "";
      }
      if (!stdout.match(/https?:\/\/127\.0\.0\.1:\d+\/?/)) {
        clearTimeout(timer);
        reject(new Error(`Matt editor host exited (${codeNumber || signal || "unknown"}). ${stderr.trim()}`.trim()));
      }
    });
  });
}

async function startMattEditorHost() {
  if (hostProcessIsAlive() && mattHostUrl) return mattHostUrl;

  const errors = [];
  for (const candidate of pythonCandidates()) {
    try {
      return await startHostWithPython(candidate);
    } catch (error) {
      errors.push(`${candidate}: ${error && error.message ? error.message : error}`);
    }
  }
  throw new Error(errors.join("\n"));
}

ipcMain.handle("app:mattEditorUrl", async () => {
  try {
    const url = await startMattEditorHost();
    return { ok: true, url, hosted: true, message: "Loaded hosted Matt editor with MSBT delivery adapter." };
  } catch (error) {
    return {
      ok: false,
      url: pathToFileURL(MATT_EDITOR_INDEX).toString(),
      hosted: false,
      message: `Hosted Matt editor failed; falling back to raw file view. ${error && error.message ? error.message : error}`
    };
  }
});

ipcMain.handle("app:checkUpdates", async () => {
  const versionInfo = await localVersionInfo();
  const local = versionInfo.localManifest || {};

  try {
    const response = await fetch(LATEST_MANIFEST_URL, { cache: "no-store" });
    const text = await response.text();
    const remote = text ? JSON.parse(text) : {};
    const localVersion = String(local.package_version || "");
    const remoteVersion = String(remote.package_version || "");
    let updater = latestUpdateState;
    if (app.isPackaged) {
      try {
        if (configureAutoUpdater()) {
          updateState({ status: "checking", message: "Checking Electron installer updates...", error: "" });
          const updaterResult = await autoUpdater.checkForUpdates();
          updater = { ...latestUpdateState, updateInfo: updaterResult && updaterResult.updateInfo ? updaterResult.updateInfo : latestUpdateState.updateInfo };
        } else {
          updater = latestUpdateState;
        }
      } catch (error) {
        updater = {
          ...latestUpdateState,
          status: "error",
          message: "Electron updater check failed.",
          error: String(error && error.message ? error.message : error)
        };
        updateState(updater);
      }
    }
    return {
      ok: response.ok,
      local,
      remote,
      appVersion: app.getVersion(),
      packageVersion: versionInfo.packageVersion,
      sdkmodVersion: versionInfo.sdkmodVersion,
      resourcesVersion: versionInfo.resourcesVersion,
      sdkRequired: versionInfo.sdkRequired,
      bundledSdkmod: versionInfo.bundledSdkmod,
      installedSdkmod: versionInfo.installedSdkmod,
      updater,
      updateAvailable: Boolean(remoteVersion && localVersion && remoteVersion !== localVersion),
      latestUrl: remote.electron_installer_download_url || remote.download_url || "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest",
      electronInstallerUrl: remote.electron_installer_download_url || "",
      manualZipUrl: remote.manual_zip_download_url || remote.download_url || ""
    };
  } catch (error) {
    return {
      ok: false,
      local,
      remote: {},
      appVersion: app.getVersion(),
      packageVersion: versionInfo.packageVersion,
      sdkmodVersion: versionInfo.sdkmodVersion,
      resourcesVersion: versionInfo.resourcesVersion,
      sdkRequired: versionInfo.sdkRequired,
      bundledSdkmod: versionInfo.bundledSdkmod,
      installedSdkmod: versionInfo.installedSdkmod,
      updater: latestUpdateState,
      updateAvailable: false,
      latestUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest",
      electronInstallerUrl: "",
      manualZipUrl: "",
      message: String(error && error.message ? error.message : error)
    };
  }
});

ipcMain.handle("app:downloadUpdate", async () => {
  if (!app.isPackaged) {
    return { ok: false, message: "Electron updater downloads are only available in an installed/package build." };
  }
  if (!configureAutoUpdater()) {
    return { ok: false, message: latestUpdateState.message || "Electron updater is not available.", state: latestUpdateState };
  }
  try {
    const result = await autoUpdater.downloadUpdate();
    return { ok: true, message: "Update download started.", result, state: latestUpdateState };
  } catch (error) {
    const message = String(error && error.message ? error.message : error);
    updateState({ status: "error", message: "Update download failed.", error: message });
    return { ok: false, message };
  }
});

ipcMain.handle("app:quitAndInstallUpdate", async () => {
  if (latestUpdateState.status !== "downloaded") {
    return { ok: false, message: "No downloaded Electron update is ready to install." };
  }
  if (!configureAutoUpdater()) {
    return { ok: false, message: latestUpdateState.message || "Electron updater is not available.", state: latestUpdateState };
  }
  autoUpdater.quitAndInstall(false, true);
  return { ok: true, message: "Restarting to install update." };
});

ipcMain.handle("app:saveReportFile", async (_event, text) => {
  const content = String(text || "").slice(0, 64000);
  if (!content.trim()) return { ok: false, message: "Report is empty." };
  const result = await dialog.showSaveDialog({
    title: "Save MSBT report",
    defaultPath: `MSBT_Report_${new Date().toISOString().slice(0, 10)}.md`,
    filters: [
      { name: "Markdown", extensions: ["md"] },
      { name: "Text", extensions: ["txt"] }
    ]
  });
  if (result.canceled || !result.filePath) {
    return { ok: false, canceled: true, message: "Save cancelled." };
  }
  await fs.writeFile(result.filePath, content, "utf8");
  return { ok: true, path: result.filePath, message: "Report saved." };
});

ipcMain.handle("app:openExternal", async (_event, url) => {
  await shell.openExternal(String(url || ""));
  return true;
});

app.whenReady().then(() => {
  app.setAppUserModelId("com.funkyoushift.msbt.electronbeta");
  if (SMOKE_MODE) {
    console.log(JSON.stringify({
      ok: true,
      appVersion: app.getVersion(),
      packaged: app.isPackaged,
      electron: process.versions.electron,
      bridge: DEFAULT_BRIDGE
    }));
    app.exit(0);
    return;
  }

  configureAutoUpdater();
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  if (hostProcessIsAlive()) {
    mattHostProcess.kill();
  }
});
