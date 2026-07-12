const { app, BrowserWindow, ipcMain, shell } = require("electron");
const fs = require("fs/promises");
const path = require("path");
const { spawn } = require("child_process");
const { pathToFileURL } = require("url");
const {
  favoritesFilePath,
  readFavorites,
  writeFavorites
} = require("./dev_spawner_favorites_store");

const REPO_ROOT = path.resolve(__dirname, "..");
const DEFAULT_BRIDGE = "http://127.0.0.1:49774";
const LATEST_MANIFEST_URL = "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/releases/latest.json";
const SMOKE_MODE = process.argv.includes("--smoke");
const MATT_EDITOR_INDEX = path.join(
  REPO_ROOT,
  "external_app",
  "v22_parts_codes_fixed",
  "matt_editor",
  "index.html"
);
const EXTERNAL_APP_DIR = path.join(REPO_ROOT, "external_app", "v22_parts_codes_fixed");
const RESOURCE_DIR = path.join(EXTERNAL_APP_DIR, "resources");
const ALLOWED_RESOURCE_FILES = new Set([
  "item_pools.json",
  "travelmaps_flat.json",
  "travelstations.json",
  "version_info.json"
]);
const LOCAL_VENV_PYTHON = path.join(REPO_ROOT, ".venv", "Scripts", "python.exe");
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

let mattHostProcess = null;
let mattHostUrl = "";

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
  out.push(LOCAL_VENV_PYTHON, "python", "py");
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
  let local = {};
  const localManifestPath = path.join(REPO_ROOT, "releases", "latest.json");
  try {
    local = JSON.parse(await fs.readFile(localManifestPath, "utf8"));
  } catch (error) {
    local = { package_version: "unknown", error: String(error && error.message ? error.message : error) };
  }

  try {
    const response = await fetch(LATEST_MANIFEST_URL, { cache: "no-store" });
    const text = await response.text();
    const remote = text ? JSON.parse(text) : {};
    const localVersion = String(local.package_version || "");
    const remoteVersion = String(remote.package_version || "");
    return {
      ok: response.ok,
      local,
      remote,
      updateAvailable: Boolean(remoteVersion && localVersion && remoteVersion !== localVersion),
      latestUrl: remote.download_url || "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest"
    };
  } catch (error) {
    return {
      ok: false,
      local,
      remote: {},
      updateAvailable: false,
      latestUrl: "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest",
      message: String(error && error.message ? error.message : error)
    };
  }
});

ipcMain.handle("app:openExternal", async (_event, url) => {
  await shell.openExternal(String(url || ""));
  return true;
});

app.whenReady().then(() => {
  if (SMOKE_MODE) {
    console.log(JSON.stringify({ ok: true, electron: process.versions.electron, bridge: DEFAULT_BRIDGE }));
    app.exit(0);
    return;
  }

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
