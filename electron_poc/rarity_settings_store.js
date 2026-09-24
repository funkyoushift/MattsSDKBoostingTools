const fs = require("fs/promises");
const path = require("path");
const { queueSettingsWrite } = require("./settings_write_queue");

const RARITY_SETTINGS_VERSION = 1;
const RARITY_SETTINGS_FILENAME = "rarity_settings.json";
const RARITY_KEYS = ["common", "uncommon", "rare", "epic", "legendary", "pearlescent"];

const DEFAULT_RARITY_PRESET = {
  common: 100,
  uncommon: 100,
  rare: 100,
  epic: 100,
  legendary: 100,
  pearlescent: 100
};

function raritySettingsFilePath(userDataPath) {
  return path.join(userDataPath, RARITY_SETTINGS_FILENAME);
}

function emptyRaritySettings() {
  return {
    version: RARITY_SETTINGS_VERSION,
    preset: { ...DEFAULT_RARITY_PRESET },
    rememberOnStart: false,
    updated_at: ""
  };
}

function normalizeBoolean(value) {
  if (typeof value === "boolean") return value;
  const text = String(value || "").trim().toLowerCase();
  return ["1", "true", "yes", "on"].includes(text);
}

function normalizePercent(value, fallback = 100) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(0, Math.min(100, Math.round(number)));
}

function normalizeRarityPreset(rawPreset) {
  const source = rawPreset && typeof rawPreset === "object" ? rawPreset : {};
  const preset = {};
  RARITY_KEYS.forEach((key) => {
    preset[key] = normalizePercent(source[key], DEFAULT_RARITY_PRESET[key]);
  });
  return preset;
}

function normalizeRaritySettingsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const updatedAt = String(source.updated_at || source.updatedAt || "").trim();
  return {
    data: {
      version: RARITY_SETTINGS_VERSION,
      preset: normalizeRarityPreset(source.preset),
      rememberOnStart: normalizeBoolean(source.rememberOnStart ?? source.remember_on_start),
      updated_at: updatedAt || new Date().toISOString()
    },
    warnings: []
  };
}

async function readRaritySettings(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    if (!text.trim()) {
      return {
        ok: true,
        data: emptyRaritySettings(),
        warnings: ["Rarity settings file was empty; started clean."]
      };
    }
    const parsed = JSON.parse(text);
    const normalized = normalizeRaritySettingsPayload(parsed);
    return { ok: true, data: normalized.data, warnings: normalized.warnings };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { ok: true, data: emptyRaritySettings(), warnings: [] };
    }
    if (error instanceof SyntaxError) {
      return {
        ok: true,
        data: emptyRaritySettings(),
        warnings: [`Rarity settings file was malformed and was ignored: ${error.message}`]
      };
    }
    return {
      ok: false,
      data: emptyRaritySettings(),
      warnings: [],
      message: String(error && error.message ? error.message : error)
    };
  }
}

function writeRaritySettings(filePath, payload) {
  return queueSettingsWrite(filePath, () => writeRaritySettingsNow(filePath, payload));
}

async function writeRaritySettingsNow(filePath, payload) {
  const normalized = normalizeRaritySettingsPayload({
    ...(payload || {}),
    updated_at: new Date().toISOString()
  });
  const directory = path.dirname(filePath);
  const tempPath = `${filePath}.tmp`;
  await fs.mkdir(directory, { recursive: true });
  await fs.writeFile(tempPath, `${JSON.stringify(normalized.data, null, 2)}\n`, "utf8");
  await fs.rename(tempPath, filePath);
  return { ok: true, data: normalized.data, warnings: normalized.warnings };
}

module.exports = {
  DEFAULT_RARITY_PRESET,
  RARITY_KEYS,
  RARITY_SETTINGS_FILENAME,
  RARITY_SETTINGS_VERSION,
  emptyRaritySettings,
  normalizeRarityPreset,
  normalizeRaritySettingsPayload,
  raritySettingsFilePath,
  readRaritySettings,
  writeRaritySettings
};
