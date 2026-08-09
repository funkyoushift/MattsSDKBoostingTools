"use strict";

/**
 * oak2-mod-manager v0.3 detect / download / install helpers for MSBT Electron.
 *
 * Official unmodified release asset is cached under Electron userData (not vendored in git).
 * LGPL-3.0: https://github.com/bl-sdk/oak2-mod-manager
 */

const fsSync = require("fs");
const fs = require("fs/promises");
const path = require("path");
const os = require("os");
const { createHash } = require("crypto");
const { execFile } = require("child_process");
const { promisify } = require("util");

const execFileAsync = promisify(execFile);

const OAK2_VERSION = "0.3";
const OAK2_RELEASE_TAG = "v0.3";
const OAK2_ZIP_NAME = "oak2-sdk.zip";
const OAK2_DOWNLOAD_URL =
  "https://github.com/bl-sdk/oak2-mod-manager/releases/download/v0.3/oak2-sdk.zip";
const OAK2_SHA256 = "602675446abed184169fa158be3c8bc81777a71203581e4a248eca8a3d00b5c7";
const OAK2_REPO_URL = "https://github.com/bl-sdk/oak2-mod-manager";
const OAK2_LICENSE_URL = "https://github.com/bl-sdk/oak2-mod-manager/blob/master/LICENSE";
const OAK2_INSTALL_GUIDE_URL = "https://bl-sdk.github.io/oak2-mod-db/";
const OAK2_LICENSE_SPDX = "LGPL-3.0";

/** Mods MSBT needs enabled via sdk_mods/settings/<module>.json {"enabled": true}. */
const REQUIRED_ENABLED_MODS = [
  { moduleName: "MattsSDKBoostingTools", label: "MattsSDKBoostingTools" },
  { moduleName: "ActorScriptDeployer", label: "ActorScriptDeployer" }
];

const OAK2_SDK_MODS_CORE_FILES = [
  "__main__.py",
  "mods_base.sdkmod",
  "console_mod_menu.sdkmod"
];

const OAK2_SDK_MODS_CORE_DIRS = ["keybinds", ".stubs"];

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

function parseSteamLibraryFoldersVdf(text) {
  const roots = [];
  const re = /"path"\s+"([^"]+)"/g;
  let match = re.exec(text || "");
  while (match) {
    roots.push(match[1].replace(/\\\\/g, "\\"));
    match = re.exec(text || "");
  }
  return roots;
}

function steamRootCandidates() {
  return uniquePaths([
    path.join(process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)", "Steam"),
    path.join(process.env.ProgramFiles || "C:\\Program Files", "Steam")
  ]);
}

function steamLibraryRoots() {
  const roots = [];
  for (const steamRoot of steamRootCandidates()) {
    roots.push(steamRoot);
    const vdfPath = path.join(steamRoot, "steamapps", "libraryfolders.vdf");
    try {
      const text = fsSync.readFileSync(vdfPath, "utf8");
      roots.push(...parseSteamLibraryFoldersVdf(text));
    } catch {
      // Steam may not be installed in the default location.
    }
  }
  return uniquePaths(roots);
}

function epicGameRootCandidates() {
  return uniquePaths([
    path.join(process.env.ProgramFiles || "C:\\Program Files", "Epic Games", "Borderlands 4"),
    path.join(process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)", "Epic Games", "Borderlands 4")
  ]);
}

function bl4GameRootCandidates() {
  const candidates = [...epicGameRootCandidates()];
  for (const libraryRoot of steamLibraryRoots()) {
    candidates.push(path.join(libraryRoot, "steamapps", "common", "Borderlands 4"));
    candidates.push(path.join(libraryRoot, "common", "Borderlands 4"));
  }
  return uniquePaths(candidates);
}

function bl4SdkModsCandidates() {
  return uniquePaths(bl4GameRootCandidates().map((root) => path.join(root, "sdk_mods")));
}

function gameRootFromSdkModsPath(sdkModsPath) {
  const normalized = path.resolve(String(sdkModsPath || "").trim());
  if (!normalized) return "";
  if (path.basename(normalized).toLowerCase() !== "sdk_mods") return "";
  return path.dirname(normalized);
}

function sdkModsPathFromGameRoot(gameRoot) {
  const root = path.resolve(String(gameRoot || "").trim());
  if (!root) return "";
  return path.join(root, "sdk_mods");
}

function pluginsDirFromGameRoot(gameRoot) {
  return path.join(String(gameRoot || ""), "OakGame", "Binaries", "Win64", "Plugins");
}

