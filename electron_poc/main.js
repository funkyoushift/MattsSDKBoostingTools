const { app, BrowserWindow, dialog, ipcMain, screen, shell } = require("electron");
const fsSync = require("fs");
const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { execFile, spawn } = require("child_process");
const { Blob } = require("buffer");
const { pathToFileURL } = require("url");
const { promisify } = require("util");
const { bindWindowState } = require("./window_state_tracker");
const {
  favoritesFilePath,
  readFavorites,
  writeFavorites
} = require("./dev_spawner_favorites_store");
const {
  favoritesFilePath: travelFavoritesFilePath,
  readFavorites: readTravelFavorites,
  writeFavorites: writeTravelFavorites
} = require("./travel_favorites_store");
const {
  bookmarksFilePath,
  readBookmarks,
  writeBookmarks
} = require("./serial_bookmarks_store");
const {
  movementSettingsFilePath,
  readMovementSettings,
  writeMovementSettings
} = require("./movement_settings_store");
const {
  raritySettingsFilePath,
  readRaritySettings,
  writeRaritySettings
} = require("./rarity_settings_store");
const {
  walkthroughSettingsFilePath,
  readWalkthroughSettings,
  writeWalkthroughSettings
} = require("./walkthrough_store");
const {
  prefsFilePath: mattEditorPrefsFilePath,
  readPrefs: readMattEditorPrefs,
  writePrefs: writeMattEditorPrefs,
  normalizePathValue,
  allowedSaveExtension,
  folderFromFile,
  steamIdFromSavePath
} = require("./matt_editor_prefs_store");
const {
  loadBl4Catalog,
  refreshGzoCatalog
} = require("./bl4_codes_catalog");
const {
  DEFAULT_MANIFEST_URLS,
  KNOWN_FILES,
  cachedFilePath,
  dataCacheDir,
  defaultDocsDataDir,
  getDataCatalogStatus,
  isElectronResourceFile,
  loadTutorialCopy,
  readCatalogJson,
  refreshRemoteDataCatalogs,
  resolveCatalogFileMap
} = require("./remote_data_catalogs");
const {
  createMobileGateway,
  DEFAULT_PORT: MOBILE_GATEWAY_PORT,
  generatePairingCode
} = require("./mobile_gateway");
const oak2Install = require("./oak2_install");
const { MAX_OUTPUT_BYTES, PersistentPythonWorker } = require("./python_worker");

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
const MOBILE_PAIRING_FILE = () => path.join(app.getPath("userData"), "mobile_gateway_pairing.json");
const mobileGateway = createMobileGateway({
  port: MOBILE_GATEWAY_PORT,
  bridgeBase: DEFAULT_BRIDGE,
  pairingCode: generatePairingCode(),
  getSerialBookmarks: async () => {
    try {
      // readBookmarks() returns { ok, data: { version, bookmarks }, warnings }
      const result = await readBookmarks(bookmarksFilePath(app.getPath("userData")));
      const bookmarks = result && result.data && Array.isArray(result.data.bookmarks)
        ? result.data.bookmarks
        : [];
      return bookmarks;
    } catch (error) {
      return [];
    }
  }
});
const LATEST_MANIFEST_URL = "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/latest.json";
const FALLBACK_LATEST_MANIFEST_URL = "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/docs/releases/latest.json";
const CODES_API = "https://save-editor.be/GZO/Borderlands4/codes/api.php";
const SMOKE_MODE = process.argv.includes("--smoke");
const FORCE_TOUR = process.argv.includes("--force-tour");
const INSTALL_SDKMODS_AND_EXIT = process.argv.includes("--install-sdkmods-and-exit");
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
const BUNDLED_ACTOR_SCRIPT_DEPLOYER_PATH = app.isPackaged
  ? path.join(RESOURCE_ROOT, "sdkmods", "ActorScriptDeployer")
  : path.join(SOURCE_ROOT, "tools", "third_party", "sdk_mods", "ActorScriptDeployer");
const ALLOWED_RESOURCE_FILES = new Set([
  "item_pools.json",
  "travelmaps_flat.json",
  "travelstations.json",
  "gzo_parts_map.json",
  "shiny_serials.json",
  "challenge_catalog.json",
  "dev_spawner_catalog.json",
  "version_info.json"
]);
const DOCS_DATA_DIR = app.isPackaged
  ? path.join(RESOURCE_ROOT, "docs", "data")
  : defaultDocsDataDir(SOURCE_ROOT);
const MOD_DATA_DIR = app.isPackaged
  ? path.join(RESOURCE_ROOT, "sdkmod_data")
  : path.join(SOURCE_ROOT, "mod_extracted", "MattsSDKBoostingTools");
const ELECTRON_APP_DIR = __dirname;
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
const BL4_DEFAULT_SDK_MODS_CANDIDATES = oak2Install.bl4SdkModsCandidates();
const USER_DATA_FILE_DEFINITIONS = [
  { key: "serialBookmarks", label: "Serial Bookmarks", fileName: "serial_bookmarks.json" },
  { key: "devSpawnerFavorites", label: "Dev Spawner Favorites", fileName: "dev_spawner_favorites.json" },
  { key: "travelFavorites", label: "Travel Favorites", fileName: "travel_favorites.json" },
  { key: "movementSettings", label: "Movement Presets", fileName: "movement_settings.json" },
  { key: "raritySettings", label: "Rarity Presets", fileName: "rarity_settings.json" },
  { key: "walkthroughSettings", label: "Walkthrough Prefs", fileName: "walkthrough_settings.json" },
  { key: "mattEditorPrefs", label: "Matt Editor Steam ID / Folders", fileName: "matt_editor_prefs.json" },
  { key: "windowState", label: "Window Size / Position / Opacity", fileName: "window-state.json" }
];

function bl4GzoCacheFilePath() {
  return path.join(app.getPath("userData"), "bl4_gzo_codes.json");
}

function dataCatalogOptions() {
  return {
    resourceDir: RESOURCE_DIR,
    docsDataDir: DOCS_DATA_DIR,
    modDataDir: MOD_DATA_DIR,
    electronAppDir: ELECTRON_APP_DIR,
    gzoLiveCachePath: bl4GzoCacheFilePath()
  };
}

function broadcastDataCatalogEvent(channel, payload) {
  for (const win of BrowserWindow.getAllWindows()) {
    if (win && !win.isDestroyed() && win.webContents) {
      win.webContents.send(channel, payload);
    }
  }
}

async function bl4CatalogLoadOptions() {
  const resolved = await resolveCatalogFileMap(app.getPath("userData"), dataCatalogOptions());
  return {
    gzoCachePath: bl4GzoCacheFilePath(),
    filePaths: {
      lootlemon: resolved.paths.lootlemon || undefined,
      custom: resolved.paths.custom_bl4_codes || undefined,
      custom_bl4_codes: resolved.paths.custom_bl4_codes || undefined,
      gzo: resolved.paths.gzo_codes || undefined,
      gzo_codes: resolved.paths.gzo_codes || undefined
    },
    sources: resolved.sources
  };
}

function gzoGithubFallbackUrls() {
  const urls = [];
  const cachedGzo = cachedFilePath(app.getPath("userData"), KNOWN_FILES.gzo_codes);
  // Prefer already-cached GitHub snapshot path via file URL only when fetchable remotely.
  urls.push(
    "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/docs/data/MattsSDKBoostingTools_gzo_codes.json"
  );
  if (fsSync.existsSync(cachedGzo)) {
    // Local snapshot is applied by loadBl4Catalog via filePaths; keep URL list remote-only.
  }
  return urls;
}

async function softRefreshDataCatalogs(options = {}) {
  const quiet = Boolean(options.quiet);
  try {
    const localManifestUrl = pathToFileURL(path.join(DOCS_DATA_DIR, "catalog_manifest.json")).href;
    const result = await refreshRemoteDataCatalogs({
      userDataPath: app.getPath("userData"),
      docsDataDir: DOCS_DATA_DIR,
      localSeedDir: DOCS_DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR,
      quiet,
      retries: Number.isFinite(options.retries) ? options.retries : 3,
      manifestUrls: app.isPackaged
        ? DEFAULT_MANIFEST_URLS
        : [localManifestUrl, ...DEFAULT_MANIFEST_URLS],
      onProgress: (progress) => {
        broadcastDataCatalogEvent("app:dataCatalogProgress", progress || {});
      }
    });
    broadcastDataCatalogEvent("app:dataCatalogRefreshed", result || {});
    return result;
  } catch (error) {
    const result = {
      ok: false,
      soft: true,
      quiet,
      message: String(error && error.message ? error.message : error),
      checkedAt: new Date().toISOString()
    };
    broadcastDataCatalogEvent("app:dataCatalogRefreshed", result);
    return result;
  }
}

