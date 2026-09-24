const fs = require("fs/promises");
const path = require("path");
const { queueSettingsWrite } = require("./settings_write_queue");

const WALKTHROUGH_VERSION = 1;
const WALKTHROUGH_FILENAME = "walkthrough_settings.json";

function walkthroughSettingsFilePath(userDataPath) {
  return path.join(userDataPath, WALKTHROUGH_FILENAME);
}

function emptyWalkthroughSettings() {
  return {
    version: WALKTHROUGH_VERSION,
    dismissed: false,
    appVersion: "",
    dontShowAgain: false,
    updated_at: ""
  };
}

function normalizeBoolean(value) {
  if (typeof value === "boolean") return value;
  const text = String(value || "").trim().toLowerCase();
  return ["1", "true", "yes", "on"].includes(text);
}

function normalizeWalkthroughSettingsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const updatedAt = String(source.updated_at || source.updatedAt || "").trim();
  return {
    data: {
      version: WALKTHROUGH_VERSION,
      dismissed: normalizeBoolean(source.dismissed),
      appVersion: String(source.appVersion || "").trim(),
      dontShowAgain: normalizeBoolean(source.dontShowAgain ?? source.dont_show_again),
      updated_at: updatedAt || new Date().toISOString()
    },
    warnings: []
  };
}

async function readWalkthroughSettings(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    if (!text.trim()) {
      return { ok: true, data: emptyWalkthroughSettings(), warnings: ["Walkthrough settings empty; started clean."] };
    }
    const normalized = normalizeWalkthroughSettingsPayload(JSON.parse(text));
    return { ok: true, data: normalized.data, warnings: normalized.warnings };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { ok: true, data: emptyWalkthroughSettings(), warnings: [] };
    }
    return {
      ok: false,
      data: emptyWalkthroughSettings(),
      message: `Failed to read walkthrough settings: ${error && error.message ? error.message : error}`
    };
  }
}

function writeWalkthroughSettings(filePath, payload) {
  return queueSettingsWrite(filePath, () => writeWalkthroughSettingsNow(filePath, payload));
}

async function writeWalkthroughSettingsNow(filePath, payload) {
  const normalized = normalizeWalkthroughSettingsPayload(payload);
  normalized.data.updated_at = new Date().toISOString();
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const tempPath = `${filePath}.tmp`;
  await fs.writeFile(tempPath, `${JSON.stringify(normalized.data, null, 2)}\n`, "utf8");
  await fs.rename(tempPath, filePath);
  return { ok: true, data: normalized.data, warnings: normalized.warnings };
}

module.exports = {
  walkthroughSettingsFilePath,
  emptyWalkthroughSettings,
  readWalkthroughSettings,
  writeWalkthroughSettings
};