function parseOak2DisplayVersion(tomlText) {
  const text = String(tomlText || "");
  const match = text.match(/^\s*display_version\s*=\s*"([^"]+)"/m);
  return match ? String(match[1] || "").trim() : "";
}

function oak2VersionLooksLikeRequired(displayVersion) {
  const value = String(displayVersion || "").trim();
  if (!value) return false;
  return /^0\.3(\b|[^\d])/i.test(value) || value.toLowerCase().startsWith("0.3");
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function sha256File(filePath) {
  const data = await fs.readFile(filePath);
  return createHash("sha256").update(data).digest("hex");
}

function cacheRoots(userDataPath) {
  const root = path.join(String(userDataPath || ""), "oak2-cache");
  return {
    root,
    zipPath: path.join(root, `oak2-sdk-${OAK2_RELEASE_TAG}.zip`),
    extractDir: path.join(root, `extracted-${OAK2_RELEASE_TAG}`),
    licenseDir: path.join(root, "licenses"),
    noticePath: path.join(root, "OAK2_NOTICE.txt")
  };
}

async function writeOak2LicenseNotice(userDataPath) {
  const caches = cacheRoots(userDataPath);
  await fs.mkdir(caches.licenseDir, { recursive: true });
  const notice = [
    "Third-party component: oak2-mod-manager (BL4 PythonSDK Mod Manager)",
    "",
    `Version: ${OAK2_RELEASE_TAG}`,
    `License: ${OAK2_LICENSE_SPDX}`,
    `Source / project: ${OAK2_REPO_URL}`,
    `License text: ${OAK2_LICENSE_URL}`,
    `Official release asset: ${OAK2_DOWNLOAD_URL}`,
    `Install guide: ${OAK2_INSTALL_GUIDE_URL}`,
    "",
    "MSBT downloads the official unmodified oak2-sdk.zip release asset and caches it under",
    "this app's userData folder. oak2-mod-manager is LGPL-3.0; see the upstream LICENSE",
    "and https://www.gnu.org/licenses/ for GPL/LGPL terms.",
    ""
  ].join("\n");
  await fs.writeFile(caches.noticePath, notice, "utf8");
  return caches.noticePath;
}

async function inspectOak2Install(gameRoot) {
  const root = path.resolve(String(gameRoot || "").trim());
  if (!root) {
    return {
      present: false,
      ok: false,
      versionOk: false,
      gameRoot: "",
      sdkModsPath: "",
      displayVersion: "",
      markers: {},
      message: "No Borderlands 4 game folder was provided."
    };
  }

  const sdkModsPath = sdkModsPathFromGameRoot(root);
  const pluginsDir = pluginsDirFromGameRoot(root);
  const markers = {
    dsound: await fileExists(path.join(root, "OakGame", "Binaries", "Win64", "dsound.dll")),
    unrealsdkDll: await fileExists(path.join(pluginsDir, "unrealsdk.dll")),
    pyunrealsdkDll: await fileExists(path.join(pluginsDir, "pyunrealsdk.dll")),
    unrealsdkToml: await fileExists(path.join(pluginsDir, "unrealsdk.toml")),
    mainPy: await fileExists(path.join(sdkModsPath, "__main__.py")),
    modsBase: await fileExists(path.join(sdkModsPath, "mods_base.sdkmod")),
    consoleModMenu: await fileExists(path.join(sdkModsPath, "console_mod_menu.sdkmod"))
  };

  let displayVersion = "";
  if (markers.unrealsdkToml) {
    try {
      const toml = await fs.readFile(path.join(pluginsDir, "unrealsdk.toml"), "utf8");
      displayVersion = parseOak2DisplayVersion(toml);
    } catch {
      displayVersion = "";
    }
  }

  const corePresent =
    markers.dsound &&
    markers.unrealsdkDll &&
    markers.pyunrealsdkDll &&
    markers.unrealsdkToml &&
    markers.mainPy &&
    markers.modsBase;
  const versionOk = oak2VersionLooksLikeRequired(displayVersion);
  const present = Boolean(corePresent);
  const ok = present && versionOk;

  let message = "oak2-mod-manager was not detected in this Borderlands 4 folder.";
  if (ok) {
    message = `oak2-mod-manager detected: ${displayVersion || OAK2_RELEASE_TAG}.`;
  } else if (present && !versionOk) {
    message = `SDK files were found, but display_version is "${displayVersion || "unknown"}" (need ${OAK2_RELEASE_TAG}).`;
  } else if (markers.unrealsdkDll || markers.mainPy) {
    message = "Partial SDK install detected; some oak2-mod-manager v0.3 files are missing.";
  }

  return {
    present,
    ok,
    versionOk,
    gameRoot: root,
    sdkModsPath,
    displayVersion,
    requiredVersion: OAK2_VERSION,
    requiredTag: OAK2_RELEASE_TAG,
    markers,
    downloadUrl: OAK2_DOWNLOAD_URL,
    repoUrl: OAK2_REPO_URL,
    licenseUrl: OAK2_LICENSE_URL,
    installGuideUrl: OAK2_INSTALL_GUIDE_URL,
    message
  };
}

async function readModEnabledState(sdkModsPath, moduleName) {
  const settingsPath = path.join(sdkModsPath, "settings", `${moduleName}.json`);
  if (!(await fileExists(settingsPath))) {
    return { available: false, enabled: false, path: settingsPath, settings: null };
  }
  try {
    const settings = JSON.parse(await fs.readFile(settingsPath, "utf8"));
    return {
      available: true,
      enabled: Boolean(settings && settings.enabled),
      path: settingsPath,
      settings
    };
  } catch (error) {
    return {
      available: true,
      enabled: false,
      path: settingsPath,
      settings: null,
      error: String(error && error.message ? error.message : error)
    };
  }
}

async function enableRequiredMods(sdkModsPath, options = {}) {
  const modsPath = path.resolve(String(sdkModsPath || "").trim());
  if (!modsPath || path.basename(modsPath).toLowerCase() !== "sdk_mods") {
    return { ok: false, message: "Choose a Borderlands 4 sdk_mods folder.", mods: [] };
  }
  const settingsDir = path.join(modsPath, "settings");
  await fs.mkdir(settingsDir, { recursive: true });

  const mods = [];
  const list = Array.isArray(options.mods) && options.mods.length
    ? options.mods
    : REQUIRED_ENABLED_MODS;

  for (const entry of list) {
    const moduleName = String(entry.moduleName || entry || "").trim();
    if (!moduleName) continue;
    const settingsPath = path.join(settingsDir, `${moduleName}.json`);
    let existing = {};
    if (await fileExists(settingsPath)) {
      try {
        existing = JSON.parse(await fs.readFile(settingsPath, "utf8")) || {};
      } catch {
        existing = {};
      }
    }
    const next = { ...existing, enabled: true };
    await fs.writeFile(settingsPath, `${JSON.stringify(next, null, 4)}\n`, "utf8");
    mods.push({
      moduleName,
      label: entry.label || moduleName,
      path: settingsPath,
      enabled: true
    });
  }

  return {
    ok: true,
    path: modsPath,
    settingsDir,
    mods,
    message: `Enabled ${mods.map((m) => m.moduleName).join(", ")} via sdk_mods/settings/*.json.`
  };
}

async function requiredModsStatus(sdkModsPath) {
  const modsPath = path.resolve(String(sdkModsPath || "").trim());
  const mods = [];
  for (const entry of REQUIRED_ENABLED_MODS) {
    const state = await readModEnabledState(modsPath, entry.moduleName);
    const installedFile =
      entry.moduleName === "MattsSDKBoostingTools"
        ? path.join(modsPath, "MattsSDKBoostingTools.sdkmod")
        : path.join(modsPath, "ActorScriptDeployer", "__init__.py");
    mods.push({
      ...entry,
      installed: await fileExists(installedFile),
      ...state
    });
  }
  const allInstalled = mods.every((m) => m.installed);
  const allEnabled = mods.every((m) => m.enabled);
  return {
    ok: allInstalled && allEnabled,
    allInstalled,
    allEnabled,
    mods,
    message: allInstalled && allEnabled
      ? "Required MSBT mods are installed and marked enabled."
      : "One or more required MSBT mods are missing or not marked enabled."
  };
}

async function downloadToFile(url, destination, options = {}) {
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (typeof fetchImpl !== "function") {
    throw new Error("fetch is not available in this Electron/Node runtime.");
  }
  const response = await fetchImpl(String(url), { redirect: "follow" });
  if (!response.ok) {
    throw new Error(`Download failed (${response.status}) for ${url}`);
  }
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, buffer);
  return {
    path: destination,
    bytes: buffer.length,
    sha256: createHash("sha256").update(buffer).digest("hex")
  };
}