function uniquePaths(paths) {
  const seen = new Set();
  const out = [];
  for (const value of paths) {
    const raw = String(value || "").trim();
    if (!raw) continue;
    const resolved = path.resolve(raw);
    const key = process.platform === "win32" ? resolved.toLowerCase() : resolved;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(resolved);
  }
  return out;
}

function bl4SdkModsCandidates() {
  return uniquePaths([
    ...BL4_DEFAULT_SDK_MODS_CANDIDATES,
    ...oak2Install.bl4SdkModsCandidates()
  ]);
}

let mattHostProcess = null;
let mattHostUrl = "";
let pythonHelperWorker = null;
let autoUpdater = null;
let autoUpdaterConfigured = false;
let latestUpdateState = {
  status: "idle",
  message: "No Electron updater check has run yet.",
  updateInfo: null,
  progress: null,
  error: ""
};

const DEFAULT_WINDOW_BOUNDS = {
  width: 1280,
  height: 820,
  // Floor high enough to stay usable; still allows 1080p half-screen (~960 CSS px).
  // Tobgun-style 2560×1440 @ 150% half-snap (~853) clamps slightly wider than true half.
  minWidth: 960,
  minHeight: 700
};
const DEFAULT_WINDOW_OPACITY = 1;
const MIN_WINDOW_OPACITY = 0.35;

function clampWindowOpacity(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return DEFAULT_WINDOW_OPACITY;
  return Math.max(MIN_WINDOW_OPACITY, Math.min(1, number));
}

function windowStatePath() {
  return path.join(app.getPath("userData"), "window-state.json");
}

function primaryWorkAreaSize() {
  try {
    const area = screen.getPrimaryDisplay().workAreaSize;
    return {
      width: Number(area && area.width) || DEFAULT_WINDOW_BOUNDS.width,
      height: Number(area && area.height) || DEFAULT_WINDOW_BOUNDS.height
    };
  } catch {
    return { width: DEFAULT_WINDOW_BOUNDS.width, height: DEFAULT_WINDOW_BOUNDS.height };
  }
}

function defaultWindowSizeForDisplay() {
  const work = primaryWorkAreaSize();
  return {
    width: Math.min(
      DEFAULT_WINDOW_BOUNDS.width,
      Math.max(DEFAULT_WINDOW_BOUNDS.minWidth, Math.floor(work.width * 0.72))
    ),
    height: Math.min(
      DEFAULT_WINDOW_BOUNDS.height,
      Math.max(DEFAULT_WINDOW_BOUNDS.minHeight, Math.floor(work.height * 0.85))
    )
  };
}

function displaySizeForBounds(bounds) {
  // Snapped windows carry invisible resize borders that overhang the work area
  // (a 1440p half-snap reports 1294x1399 against a 1392px work area), so the
  // saved size is clamped against the full display it lives on, not the primary
  // work area. Otherwise every restore shaves the window a few pixels.
  try {
    if (
      bounds &&
      Number.isFinite(bounds.x) &&
      Number.isFinite(bounds.y) &&
      Number.isFinite(bounds.width) &&
      Number.isFinite(bounds.height)
    ) {
      const match = screen.getDisplayMatching({
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height
      });
      if (match && match.bounds) return { width: match.bounds.width, height: match.bounds.height };
    }
    const primary = screen.getPrimaryDisplay();
    if (primary && primary.bounds) return { width: primary.bounds.width, height: primary.bounds.height };
  } catch {
    // Fall through to the work-area estimate below.
  }
  return primaryWorkAreaSize();
}

function sanitizeWindowSize(width, height, { maximized = false, x, y } = {}) {
  const limit = displaySizeForBounds({ x, y, width, height });
  const defaults = defaultWindowSizeForDisplay();
  const rawWidth = Number.isFinite(width) ? width : defaults.width;
  const rawHeight = Number.isFinite(height) ? height : defaults.height;

  let nextWidth = Math.max(DEFAULT_WINDOW_BOUNDS.minWidth, Math.min(rawWidth, limit.width));
  let nextHeight = Math.max(DEFAULT_WINDOW_BOUNDS.minHeight, Math.min(rawHeight, limit.height));

  // Reject postage-stamp restores from older lower floors (e.g. minWidth 880) or bad snaps.
  // Maximized windows keep restored size; maximize() fills the display.
  if (!maximized) {
    const wasBelowFloor =
      (Number.isFinite(width) && width < DEFAULT_WINDOW_BOUNDS.minWidth) ||
      (Number.isFinite(height) && height < DEFAULT_WINDOW_BOUNDS.minHeight);
    const stuckAtFloor =
      nextWidth <= DEFAULT_WINDOW_BOUNDS.minWidth + 4 &&
      nextHeight <= DEFAULT_WINDOW_BOUNDS.minHeight + 4;
    if (wasBelowFloor || stuckAtFloor) {
      nextWidth = defaults.width;
      nextHeight = defaults.height;
    }
  }

  return { width: nextWidth, height: nextHeight };
}

function readWindowState() {
  const defaults = defaultWindowSizeForDisplay();
  try {
    const parsed = JSON.parse(fsSync.readFileSync(windowStatePath(), "utf8"));
    const bounds = parsed && typeof parsed === "object" ? parsed.bounds || {} : {};
    const maximized = Boolean(parsed.maximized);
    const sized = sanitizeWindowSize(bounds.width, bounds.height, {
      maximized,
      x: bounds.x,
      y: bounds.y
    });
    const state = {
      width: sized.width,
      height: sized.height,
      maximized,
      opacity: clampWindowOpacity(parsed.opacity)
    };
    if (Number.isFinite(bounds.x) && Number.isFinite(bounds.y)) {
      state.x = bounds.x;
      state.y = bounds.y;
    }
    return state;
  } catch {
    return {
      width: defaults.width,
      height: defaults.height,
      maximized: false,
      opacity: DEFAULT_WINDOW_OPACITY
    };
  }
}

function ensureWindowOnScreen(bounds) {
  const displays = screen.getAllDisplays();
  const isVisible = displays.some((display) => {
    const area = display.workArea;
    return (
      bounds.x !== undefined &&
      bounds.y !== undefined &&
      bounds.x < area.x + area.width &&
      bounds.x + bounds.width > area.x &&
      bounds.y < area.y + area.height &&
      bounds.y + bounds.height > area.y
    );
  });
  if (isVisible) return bounds;
  return {
    width: bounds.width,
    height: bounds.height,
    maximized: bounds.maximized,
    opacity: bounds.opacity
  };
}

function saveWindowState(win, snapshot = {}) {
  if (!win || win.isDestroyed()) return;
  try {
    // While fullscreen or maximized, getBounds() reports the screen-filling
    // rect; persisting that would erase the user's windowed (often snapped)
    // size and position.
    const bounds = snapshot.bounds || (
      (win.isFullScreen() || win.isMaximized()) && typeof win.getNormalBounds === "function"
        ? win.getNormalBounds()
        : win.getBounds()
    );
    const maximized = snapshot.maximized == null ? win.isMaximized() : Boolean(snapshot.maximized);
    fsSync.mkdirSync(app.getPath("userData"), { recursive: true });
    fsSync.writeFileSync(
      windowStatePath(),
      JSON.stringify({
        bounds,
        maximized,
        opacity: clampWindowOpacity(win.getOpacity())
      }, null, 2),
      "utf8"
    );
  } catch (error) {
    console.warn(`[MSBT Electron] Could not save window state: ${error && error.message ? error.message : error}`);
  }
}

