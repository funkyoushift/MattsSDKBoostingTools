const fs = require("fs/promises");
const path = require("path");

const MOVEMENT_SETTINGS_VERSION = 1;
const MOVEMENT_SETTINGS_FILENAME = "movement_settings.json";

const DEFAULT_PRESET = {
  speedScale: "1.00",
  walkSpeed: "600",
  jumpHeight: "198",
  gravityScale: "1.00",
  stepHeight: "45",
  floorAngle: "44.8",
  floorZ: "0.71",
  sprintJumpGoal: "198",
  doubleJumpGoal: "198",
  slideJumpGoal: "198",
  glideSpeed: "1200",
  glideBoost: "0",
  glideAirControl: "0.60",
  dashSpeed: "2500",
  timeDilation: "1.00",
  individualJumpGoals: false,
  zeroVaultOnApply: false
};

function movementSettingsFilePath(userDataPath) {
  return path.join(userDataPath, MOVEMENT_SETTINGS_FILENAME);
}

function emptyMovementSettings() {
  return {
    version: MOVEMENT_SETTINGS_VERSION,
    preset: {},
    autoApplyOnStart: false,
    updated_at: ""
  };
}

function normalizePresetValue(value, fallback = "") {
  const text = String(value ?? fallback ?? "").trim();
  return text.slice(0, 64);
}

function normalizeBoolean(value) {
  if (typeof value === "boolean") return value;
  const text = String(value || "").trim().toLowerCase();
  return ["1", "true", "yes", "on"].includes(text);
}

function normalizeMovementPreset(rawPreset) {
  const source = rawPreset && typeof rawPreset === "object" ? rawPreset : {};
  const preset = {};

  Object.keys(DEFAULT_PRESET).forEach((key) => {
    const fallback = DEFAULT_PRESET[key];
    if (typeof fallback === "boolean") {
      preset[key] = normalizeBoolean(source[key]);
    } else {
      preset[key] = normalizePresetValue(source[key], fallback);
    }
  });

  return preset;
}

function normalizeMovementSettingsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const preset = source.preset && typeof source.preset === "object"
    ? normalizeMovementPreset(source.preset)
    : {};
  const updatedAt = String(source.updated_at || source.updatedAt || "").trim();

  return {
    data: {
      version: MOVEMENT_SETTINGS_VERSION,
      preset,
      autoApplyOnStart: normalizeBoolean(source.autoApplyOnStart || source.auto_apply_on_load),
      updated_at: updatedAt || new Date().toISOString()
    },
    warnings: []
  };
}

async function readMovementSettings(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    if (!text.trim()) {
      return {
        ok: true,
        data: emptyMovementSettings(),
        warnings: ["Movement settings file was empty; started clean."]
      };
    }
    const parsed = JSON.parse(text);
    const normalized = normalizeMovementSettingsPayload(parsed);
    return { ok: true, data: normalized.data, warnings: normalized.warnings };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { ok: true, data: emptyMovementSettings(), warnings: [] };
    }
    if (error instanceof SyntaxError) {
      return {
        ok: true,
        data: emptyMovementSettings(),
        warnings: [`Movement settings file was malformed and was ignored: ${error.message}`]
      };
    }
    return {
      ok: false,
      data: emptyMovementSettings(),
      warnings: [],
      message: String(error && error.message ? error.message : error)
    };
  }
}

async function writeMovementSettings(filePath, payload) {
  const normalized = normalizeMovementSettingsPayload({
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
  DEFAULT_PRESET,
  MOVEMENT_SETTINGS_FILENAME,
  MOVEMENT_SETTINGS_VERSION,
  emptyMovementSettings,
  movementSettingsFilePath,
  normalizeMovementPreset,
  normalizeMovementSettingsPayload,
  readMovementSettings,
  writeMovementSettings
};