async function ensureOak2ZipCached(userDataPath, options = {}) {
  const caches = cacheRoots(userDataPath);
  await fs.mkdir(caches.root, { recursive: true });
  await writeOak2LicenseNotice(userDataPath);

  const force = Boolean(options.forceDownload);
  if (!force && (await fileExists(caches.zipPath))) {
    const hash = await sha256File(caches.zipPath);
    if (hash.toLowerCase() === OAK2_SHA256.toLowerCase()) {
      return {
        ok: true,
        cached: true,
        path: caches.zipPath,
        sha256: hash,
        message: "Using cached official oak2-sdk.zip (hash verified)."
      };
    }
  }

  const downloaded = await downloadToFile(OAK2_DOWNLOAD_URL, caches.zipPath, options);
  if (downloaded.sha256.toLowerCase() !== OAK2_SHA256.toLowerCase()) {
    return {
      ok: false,
      path: caches.zipPath,
      sha256: downloaded.sha256,
      expectedSha256: OAK2_SHA256,
      message: "Downloaded oak2-sdk.zip failed SHA-256 verification; leaving file for inspection."
    };
  }
  return {
    ok: true,
    cached: false,
    path: caches.zipPath,
    sha256: downloaded.sha256,
    bytes: downloaded.bytes,
    message: "Downloaded official oak2-sdk.zip and verified SHA-256."
  };
}