function updateState(patch) {
  latestUpdateState = { ...latestUpdateState, ...patch };
  for (const win of BrowserWindow.getAllWindows()) {
    if (!win.isDestroyed() && win.webContents && !win.webContents.isDestroyed()) {
      win.webContents.send("app:updateState", latestUpdateState);
    }
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

function normalizeVersion(value) {
  return String(value || "").trim().replace(/^v/i, "");
}

function parsePublicVersion(value) {
  const text = normalizeVersion(value);
  const match = text.match(/^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?(?:-(alpha|beta)\.(\d+))?$/i);
  if (!match) return null;
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    build: match[4] ? Number(match[4]) : 0,
    prerelease: match[5] ? String(match[5]).toLowerCase() : "",
    prereleaseNumber: match[6] ? Number(match[6]) : 0
  };
}

function comparePublicVersions(left, right) {
  const a = parsePublicVersion(left);
  const b = parsePublicVersion(right);
  if (!a || !b) return normalizeVersion(left).localeCompare(normalizeVersion(right));
  for (const key of ["major", "minor", "patch", "build"]) {
    if (a[key] !== b[key]) return a[key] > b[key] ? 1 : -1;
  }
  if (a.prerelease !== b.prerelease) {
    if (!a.prerelease) return 1;
    if (!b.prerelease) return -1;
    const order = { alpha: 0, beta: 1 };
    const aOrder = Object.prototype.hasOwnProperty.call(order, a.prerelease) ? order[a.prerelease] : -1;
    const bOrder = Object.prototype.hasOwnProperty.call(order, b.prerelease) ? order[b.prerelease] : -1;
    if (aOrder !== bOrder) return aOrder > bOrder ? 1 : -1;
  }
  if (a.prereleaseNumber !== b.prereleaseNumber) return a.prereleaseNumber > b.prereleaseNumber ? 1 : -1;
  return 0;
}

function isNewerPublicVersion(remote, local) {
  if (!remote || !local) return false;
  return comparePublicVersions(remote, local) > 0;
}

function normalizeManifestValue(value) {
  const text = value == null ? "" : String(value).trim();
  // Treat build placeholders as empty so post-release manifest stamps
  // (pending -> real commit) do not look like same-version rebuilds.
  if (!text || text === "unknown" || text === "unavailable" || text === "pending" || text === "dev") {
    return "";
  }
  return text;
}

function manifestMetadataChanged(local, remote) {
  // Compare content hashes only. Do not use git_commit: release builds bake
  // "pending", then a later refresh often stamps the real SHA without rebuilding.
  const fields = [
    "external_exe_sha256",
    "sdkmod_sha256",
    "ui_layout_sha256",
    "portable_zip_sha256",
    "legacy_tkinter_zip_sha256",
    "beta_zip_sha256"
  ];
  return fields.some((field) => {
    const localValue = normalizeManifestValue(local && local[field]);
    const remoteValue = normalizeManifestValue(remote && remote[field]);
    return Boolean(localValue && remoteValue && localValue !== remoteValue);
  });
}

async function fetchLatestManifest() {
  const urls = [LATEST_MANIFEST_URL, FALLBACK_LATEST_MANIFEST_URL];
  let lastError = null;
  for (const url of urls) {
    try {
      const response = await fetch(url, { cache: "no-store" });
      const text = await response.text();
      if (!response.ok) {
        lastError = new Error(`Update manifest request failed (${response.status}) from ${url}`);
        continue;
      }
      const manifest = text ? JSON.parse(text) : {};
      return { response, manifest, url };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("Update manifest could not be loaded.");
}

function createWindow() {
  const savedBounds = ensureWindowOnScreen(readWindowState());
  const windowOptions = {
    width: savedBounds.width,
    height: savedBounds.height,
    minWidth: DEFAULT_WINDOW_BOUNDS.minWidth,
    minHeight: DEFAULT_WINDOW_BOUNDS.minHeight,
    resizable: true,
    backgroundColor: "#090d17",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      zoomFactor: 1
    }
  };
  if (Number.isFinite(savedBounds.x) && Number.isFinite(savedBounds.y)) {
    windowOptions.x = savedBounds.x;
    windowOptions.y = savedBounds.y;
  }
  const win = new BrowserWindow(windowOptions);

  if (Number.isFinite(savedBounds.x) && Number.isFinite(savedBounds.y)) {
    // The constructor clamps to the work area, which shaves the invisible
    // resize border off a restored Aero-Snap rect; setBounds applies it exactly.
    win.setBounds({
      x: savedBounds.x,
      y: savedBounds.y,
      width: savedBounds.width,
      height: savedBounds.height
    });
  }
  if (savedBounds.maximized) {
    win.maximize();
  }
  win.setOpacity(clampWindowOpacity(savedBounds.opacity));
  win.webContents.setVisualZoomLevelLimits(1, 1).catch(() => {});
  win.webContents.on("did-finish-load", () => {
    try {
      win.webContents.setZoomFactor(1);
    } catch {
      // Ignore zoom APIs missing on older Electron builds.
    }
    if (FORCE_TOUR) {
      // After renderer init (update check + maybe auto-tour), force Welcome 1/8.
      setTimeout(() => {
        win.webContents
          .executeJavaScript(
            "typeof window.msbtResetTutorials === 'function' && window.msbtResetTutorials()"
          )
          .catch(() => {});
      }, 2800);
    }
  });
  bindWindowState(win, (snapshot) => saveWindowState(win, snapshot));
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

async function loadMobilePairingCode() {
  try {
    const raw = await fs.readFile(MOBILE_PAIRING_FILE(), "utf8");
    const parsed = JSON.parse(raw);
    const code = String(parsed && parsed.pairingCode ? parsed.pairingCode : "").trim();
    if (/^\d{6}$/.test(code)) {
      mobileGateway.setPairingCode(code);
      return code;
    }
  } catch {
    // First launch or unreadable file — generate below.
  }
  const code = mobileGateway.rotatePairingCode();
  await saveMobilePairingCode(code);
  return code;
}

async function saveMobilePairingCode(code) {
  const pairingCode = String(code || mobileGateway.info().pairingCode || "").trim();
  await fs.mkdir(path.dirname(MOBILE_PAIRING_FILE()), { recursive: true });
  await fs.writeFile(
    MOBILE_PAIRING_FILE(),
    JSON.stringify({ pairingCode, updated_at: new Date().toISOString() }, null, 2),
    "utf8"
  );
  return pairingCode;
}

async function startMobileGateway() {
  await loadMobilePairingCode();
  try {
    return await mobileGateway.start();
  } catch (error) {
    return {
      ...mobileGateway.info(),
      ok: false,
      enabled: false,
      lastError: String(error && error.message ? error.message : error)
    };
  }
}

ipcMain.handle("mobileGateway:getInfo", async () => mobileGateway.info());
ipcMain.handle("mobileGateway:start", async () => startMobileGateway());
ipcMain.handle("mobileGateway:stop", async () => mobileGateway.stop());
ipcMain.handle("mobileGateway:rotateCode", async () => {
  const pairingCode = mobileGateway.rotatePairingCode();
  await saveMobilePairingCode(pairingCode);
  return mobileGateway.info();
});
ipcMain.handle("mobileGateway:makeQr", async (_event, text) => {
  const payload = String(text || "").trim();
  if (!payload) {
    return { ok: false, message: "Missing pairing payload." };
  }
  try {
    const QRCode = require("qrcode");
    const dataUrl = await QRCode.toDataURL(payload, {
      errorCorrectionLevel: "M",
      margin: 1,
      width: 280,
      color: { dark: "#0b1220", light: "#ffffff" }
    });
    return { ok: true, dataUrl };
  } catch (error) {
    return {
      ok: false,
      message: error && error.message ? error.message : String(error)
    };
  }
});

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJsonFile(filePath) {
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw.replace(/^\uFEFF/, ""));
}

function normalizeManifestVersion(value, fallback = "") {
  const text = String(value || "").trim();
  if (!text || text === "unknown" || text === "unavailable" || text === "pending" || text === "dev") {
    return String(fallback || "").trim();
  }
  return text;
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

async function userDataFileInfo(userDataPath, definition) {
  const filePath = path.join(userDataPath, definition.fileName);
  try {
    const stat = await fs.stat(filePath);
    return {
      ...definition,
      exists: true,
      path: filePath,
      size: stat.size,
      modifiedAt: stat.mtime.toISOString()
    };
  } catch (error) {
    if (error && error.code !== "ENOENT") {
      return {
        ...definition,
        exists: false,
        path: filePath,
        error: String(error.message || error)
      };
    }
    return {
      ...definition,
      exists: false,
      path: filePath,
      size: 0,
      modifiedAt: ""
    };
  }
}

async function getUserDataInfo() {
  const userDataPath = app.getPath("userData");
  await fs.mkdir(userDataPath, { recursive: true });
  const files = [];
  for (const definition of USER_DATA_FILE_DEFINITIONS) {
    files.push(await userDataFileInfo(userDataPath, definition));
  }
  return {
    ok: true,
    path: userDataPath,
    files,
    message: "Saved Electron user data is stored outside the install folder and should survive app updates."
  };
}

async function getDataCacheInfo() {
  const userDataPath = app.getPath("userData");
  const cachePath = dataCacheDir(userDataPath);
  const liveGzoPath = bl4GzoCacheFilePath();
  await fs.mkdir(cachePath, { recursive: true });
  let fileCount = 0;
  let bytes = 0;
  const entries = await fs.readdir(cachePath, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    try {
      const stat = await fs.stat(path.join(cachePath, entry.name));
      fileCount += 1;
      bytes += stat.size;
    } catch {
      /* file changed while inspecting */
    }
  }
  if (await fileExists(liveGzoPath)) {
    try {
      const stat = await fs.stat(liveGzoPath);
      fileCount += 1;
      bytes += stat.size;
    } catch {
      /* file changed while inspecting */
    }
  }
  return {
    ok: true,
    path: cachePath,
    fileCount,
    bytes,
    message: fileCount
      ? `${fileCount} downloaded catalog cache file(s) found.`
      : "Downloaded catalog cache is empty; bundled offline data remains available."
  };
}

function backupTimestamp() {
  return new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
}

async function exportUserDataBackup() {
  const info = await getUserDataInfo();
  const defaultPath = path.join(
    app.getPath("documents"),
    `MSBT-Electron-User-Data-Backup-${backupTimestamp()}.json`
  );
  const result = await dialog.showSaveDialog({
    title: "Export MSBT saved data backup",
    defaultPath,
    filters: [
      { name: "MSBT JSON backup", extensions: ["json"] }
    ]
  });
  if (result.canceled || !result.filePath) {
    return { ok: false, canceled: true, message: "Backup export cancelled." };
  }

  const files = {};
  for (const fileInfo of info.files) {
    if (!fileInfo.exists) continue;
    try {
      files[fileInfo.fileName] = {
        label: fileInfo.label,
        size: fileInfo.size,
        modifiedAt: fileInfo.modifiedAt,
        content: await fs.readFile(fileInfo.path, "utf8")
      };
    } catch (error) {
      files[fileInfo.fileName] = {
        label: fileInfo.label,
        error: String(error && error.message ? error.message : error)
      };
    }
  }

  const payload = {
    version: 1,
    appVersion: app.getVersion(),
    exportedAt: new Date().toISOString(),
    userDataPath: info.path,
    files
  };
  await fs.writeFile(result.filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  return {
    ok: true,
    path: result.filePath,
    files: Object.keys(files),
    message: `Saved data backup exported to ${result.filePath}`
  };
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

async function bundledActorScriptDeployerInfo() {
  const initPath = path.join(BUNDLED_ACTOR_SCRIPT_DEPLOYER_PATH, "__init__.py");
  const projectPath = path.join(BUNDLED_ACTOR_SCRIPT_DEPLOYER_PATH, "pyproject.toml");
  const available = (await fileExists(initPath)) && (await fileExists(projectPath));
  return {
    available,
    path: BUNDLED_ACTOR_SCRIPT_DEPLOYER_PATH,
    status: available ? "bundled" : "missing",
    message: available
      ? "Bundled ActorScriptDeployer is available in this app build."
      : "Bundled ActorScriptDeployer folder is missing from this app build."
  };
}

async function installedActorScriptDeployerInfo(destination) {
  const initPath = path.join(destination, "__init__.py");
  const projectPath = path.join(destination, "pyproject.toml");
  const available = (await fileExists(initPath)) && (await fileExists(projectPath));
  return {
    available,
    path: destination,
    status: available ? "detected" : "missing",
    message: available
      ? "ActorScriptDeployer folder is installed at this sdk_mods path."
      : "ActorScriptDeployer folder is not installed at this sdk_mods path."
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
      ? "Installed SDK mod matches the bundled SDK mod."
      : bundledHash
        ? "Installed SDK mod differs from the bundled SDK mod."
        : "Installed SDK mod was detected; bundled comparison is unavailable."
  };
}

async function detectInstalledSdkmodInfo(bundledHash = "") {
  for (const candidate of bl4SdkModsCandidates()) {
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
    manifest = { error: String(error && error.message ? error.message : error) };
  }
  const bundledSdkmod = await bundledSdkmodInfo();
  const bundledActorScriptDeployer = await bundledActorScriptDeployerInfo();
  const installedSdkmod = await detectInstalledSdkmodInfo(bundledSdkmod.sha256);
  let oak2 = null;
  let requiredMods = null;
  try {
    const sdkModsPath = installedSdkmod && installedSdkmod.sdkModsPath
      ? installedSdkmod.sdkModsPath
      : "";
    const detection = await detectOak2Status(sdkModsPath);
    oak2 = detection.oak2 || null;
    requiredMods = detection.requiredMods || null;
  } catch {
    oak2 = null;
    requiredMods = null;
  }
  const appVersion = app.getVersion();
  const packageVersion = normalizeManifestVersion(manifest.package_version || manifest.app_version, appVersion) || appVersion;
  return {
    ok: true,
    appVersion,
    electronVersion: process.versions.electron,
    platform: process.platform,
    osRelease: os.release(),
    packageVersion,
    sdkmodVersion: normalizeManifestVersion(manifest.sdkmod_version, packageVersion) || "unavailable",
    resourcesVersion: normalizeManifestVersion(manifest.resources_version, packageVersion) || "unavailable",
    sdkRequired: manifest.sdk_required || "oak2-mod-manager v0.3",
    sdkRequiredUrl: manifest.sdk_required_url || oak2Install.OAK2_INSTALL_GUIDE_URL,
    oak2,
    oak2Present: Boolean(oak2 && oak2.present),
    hasOak2: Boolean(oak2 && oak2.ok),
    requiredMods,
    packaged: app.isPackaged,
    localManifest: {
      ...manifest,
      package_version: packageVersion,
      app_version: normalizeManifestVersion(manifest.app_version, appVersion) || appVersion,
      sdkmod_version: normalizeManifestVersion(manifest.sdkmod_version, packageVersion) || packageVersion,
      resources_version: normalizeManifestVersion(manifest.resources_version, packageVersion) || packageVersion,
      electron_version: normalizeManifestVersion(manifest.electron_version, appVersion) || appVersion
    },
    bundledSdkmod,
    bundledActorScriptDeployer,
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

async function sdkModsPathInfo(rawPath, bundledHash = "", options = {}) {
  const sdkModsPath = normalizeSdkModsPath(rawPath);
  if (!sdkModsPath) return { ok: false, message: "No sdk_mods path was provided." };
  const baseName = path.basename(sdkModsPath).toLowerCase();
  if (baseName !== "sdk_mods") {
    return { ok: false, path: sdkModsPath, message: "Choose the Borderlands 4 sdk_mods folder." };
  }
  const exists = await fileExists(sdkModsPath);
  const allowMissing = Boolean(options && options.allowMissing);
  const parentExists = exists ? true : await fileExists(path.dirname(sdkModsPath));
  const canCreate = allowMissing && parentExists;
  const destination = path.join(sdkModsPath, "MattsSDKBoostingTools.sdkmod");
  const actorScriptDeployerDestination = path.join(sdkModsPath, "ActorScriptDeployer");
  const bundledSha = bundledHash || (await bundledSdkmodInfo()).sha256;
  const gameRoot = oak2Install.gameRootFromSdkModsPath(sdkModsPath);
  const oak2 = gameRoot ? await oak2Install.inspectOak2Install(gameRoot) : null;
  const requiredMods = exists
    ? await oak2Install.requiredModsStatus(sdkModsPath)
    : { ok: false, allInstalled: false, allEnabled: false, mods: [], message: "sdk_mods folder does not exist yet." };
  const installedSdkmod = await installedSdkmodInfo(destination, bundledSha);
  const installedActorScriptDeployer = await installedActorScriptDeployerInfo(actorScriptDeployerDestination);
  return {
    ok: exists || canCreate,
    path: sdkModsPath,
    gameRoot,
    destination,
    actorScriptDeployerDestination,
    installedSdkmod,
    installedActorScriptDeployer,
    oak2,
    oak2Present: Boolean(oak2 && oak2.present),
    hasOak2: Boolean(oak2 && oak2.ok),
    sdkPresent: Boolean(oak2 && oak2.ok),
    msbtInstalled: Boolean(installedSdkmod && installedSdkmod.available),
    hasMsbt: Boolean(installedSdkmod && installedSdkmod.available),
    requiredMods,
    message: exists
      ? "sdk_mods folder found."
      : canCreate
        ? "Borderlands 4 folder found; sdk_mods will be created."
        : "sdk_mods folder does not exist."
  };
}

async function autoDetectSdkModsPathInfo(options = {}) {
  const candidates = bl4SdkModsCandidates();
  for (const candidate of candidates) {
    const info = await sdkModsPathInfo(candidate, "", options);
    if (info.ok) return info;
  }
  return {
    ok: false,
    path: "",
    candidates,
    message: "Could not auto-detect Borderlands 4 sdk_mods from the known Steam library folders. Paste or browse to the sdk_mods folder."
  };
}

ipcMain.handle("app:detectSdkMods", async () => {
  return autoDetectSdkModsPathInfo();
});

ipcMain.handle("app:browseSdkMods", async () => {
  const prefs = await loadMattEditorPrefsData();
  const remembered = prefs && prefs.data ? prefs.data.sdkModsPath : "";
  const result = await dialog.showOpenDialog({
    title: "Choose the Borderlands 4 sdk_mods folder",
    defaultPath: remembered || undefined,
    properties: ["openDirectory"]
  });
  if (result.canceled || !result.filePaths.length) {
    return { ok: false, canceled: true, message: "No sdk_mods folder selected." };
  }
  return sdkModsPathInfo(result.filePaths[0]);
});

async function installBundledSdkMods(rawPath = "", options = {}) {
  const sourceExists = await fileExists(BUNDLED_SDKMOD_PATH);
  if (!sourceExists) {
    return { ok: false, message: "Bundled MattsSDKBoostingTools.sdkmod was not found in this app build." };
  }
  const bundledActorScriptDeployer = await bundledActorScriptDeployerInfo();
  if (!bundledActorScriptDeployer.available) {
    return { ok: false, message: "Bundled ActorScriptDeployer folder was not found in this app build." };
  }
  const allowGameRunning = Boolean(options && options.allowGameRunning);
  const gameWasRunning = await isBorderlandsRunning();
  if (gameWasRunning && !allowGameRunning) {
    return { ok: false, message: "Borderlands4.exe is running. Close the game before installing or updating the SDK mod." };
  }
  const hasPath = Boolean(String(rawPath || "").trim());
  const info = hasPath
    ? await sdkModsPathInfo(rawPath, "", { allowMissing: Boolean(options && options.allowMissing) })
    : await autoDetectSdkModsPathInfo({ allowMissing: Boolean(options && options.allowMissing) });
  if (!info.ok) return info;
  await fs.mkdir(info.path, { recursive: true });
  await fs.copyFile(BUNDLED_SDKMOD_PATH, info.destination);
  await fs.rm(info.actorScriptDeployerDestination, { recursive: true, force: true });
  await fs.cp(BUNDLED_ACTOR_SCRIPT_DEPLOYER_PATH, info.actorScriptDeployerDestination, {
    recursive: true,
    force: true,
    filter: (source) => !/(^|[\\/])__pycache__($|[\\/])|\.pyc$/i.test(source)
  });
  const enabled = await oak2Install.enableRequiredMods(info.path);
  const bundled = await bundledSdkmodInfo();
  const refreshed = await sdkModsPathInfo(info.path, bundled.sha256, { allowMissing: true });
  return {
    ok: true,
    path: info.path,
    gameRoot: info.gameRoot || refreshed.gameRoot,
    destination: info.destination,
    actorScriptDeployerDestination: info.actorScriptDeployerDestination,
    sha256: await safeFileHash(info.destination),
    installedSdkmod: await installedSdkmodInfo(info.destination, bundled.sha256),
    installedActorScriptDeployer: await installedActorScriptDeployerInfo(info.actorScriptDeployerDestination),
    enabledMods: enabled,
    oak2: refreshed.oak2,
    requiredMods: refreshed.requiredMods,
    gameWasRunning,
    message: gameWasRunning
      ? "MattsSDKBoostingTools.sdkmod and ActorScriptDeployer installed/updated and marked enabled. Borderlands 4 was open; fully restart the game before testing live actions."
      : "MattsSDKBoostingTools.sdkmod and ActorScriptDeployer installed/updated and marked enabled in sdk_mods/settings."
  };
}

async function detectOak2Status(rawPath = "") {
  const gameRoot = await oak2Install.resolveGameRoot(rawPath);
  if (!gameRoot) {
    return {
      ok: false,
      present: false,
      hasOak2: false,
      oak2Present: false,
      sdkPresent: false,
      message: "Could not auto-detect a Borderlands 4 install. Browse to the game folder or sdk_mods folder."
    };
  }
  const oak2 = await oak2Install.inspectOak2Install(gameRoot);
  const sdkModsPath = oak2.sdkModsPath;
  const requiredMods = await oak2Install.requiredModsStatus(sdkModsPath);
  const bundled = await bundledSdkmodInfo();
  const pathInfo = await sdkModsPathInfo(sdkModsPath, bundled.sha256, { allowMissing: true });
  return {
    ok: Boolean(oak2.ok),
    ...pathInfo,
    oak2,
    oak2Present: Boolean(oak2.present),
    hasOak2: Boolean(oak2.ok),
    sdkPresent: Boolean(oak2.ok),
    requiredMods,
    message: oak2.message
  };
}

async function installOak2SdkManager(rawPath = "", options = {}) {
  const allowGameRunning = Boolean(options && options.allowGameRunning);
  const gameWasRunning = await isBorderlandsRunning();
  if (gameWasRunning && !allowGameRunning) {
    return { ok: false, message: "Borderlands4.exe is running. Close the game before installing oak2-mod-manager." };
  }
  const gameRoot = await oak2Install.resolveGameRoot(rawPath);
  if (!gameRoot) {
    return {
      ok: false,
      message: "Could not find a Borderlands 4 folder. Detect or browse to sdk_mods / the game root first."
    };
  }
  const installMsbt = options.installMsbt !== false;
  const oak2Result = await oak2Install.installOak2FromCache(app.getPath("userData"), gameRoot, options);
  if (!oak2Result.ok && !options.dryRun) return oak2Result;

  let sdkResult = null;
  let enabled = null;
  if (installMsbt && !options.dryRun) {
    sdkResult = await installBundledSdkMods(path.join(gameRoot, "sdk_mods"), {
      allowMissing: true,
      allowGameRunning: true
    });
    enabled = sdkResult && sdkResult.enabledMods;
  } else if (!options.dryRun) {
    enabled = await oak2Install.enableRequiredMods(path.join(gameRoot, "sdk_mods"));
  }

  const detection = await detectOak2Status(path.join(gameRoot, "sdk_mods"));
  return {
    ok: Boolean(options.dryRun ? oak2Result.ok : detection.hasOak2 && (!installMsbt || (sdkResult && sdkResult.ok))),
    gameWasRunning,
    gameRoot,
    oak2Install: oak2Result,
    sdkModInstall: sdkResult,
    enabledMods: enabled,
    detection,
    noticePath: oak2Result.noticePath || "",
    license: {
      spdx: oak2Install.OAK2_LICENSE_SPDX,
      repoUrl: oak2Install.OAK2_REPO_URL,
      licenseUrl: oak2Install.OAK2_LICENSE_URL
    },
    message: options.dryRun
      ? oak2Result.message
      : [
          oak2Result.message,
          sdkResult && sdkResult.message ? sdkResult.message : "",
          gameWasRunning ? "Borderlands 4 was open; fully restart the game after install." : "Restart Borderlands 4 so oak2 and MSBT load."
        ]
          .filter(Boolean)
          .join(" ")
  };
}

ipcMain.handle("app:installSdkMod", async (_event, rawPath) => {
  return installBundledSdkMods(rawPath, { allowMissing: true });
});

ipcMain.handle("app:detectOak2", async (_event, rawPath) => {
  return detectOak2Status(rawPath || "");
});

ipcMain.handle("app:installOak2", async (_event, rawPath, options = {}) => {
  return installOak2SdkManager(rawPath || "", options || {});
});

ipcMain.handle("app:enableRequiredSdkMods", async (_event, rawPath) => {
  const info = String(rawPath || "").trim()
    ? await sdkModsPathInfo(rawPath, "", { allowMissing: true })
    : await autoDetectSdkModsPathInfo({ allowMissing: true });
  if (!info.ok) return info;
  await fs.mkdir(info.path, { recursive: true });
  const enabled = await oak2Install.enableRequiredMods(info.path);
  const requiredMods = await oak2Install.requiredModsStatus(info.path);
  return { ...enabled, requiredMods, path: info.path, gameRoot: info.gameRoot };
});

ipcMain.handle("app:recheckSdkStack", async (_event, rawPath) => {
  return detectOak2Status(rawPath || "");
});

ipcMain.handle("app:readResourceJson", async (_event, resourceName) => {
  const name = path.basename(String(resourceName || ""));
  if (!ALLOWED_RESOURCE_FILES.has(name)) {
    return { ok: false, message: `Resource is not allowlisted: ${name}` };
  }
  try {
    if (isElectronResourceFile(name)) {
      const catalog = await readCatalogJson(app.getPath("userData"), name, dataCatalogOptions());
      if (catalog.ok) {
        return { ok: true, name, data: catalog.data, source: catalog.source, path: catalog.path };
      }
    }
    const text = await fs.readFile(path.join(RESOURCE_DIR, name), "utf8");
    return { ok: true, name, data: JSON.parse(text), source: "bundled" };
  } catch (error) {
    return { ok: false, name, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:readDevSpawnerCatalog", async () => {
  try {
    const catalog = await readCatalogJson(
      app.getPath("userData"),
      KNOWN_FILES.dev_spawner_catalog,
      dataCatalogOptions()
    );
    if (catalog.ok) {
      return {
        ok: true,
        data: catalog.data,
        source: catalog.source,
        path: catalog.path
      };
    }
    const catalogPath = path.join(ELECTRON_APP_DIR, "dev_spawner_catalog.json");
    const text = await fs.readFile(catalogPath, "utf8");
    return { ok: true, data: JSON.parse(text), source: "bundled", path: catalogPath };
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:getUserDataInfo", async () => getUserDataInfo());

ipcMain.handle("app:getDataCacheInfo", async () => getDataCacheInfo());

ipcMain.handle("app:openDataCacheFolder", async () => {
  const info = await getDataCacheInfo();
  const error = await shell.openPath(info.path);
  if (error) return { ...info, ok: false, message: error };
  return { ...info, message: "Opened downloaded catalog cache folder." };
});

ipcMain.handle("app:clearDataCatalogCache", async () => {
  const userDataPath = app.getPath("userData");
  const cachePath = dataCacheDir(userDataPath);
  await fs.rm(cachePath, { recursive: true, force: true });
  await fs.rm(bl4GzoCacheFilePath(), { force: true });
  await fs.mkdir(cachePath, { recursive: true });
  return {
    ...(await getDataCacheInfo()),
    message: "Downloaded catalog cache cleared. Saved settings were not changed."
  };
});

ipcMain.handle("app:openUserDataFolder", async () => {
  const info = await getUserDataInfo();
  const error = await shell.openPath(info.path);
  if (error) return { ok: false, path: info.path, message: error };
  return { ok: true, path: info.path, message: "Opened saved data folder." };
});

ipcMain.handle("app:exportUserDataBackup", async () => exportUserDataBackup());

ipcMain.handle("app:getWindowSettings", async () => {
  const win = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0];
  return {
    ok: true,
    opacity: win && !win.isDestroyed() ? clampWindowOpacity(win.getOpacity()) : DEFAULT_WINDOW_OPACITY
  };
});

ipcMain.handle("app:setWindowOpacity", async (_event, rawOpacity) => {
  const opacity = clampWindowOpacity(rawOpacity);
  for (const win of BrowserWindow.getAllWindows()) {
    if (win && !win.isDestroyed()) {
      win.setOpacity(opacity);
      saveWindowState(win);
    }
  }
  return { ok: true, opacity, message: `App opacity saved at ${Math.round(opacity * 100)}%.` };
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

ipcMain.handle("app:loadTravelFavorites", async () => {
  const filePath = travelFavoritesFilePath(app.getPath("userData"));
  return readTravelFavorites(filePath);
});

ipcMain.handle("app:saveTravelFavorites", async (_event, payload) => {
  const filePath = travelFavoritesFilePath(app.getPath("userData"));
  try {
    return await writeTravelFavorites(filePath, payload || {});
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

ipcMain.handle("app:loadMovementSettings", async () => {
  const filePath = movementSettingsFilePath(app.getPath("userData"));
  return readMovementSettings(filePath);
});

ipcMain.handle("app:saveMovementSettings", async (_event, payload) => {
  const filePath = movementSettingsFilePath(app.getPath("userData"));
  try {
    return await writeMovementSettings(filePath, payload || {});
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:loadRaritySettings", async () => {
  const filePath = raritySettingsFilePath(app.getPath("userData"));
  return readRaritySettings(filePath);
});

ipcMain.handle("app:saveRaritySettings", async (_event, payload) => {
  const filePath = raritySettingsFilePath(app.getPath("userData"));
  try {
    return await writeRaritySettings(filePath, payload || {});
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:loadWalkthroughSettings", async () => {
  const filePath = walkthroughSettingsFilePath(app.getPath("userData"));
  return readWalkthroughSettings(filePath);
});

ipcMain.handle("app:saveWalkthroughSettings", async (_event, payload) => {
  const filePath = walkthroughSettingsFilePath(app.getPath("userData"));
  try {
    return await writeWalkthroughSettings(filePath, payload || {});
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

const MATT_EDITOR_SAVE_MAX_BYTES = 48 * 1024 * 1024;

function mattEditorPrefsPath() {
  return mattEditorPrefsFilePath(app.getPath("userData"));
}

async function loadMattEditorPrefsData() {
  return readMattEditorPrefs(mattEditorPrefsPath());
}

async function rememberMattEditorPrefs(partial) {
  return writeMattEditorPrefs(mattEditorPrefsPath(), partial);
}

async function firstExistingPath(candidates) {
  for (const candidate of candidates) {
    const resolved = normalizePathValue(candidate);
    if (!resolved) continue;
    try {
      await fs.access(resolved);
      return resolved;
    } catch {
      // try next
    }
  }
  return "";
}

function bl4ClientSaveFolderCandidates(steamId) {
  const names = ["My Games", "My games"];
  const folders = [];
  for (const name of names) {
    const root = path.join(os.homedir(), "Documents", name, "Bl4", "Saved", "SaveGames");
    if (steamId) folders.push(path.join(root, steamId, "Profiles", "client"));
    folders.push(root);
  }
  return folders;
}

async function readSaveFilePayload(filePath) {
  const resolved = normalizePathValue(filePath);
  if (!resolved) return { ok: false, message: "No file path." };
  if (!allowedSaveExtension(resolved)) {
    return { ok: false, message: "Choose a .sav, .yaml, .yml, or .txt file." };
  }
  try {
    const stat = await fs.stat(resolved);
    if (!stat.isFile()) return { ok: false, message: "That path is not a file." };
    if (stat.size > MATT_EDITOR_SAVE_MAX_BYTES) {
      return { ok: false, message: "That save file is larger than the 48 MB editor limit." };
    }
    const buffer = await fs.readFile(resolved);
    return {
      ok: true,
      path: resolved,
      folder: path.dirname(resolved),
      name: path.basename(resolved),
      base64: buffer.toString("base64")
    };
  } catch (error) {
    return { ok: false, message: `Could not read file: ${error && error.message ? error.message : error}` };
  }
}

function withDetectedSteamId(payload, currentSteamId) {
  if (!payload || !payload.ok) return payload;
  const detected = steamIdFromSavePath(payload.path);
  return {
    ...payload,
    steamId: detected || String(currentSteamId || "").trim()
  };
}

ipcMain.handle("app:loadMattEditorPrefs", async () => {
  return loadMattEditorPrefsData();
});

ipcMain.handle("app:saveMattEditorPrefs", async (_event, payload) => {
  try {
    return await rememberMattEditorPrefs(payload || {});
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:mattEditorOpenFile", async (_event, kind) => {
  const prefs = await loadMattEditorPrefsData();
  const data = prefs.data || {};
  const isProfile = String(kind || "save") === "profile";
  const rememberedFile = isProfile ? data.lastProfileFile : data.lastSaveFile;
  const rememberedFolder = isProfile ? data.lastProfileFolder : data.lastSaveFolder;
  const guessed = await firstExistingPath([
    rememberedFolder,
    folderFromFile(rememberedFile),
    ...bl4ClientSaveFolderCandidates(data.steamId)
  ]);
  const result = await dialog.showOpenDialog({
    title: isProfile ? "Open BL4 profile.sav" : "Open BL4 save file",
    defaultPath: guessed || rememberedFile || undefined,
    properties: ["openFile"],
    filters: [
      {
        name: isProfile ? "Profile / YAML" : "Save / YAML / Text",
        extensions: isProfile ? ["sav", "yaml", "yml"] : ["sav", "yaml", "yml", "txt"]
      },
      { name: "All files", extensions: ["*"] }
    ]
  });
  if (result.canceled || !result.filePaths.length) {
    return { ok: false, canceled: true, message: "No file selected." };
  }
  const payload = withDetectedSteamId(await readSaveFilePayload(result.filePaths[0]), data.steamId);
  if (!payload.ok) return payload;
  const patch = isProfile
    ? { lastProfileFile: payload.path, lastProfileFolder: payload.folder }
    : { lastSaveFile: payload.path, lastSaveFolder: payload.folder };
  if (payload.steamId) patch.steamId = payload.steamId;
  const saved = await rememberMattEditorPrefs(patch);
  return { ...payload, prefs: saved.data };
});

ipcMain.handle("app:mattEditorReopenFile", async (_event, kind) => {
  const prefs = await loadMattEditorPrefsData();
  const data = prefs.data || {};
  const isProfile = String(kind || "save") === "profile";
  const filePath = isProfile ? data.lastProfileFile : data.lastSaveFile;
  if (!filePath) {
    return { ok: false, message: isProfile ? "No remembered profile file yet." : "No remembered save file yet." };
  }
  const payload = withDetectedSteamId(await readSaveFilePayload(filePath), data.steamId);
  if (!payload.ok) return payload;
  if (payload.steamId && payload.steamId !== data.steamId) {
    const saved = await rememberMattEditorPrefs({ steamId: payload.steamId });
    return { ...payload, prefs: saved.data };
  }
  return payload;
});

ipcMain.handle("app:mattEditorSaveFile", async (_event, payload) => {
  const body = payload && typeof payload === "object" ? payload : {};
  const overwritePath = normalizePathValue(body.overwritePath || "");
  const suggestedName = String(body.suggestedName || "save_encrypted.sav").trim() || "save_encrypted.sav";
  const prefs = await loadMattEditorPrefsData();
  const data = prefs.data || {};
  let target = "";
  if (body.overwrite && overwritePath) {
    target = overwritePath;
  } else {
    const defaultDir = await firstExistingPath([
      data.lastExportFolder,
      data.lastSaveFolder,
      folderFromFile(data.lastSaveFile),
      ...bl4ClientSaveFolderCandidates(data.steamId)
    ]);
    const defaultPath = path.join(defaultDir || "", path.basename(suggestedName));
    const result = await dialog.showSaveDialog({
      title: "Save encrypted BL4 file",
      defaultPath,
      filters: [{ name: "BL4 Save", extensions: ["sav"] }]
    });
    if (result.canceled || !result.filePath) {
      return { ok: false, canceled: true, message: "Save cancelled." };
    }
    target = normalizePathValue(result.filePath);
  }
  if (!target) return { ok: false, message: "No save path." };
  const raw = String(body.base64 || "");
  if (!raw) return { ok: false, message: "No file data to write." };
  let buffer;
  try {
    buffer = Buffer.from(raw, "base64");
  } catch (error) {
    return { ok: false, message: `Could not decode file data: ${error && error.message ? error.message : error}` };
  }
  if (!buffer.length) return { ok: false, message: "Encrypted data is empty." };
  if (buffer.length > MATT_EDITOR_SAVE_MAX_BYTES) {
    return { ok: false, message: "Encrypted file is larger than the 48 MB editor limit." };
  }
  try {
    await fs.mkdir(path.dirname(target), { recursive: true });
    await fs.writeFile(target, buffer);
  } catch (error) {
    return { ok: false, message: `Could not write file: ${error && error.message ? error.message : error}` };
  }
  const detectedSteamId = steamIdFromSavePath(target);
  const saved = await rememberMattEditorPrefs({
    lastSaveFile: target,
    lastSaveFolder: path.dirname(target),
    lastExportFolder: path.dirname(target),
    ...(detectedSteamId ? { steamId: detectedSteamId } : {})
  });
  return {
    ok: true,
    path: target,
    name: path.basename(target),
    folder: path.dirname(target),
    prefs: saved.data
  };
});

ipcMain.handle("app:loadBl4Catalog", async () => {
  try {
    const options = await bl4CatalogLoadOptions();
    const catalog = await loadBl4Catalog(RESOURCE_DIR, options);
    return { ...catalog, catalogSources: options.sources };
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:refreshGzoCatalog", async () => {
  try {
    const options = await bl4CatalogLoadOptions();
    return await refreshGzoCatalog(RESOURCE_DIR, bl4GzoCacheFilePath(), {
      filePaths: options.filePaths,
      fallbackUrls: gzoGithubFallbackUrls()
    });
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:refreshDataCatalogs", async (_event, options = {}) => {
  try {
    return await softRefreshDataCatalogs({
      quiet: Boolean(options && options.quiet),
      retries: options && Number.isFinite(options.retries) ? options.retries : 3
    });
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:getDataCatalogStatus", async () => {
  try {
    return await getDataCatalogStatus(app.getPath("userData"), dataCatalogOptions());
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error) };
  }
});

ipcMain.handle("app:getTutorialCopy", async () => {
  try {
    return await loadTutorialCopy(app.getPath("userData"), dataCatalogOptions());
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

function normalizeGzoField(value) {
  return String(value || "").trim();
}

function gzoImageMime(payload, imagePath) {
  const explicitType = normalizeGzoField(payload.imageType).toLowerCase();
  if (["image/png", "image/jpeg", "image/webp"].includes(explicitType)) return explicitType;
  const extension = path.extname(imagePath).toLowerCase();
  if (extension === ".png") return "image/png";
  if (extension === ".jpg" || extension === ".jpeg") return "image/jpeg";
  if (extension === ".webp") return "image/webp";
  return "";
}

async function submitGzoCode(payload = {}) {
  const listing = normalizeGzoField(payload.listing).toLowerCase() === "modded" ? "Modded" : "Legit";
  const fields = {
    action: "submit",
    listing,
    name: normalizeGzoField(payload.name),
    creator: normalizeGzoField(payload.creator),
    type: normalizeGzoField(payload.type),
    category: normalizeGzoField(payload.category),
    rarity: normalizeGzoField(payload.rarity),
    base85: normalizeGzoField(payload.base85),
    deserialized: normalizeGzoField(payload.deserialized),
    notes: normalizeGzoField(payload.notes)
  };
  const missing = ["name", "creator", "type", "rarity"].filter((key) => !fields[key]);
  if (!fields.base85 && !fields.deserialized) {
    missing.push("base85 or deserialized");
  }
  const imagePath = normalizeGzoField(payload.imagePath);
  if (!imagePath) missing.push("image");
  if (missing.length) {
    return { ok: false, message: `Required before submission: ${missing.join(", ")}.` };
  }

  let stat;
  try {
    stat = await fs.stat(imagePath);
  } catch {
    return { ok: false, message: "Selected image file could not be read." };
  }
  if (!stat.isFile()) {
    return { ok: false, message: "Selected image path is not a file." };
  }

  const imageType = gzoImageMime(payload, imagePath);
  if (!imageType) {
    return { ok: false, message: "Image must be PNG, JPEG, or WebP." };
  }

  const form = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    if (value || key === "action" || key === "listing") form.append(key, value);
  }
  const imageData = await fs.readFile(imagePath);
  const imageName = normalizeGzoField(payload.imageName) || path.basename(imagePath);
  form.append("image", new Blob([imageData], { type: imageType }), imageName);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(CODES_API, {
      method: "POST",
      body: form,
      signal: controller.signal
    });
    const text = await response.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { message: text };
    }
    const apiSuccess = Boolean(data && (data.success === true || data.ok === true));
    const apiFailure = Boolean(data && (data.success === false || data.ok === false));
    const ok = response.ok && !apiFailure;
    const message = data && data.message
      ? String(data.message)
      : ok
        ? (apiSuccess ? "Submitted to GZO pending review." : `GZO returned HTTP ${response.status}. Check the response body for review status.`)
        : `GZO submission failed with HTTP ${response.status}.`;
    return {
      ok,
      status: response.status,
      endpoint: CODES_API,
      data,
      rawText: text,
      editUrl: data && data.editUrl ? String(data.editUrl) : "",
      published: Boolean(data && data.published),
      message
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      endpoint: CODES_API,
      message: `GZO submission failed: ${String(error && error.message ? error.message : error)}`
    };
  } finally {
    clearTimeout(timer);
  }
}

ipcMain.handle("app:submitGzoCode", async (_event, payload) => submitGzoCode(payload || {}));

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

ipcMain.handle("app:serialDecodeCheck", async (_event, payload) => {
  const code = [
    "import json, sys",
    "import re",
    "import external_serial_tools",
    "raw = sys.stdin.read()",
    "try:",
    "    payload = json.loads(raw)",
    "    text = str(payload.get('text') or '')",
    "    level = int(payload.get('level') or 70)",
    "except Exception:",
    "    text = raw",
    "    level = 70",
    "level = max(1, min(70, level))",
    "serials = [line.strip() for line in text.splitlines() if line.strip()]",
    "results = []",
    "for serial in serials:",
    "    try:",
    "        if serial.startswith('@U'):",
    "            external_serial_tools.rewrite_item_level(serial, level)",
    "        else:",
    "            human = serial",
    "            new_human, count = re.subn(r'^(\\s*\\d+\\s*(?:,\\s*|\\s+)\\d+\\s*(?:,\\s*|\\s+)\\d+\\s*(?:,\\s*|\\s+))\\d+', r'\\g<1>' + str(level), human, count=1)",
    "            if count <= 0:",
    "                raise ValueError('could not find leading item level in serial')",
    "            external_serial_tools.human_to_serial(new_human)",
    "        results.append({'ok': True, 'message': ''})",
    "    except Exception as exc:",
    "        results.append({'ok': False, 'message': str(exc)})",
    "print(json.dumps({'ok': True, 'total': len(serials), 'results': results}))"
  ].join("\n");
  return runExternalPythonJson(code, typeof payload === "string" ? payload : JSON.stringify(payload || {}), 60000);
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

function killProcessTree(pid) {
  if (!pid) return;
  if (process.platform === "win32") {
    execFile("taskkill", ["/PID", String(pid), "/T", "/F"], { windowsHide: true }, () => {});
    return;
  }
  try {
    process.kill(pid, "SIGTERM");
  } catch {
    // Process already exited.
  }
}

function externalPythonWorker() {
  if (!pythonHelperWorker) {
    pythonHelperWorker = new PersistentPythonWorker({
      candidates: pythonCandidates(),
      cwd: EXTERNAL_APP_DIR,
      pythonPath: EXTERNAL_APP_DIR,
      idleMs: 5 * 60 * 1000,
      killTree: killProcessTree
    });
  }
  return pythonHelperWorker;
}

function runPythonSnippet(pythonExe, code, inputText = "", timeoutMs = 15000) {
  const bootstrappedCode = [
    "import sys",
    `sys.path.insert(0, ${JSON.stringify(EXTERNAL_APP_DIR)})`,
    code
  ].join("\n");
  const args = pythonExe === "py" ? ["-3", "-c", bootstrappedCode] : ["-c", bootstrappedCode];
  const child = spawn(pythonExe, args, {
    cwd: EXTERNAL_APP_DIR,
    stdio: ["pipe", "pipe", "pipe"],
    windowsHide: true
  });

  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    let outputExceeded = false;
    const timer = setTimeout(() => {
      killProcessTree(child.pid);
      reject(new Error(`Timed out running helper with ${pythonExe}. ${stderr.trim()}`.trim()));
    }, timeoutMs);

    child.stdout.on("data", (chunk) => {
      if (outputExceeded) return;
      stdout += chunk.toString();
      if (Buffer.byteLength(stdout) > MAX_OUTPUT_BYTES) {
        outputExceeded = true;
        killProcessTree(child.pid);
      }
    });
    child.stderr.on("data", (chunk) => {
      stderr = (stderr + chunk.toString()).slice(-MAX_OUTPUT_BYTES);
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("exit", (codeNumber) => {
      clearTimeout(timer);
      if (outputExceeded) {
        reject(new Error("Python helper stdout exceeded its 8MB cap."));
      } else if (codeNumber === 0) {
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
  try {
    const stdout = await externalPythonWorker().run(code, inputText, timeoutMs);
    return JSON.parse(stdout || "{}");
  } catch (error) {
    errors.push(`persistent worker: ${error && error.message ? error.message : error}`);
  }
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
    env: {
      ...process.env,
      MSBT_ELECTRON_EXE: process.execPath,
      MSBT_ELECTRON_RESOURCES: RESOURCE_ROOT
    },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true
  });

  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      killProcessTree(child.pid);
      reject(new Error(`Timed out starting Matt editor host with ${pythonExe}. ${stderr.trim()}`.trim()));
    }, MATT_HOST_START_TIMEOUT_MS);

    child.stdout.on("data", (chunk) => {
      stdout = (stdout + chunk.toString()).slice(-MAX_OUTPUT_BYTES);
      const match = stdout.match(/https?:\/\/127\.0\.0\.1:\d+\/?/);
      if (!match) return;
      clearTimeout(timer);
      mattHostProcess = child;
      mattHostUrl = match[0].endsWith("/") ? match[0] : `${match[0]}/`;
      resolve(mattHostUrl);
    });

    child.stderr.on("data", (chunk) => {
      stderr = (stderr + chunk.toString()).slice(-MAX_OUTPUT_BYTES);
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
    return { ok: true, url, hosted: true, message: "Loaded bundled Matt editor with save/profile API routing and MSBT delivery adapter." };
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
    const { response, manifest: remote, url: manifestUrl } = await fetchLatestManifest();
    const localVersion = normalizeManifestVersion(local.package_version || versionInfo.packageVersion, versionInfo.appVersion);
    const remoteVersion = normalizeManifestVersion(remote.package_version);
    const localAppVersion = normalizeManifestVersion(versionInfo.appVersion);
    const remoteElectronVersion = normalizeManifestVersion(remote.electron_version || remote.app_version || remote.package_version);
    const packageVersionChanged = Boolean(remoteVersion && localVersion && remoteVersion !== localVersion);
    const packageBuildChanged = Boolean(remoteVersion && localVersion && remoteVersion === localVersion && manifestMetadataChanged(local, remote));
    const packageUpdateAvailable = packageVersionChanged || packageBuildChanged;
    const electronUpdateAvailable = Boolean(remoteElectronVersion && localAppVersion && isNewerPublicVersion(remoteElectronVersion, localAppVersion));
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
      sdkRequiredUrl: versionInfo.sdkRequiredUrl,
      bundledSdkmod: versionInfo.bundledSdkmod,
      installedSdkmod: versionInfo.installedSdkmod,
      updater,
      manifestUrl,
      packageUpdateAvailable,
      packageVersionChanged,
      packageBuildChanged,
      electronUpdateAvailable,
      updateAvailable: packageUpdateAvailable || electronUpdateAvailable,
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
      sdkRequiredUrl: versionInfo.sdkRequiredUrl,
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
  app.setAppUserModelId("com.funkyoushift.msbt");
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
  if (INSTALL_SDKMODS_AND_EXIT) {
    installBundledSdkMods("", { allowMissing: true, allowGameRunning: true })
      .then((result) => {
        console.log(JSON.stringify(result, null, 2));
        app.exit(result.ok ? 0 : 2);
      })
      .catch((error) => {
        console.error(error && error.stack ? error.stack : String(error));
        app.exit(2);
      });
    return;
  }

  configureAutoUpdater();
  createWindow();
  // Quiet startup auto-check: never blocks UI; offline keeps last-good cache.
  softRefreshDataCatalogs({ quiet: true })
    .then((result) => {
      if (result && result.message) {
        console.log(`[MSBT Data Catalogs] ${result.message}`);
      }
    })
    .catch((error) => {
      console.warn(`[MSBT Data Catalogs] soft refresh failed: ${error && error.message ? error.message : error}`);
    });
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
  mobileGateway.stop().catch(() => {});
  if (pythonHelperWorker) pythonHelperWorker.stop();
  if (hostProcessIsAlive()) {
    killProcessTree(mattHostProcess.pid);
  }
});
