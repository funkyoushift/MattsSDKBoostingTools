"use strict";

/**
 * Packaged installer/portable builds must load electron-updater.
 * The "not available in this build" copy is unpackaged `npm start` only.
 */

const UNPACKAGED_UPDATER_MESSAGE = "Electron updater is not available in this build.";
const PACKAGED_LOAD_FAILURE_MESSAGE = "Electron updater failed to load.";

// Direct production packages that electron-builder must copy into app.asar.
// Transitive electron-updater deps were dropped from v2.12.1 because they are
// also used by electron-builder (dev) and got classified off the pack list.
const REQUIRED_PACKAGED_UPDATER_MODULES = [
  "electron-updater",
  "builder-util-runtime",
  "lazy-val",
  "lodash.isequal",
  "lodash.escaperegexp",
  "js-yaml",
  "tiny-typed-emitter",
  "fs-extra",
  "semver"
];

function autoUpdaterGate(isPackaged) {
  if (!isPackaged) {
    return {
      enabled: false,
      status: "unavailable",
      message: UNPACKAGED_UPDATER_MESSAGE,
      error: ""
    };
  }
  return { enabled: true };
}

function formatUpdaterError(error) {
  const detail = String(error && error.message ? error.message : error);
  const code = error && error.code ? ` (${error.code})` : "";
  return `${detail}${code}`;
}

function packagedLoadFailure(error) {
  const detail = formatUpdaterError(error);
  return {
    enabled: false,
    status: "error",
    message: `${PACKAGED_LOAD_FAILURE_MESSAGE}: ${detail}`,
    error: detail
  };
}

module.exports = {
  UNPACKAGED_UPDATER_MESSAGE,
  PACKAGED_LOAD_FAILURE_MESSAGE,
  REQUIRED_PACKAGED_UPDATER_MODULES,
  autoUpdaterGate,
  formatUpdaterError,
  packagedLoadFailure
};