async function extractZip(zipPath, destinationDir) {
  await fs.rm(destinationDir, { recursive: true, force: true });
  await fs.mkdir(destinationDir, { recursive: true });
  // Windows 10+ ships tar.exe which extracts zip archives.
  await execFileAsync("tar", ["-xf", zipPath, "-C", destinationDir], {
    windowsHide: true
  });
  const oakGame = path.join(destinationDir, "OakGame");
  const sdkMods = path.join(destinationDir, "sdk_mods");
  if (!(await fileExists(oakGame)) || !(await fileExists(sdkMods))) {
    throw new Error("Extracted oak2-sdk.zip is missing OakGame/ or sdk_mods/.");
  }
  return { oakGame, sdkMods, destinationDir };
}

function isPermissionError(error) {
  const code = error && error.code ? String(error.code) : "";
  const message = String(error && error.message ? error.message : error).toLowerCase();
  return code === "EPERM" || code === "EACCES" || /access is denied|permission denied|eacces|eperm/.test(message);
}

async function copyPathRecursive(source, destination) {
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.cp(source, destination, { recursive: true, force: true });
}

function buildElevatedCopyScript(pairs) {
  const lines = ["$ErrorActionPreference = 'Stop'"];
  for (const pair of pairs) {
    const src = String(pair.source || "").replace(/'/g, "''");
    const dest = String(pair.destination || "").replace(/'/g, "''");
    lines.push(`$src = '${src}'`);
    lines.push(`$dest = '${dest}'`);
    lines.push("$parent = Split-Path -Parent $dest");
    lines.push("if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }");
    lines.push("Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force");
  }
  return `${lines.join("\n")}\n`;
}

async function elevatedCopyForest(pairs) {
  if (process.platform !== "win32") {
    throw new Error("Elevated install is only implemented for Windows.");
  }
  const scriptPath = path.join(os.tmpdir(), `msbt-oak2-elevate-${Date.now()}.ps1`);
  await fs.writeFile(scriptPath, buildElevatedCopyScript(pairs), "utf8");
  try {
    await execFileAsync(
      "powershell.exe",
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        `Start-Process -FilePath powershell.exe -Verb RunAs -Wait -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','${scriptPath.replace(/'/g, "''")}')`
      ],
      { windowsHide: true }
    );
  } finally {
    await fs.rm(scriptPath, { force: true }).catch(() => {});
  }
}

async function copyWithOptionalElevation(pairs) {
  try {
    for (const pair of pairs) {
      await copyPathRecursive(pair.source, pair.destination);
    }
    return { elevated: false };
  } catch (error) {
    if (!isPermissionError(error)) throw error;
    await elevatedCopyForest(pairs);
    return { elevated: true };
  }
}

function buildOak2CopyPairs(extractedRoot, gameRoot) {
  const pairs = [];
  const extractedOak = path.join(extractedRoot, "OakGame");
  const extractedMods = path.join(extractedRoot, "sdk_mods");
  pairs.push({
    source: extractedOak,
    destination: path.join(gameRoot, "OakGame")
  });
  for (const name of OAK2_SDK_MODS_CORE_FILES) {
    pairs.push({
      source: path.join(extractedMods, name),
      destination: path.join(gameRoot, "sdk_mods", name)
    });
  }
  for (const name of OAK2_SDK_MODS_CORE_DIRS) {
    pairs.push({
      source: path.join(extractedMods, name),
      destination: path.join(gameRoot, "sdk_mods", name)
    });
  }
  // Ensure settings directory exists without wiping user JSON files.
  pairs.push({
    source: path.join(extractedMods, "settings"),
    destination: path.join(gameRoot, "sdk_mods", "settings")
  });
  return pairs;
}

async function installOak2FromCache(userDataPath, gameRoot, options = {}) {
  const root = path.resolve(String(gameRoot || "").trim());
  if (!root) {
    return { ok: false, message: "No Borderlands 4 game folder was provided." };
  }
  if (!(await fileExists(root))) {
    return { ok: false, gameRoot: root, message: `Borderlands 4 folder does not exist: ${root}` };
  }

  const dryRun = Boolean(options.dryRun);
  let zipInfo;
  try {
    zipInfo = await ensureOak2ZipCached(userDataPath, options);
  } catch (error) {
    return {
      ok: false,
      gameRoot: root,
      message: String(error && error.message ? error.message : error)
    };
  }
  if (!zipInfo.ok) return { ...zipInfo, gameRoot: root };

  const caches = cacheRoots(userDataPath);
  if (dryRun) {
    return {
      ok: true,
      dryRun: true,
      gameRoot: root,
      sdkModsPath: sdkModsPathFromGameRoot(root),
      zipPath: zipInfo.path,
      sha256: zipInfo.sha256,
      copyPairs: buildOak2CopyPairs(caches.extractDir, root).map((p) => ({
        source: p.source,
        destination: p.destination
      })),
      message: "Dry-run: oak2 zip verified; no files were written to the game folder."
    };
  }

  await extractZip(zipInfo.path, caches.extractDir);
  const pairs = buildOak2CopyPairs(caches.extractDir, root);
  // Always create sdk_mods before merge copies.
  await fs.mkdir(path.join(root, "sdk_mods"), { recursive: true }).catch(async (error) => {
    if (!isPermissionError(error)) throw error;
    await elevatedCopyForest([
      {
        source: path.join(caches.extractDir, "sdk_mods", "settings"),
        destination: path.join(root, "sdk_mods", "settings")
      }
    ]);
  });

  const copyResult = await copyWithOptionalElevation(pairs);
  const detection = await inspectOak2Install(root);
  return {
    ok: detection.ok,
    elevated: Boolean(copyResult.elevated),
    gameRoot: root,
    sdkModsPath: detection.sdkModsPath,
    zipPath: zipInfo.path,
    sha256: zipInfo.sha256,
    oak2: detection,
    noticePath: await writeOak2LicenseNotice(userDataPath),
    message: detection.ok
      ? `oak2-mod-manager ${OAK2_RELEASE_TAG} installed into ${root}.${copyResult.elevated ? " Used elevated copy for Program Files." : ""}`
      : `oak2 install finished but verification failed: ${detection.message}`
  };
}

async function resolveGameRoot(rawSdkModsOrGamePath = "") {
  const raw = String(rawSdkModsOrGamePath || "").trim();
  if (raw) {
    const resolved = path.resolve(raw);
    if (path.basename(resolved).toLowerCase() === "sdk_mods") {
      return gameRootFromSdkModsPath(resolved);
    }
    if (await fileExists(path.join(resolved, "OakGame"))) {
      return resolved;
    }
    if (await fileExists(path.join(resolved, "sdk_mods"))) {
      return resolved;
    }
    // Treat as game root aspirationally when browsing a folder named Borderlands 4.
    return resolved;
  }
  for (const candidate of bl4GameRootCandidates()) {
    if (await fileExists(candidate)) return candidate;
  }
  return "";
}

module.exports = {
  OAK2_VERSION,
  OAK2_RELEASE_TAG,
  OAK2_ZIP_NAME,
  OAK2_DOWNLOAD_URL,
  OAK2_SHA256,
  OAK2_REPO_URL,
  OAK2_LICENSE_URL,
  OAK2_INSTALL_GUIDE_URL,
  OAK2_LICENSE_SPDX,
  REQUIRED_ENABLED_MODS,
  uniquePaths,
  parseSteamLibraryFoldersVdf,
  steamLibraryRoots,
  epicGameRootCandidates,
  bl4GameRootCandidates,
  bl4SdkModsCandidates,
  gameRootFromSdkModsPath,
  sdkModsPathFromGameRoot,
  parseOak2DisplayVersion,
  oak2VersionLooksLikeRequired,
  cacheRoots,
  writeOak2LicenseNotice,
  inspectOak2Install,
  readModEnabledState,
  enableRequiredMods,
  requiredModsStatus,
  ensureOak2ZipCached,
  extractZip,
  buildOak2CopyPairs,
  installOak2FromCache,
  resolveGameRoot,
  isPermissionError,
  // exported for tests
  downloadToFile,
  sha256File
};
