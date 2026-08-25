const fs = require("fs/promises");
const path = require("path");

const PREFS_VERSION = 1;
const PREFS_FILENAME = "matt_editor_prefs.json";
const MAX_PATH_LEN = 480;
const MAX_STEAM_ID_LEN = 64;
const SAVE_EXTENSIONS = new Set([".sav", ".yaml", ".yml", ".txt"]);

function prefsFilePath(userDataPath) {
  return path.join(userDataPath, PREFS_FILENAME);
}

function emptyPrefs() {
  return {
    version: PREFS_VERSION,
    steamId: "",
    sdkModsPath: "",
    lastSaveFile: "",
    lastSaveFolder: "",
    lastProfileFile: "",
    lastProfileFolder: "",
    lastExportFolder: "",
    lastLegitFolder: "",
    updated_at: ""
  };
}

function normalizePathValue(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  try {
    const resolved = path.resolve(text);
    if (!path.isAbsolute(resolved)) return "";
    if (resolved.length > MAX_PATH_LEN) return resolved.slice(0, MAX_PATH_LEN);
    return resolved;
  } catch {
    return "";
  }
}

function normalizeSteamId(value) {
  return String(value || "").trim().replace(/\s+/g, "").slice(0, MAX_STEAM_ID_LEN);
}

function looksLikeSteamOrEpicId(value) {
  const id = normalizeSteamId(value);
  if (!id) return "";
  if (/^7656119\d{10}$/.test(id)) return id;
  if (/^\d{17}$/.test(id)) return id;
  if (/^[0-9a-f]{32}$/i.test(id)) return id;
  return "";
}

/** BL4 keeps saves under SaveGames/<SteamID64 or Epic ID>/... */
function steamIdFromSavePath(filePath) {
  const text = String(filePath || "").trim();
  if (!text) return "";
  const parts = text.replace(/\\/g, "/").split("/").filter(Boolean);
  const saveGamesIdx = parts.findIndex((part) => part.toLowerCase() === "savegames");
  if (saveGamesIdx >= 0 && saveGamesIdx + 1 < parts.length) {
    const fromFolder = looksLikeSteamOrEpicId(parts[saveGamesIdx + 1]);
    if (fromFolder) return fromFolder;
  }
  for (const part of parts) {
    if (/^7656119\d{10}$/.test(part)) return part;
  }
  return "";
}

function folderFromFile(filePath) {
  const resolved = normalizePathValue(filePath);
  return resolved ? path.dirname(resolved) : "";
}

function allowedSaveExtension(filePath) {
  const ext = path.extname(String(filePath || "")).toLowerCase();
  return SAVE_EXTENSIONS.has(ext);
}

function normalizePrefsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const lastSaveFile = normalizePathValue(source.lastSaveFile || source.last_save_file);
  const lastProfileFile = normalizePathValue(source.lastProfileFile || source.last_profile_file);
  const lastSaveFolder = normalizePathValue(source.lastSaveFolder || source.last_save_folder) || folderFromFile(lastSaveFile);
  const lastProfileFolder = normalizePathValue(source.lastProfileFolder || source.last_profile_folder) || folderFromFile(lastProfileFile);
  return {
    data: {
      version: PREFS_VERSION,
      steamId: normalizeSteamId(source.steamId || source.steam_id || source.lastSteamEpicId),
      sdkModsPath: normalizePathValue(source.sdkModsPath || source.sdk_mods_path),
      lastSaveFile,
      lastSaveFolder,
      lastProfileFile,
      lastProfileFolder,
      lastExportFolder: normalizePathValue(source.lastExportFolder || source.last_export_folder) || lastSaveFolder,
      lastLegitFolder: normalizePathValue(source.lastLegitFolder || source.last_legit_folder),
      updated_at: String(source.updated_at || source.updatedAt || "").trim() || new Date().toISOString()
    },
    warnings: []
  };
}

async function readPrefs(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    if (!text.trim()) {
      return { ok: true, data: emptyPrefs(), warnings: ["Matt Editor prefs empty; started clean."] };
    }
    const normalized = normalizePrefsPayload(JSON.parse(text));
    return { ok: true, data: normalized.data, warnings: normalized.warnings };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { ok: true, data: emptyPrefs(), warnings: [] };
    }
    return {
      ok: false,
      data: emptyPrefs(),
      message: `Failed to read Matt Editor prefs: ${error && error.message ? error.message : error}`
    };
  }
}

async function writePrefs(filePath, payload) {
  const current = await readPrefs(filePath);
  const merged = { ...current.data, ...(payload && typeof payload === "object" ? payload : {}) };
  const normalized = normalizePrefsPayload(merged);
  normalized.data.updated_at = new Date().toISOString();
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(normalized.data, null, 2)}\n`, "utf8");
  return { ok: true, data: normalized.data, warnings: normalized.warnings };
}

module.exports = {
  PREFS_FILENAME,
  SAVE_EXTENSIONS,
  prefsFilePath,
  emptyPrefs,
  normalizePathValue,
  normalizeSteamId,
  looksLikeSteamOrEpicId,
  steamIdFromSavePath,
  folderFromFile,
  allowedSaveExtension,
  normalizePrefsPayload,
  readPrefs,
  writePrefs
};
