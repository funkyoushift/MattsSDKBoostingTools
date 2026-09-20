"use strict";

/**
 * Guardrail: "Electron updater is not available in this build." is unpackaged
 * `npm start` copy only. Packaged installer/portable must keep electron-updater
 * AND its runtime graph inside app.asar (v2.12.1 shipped the module but dropped
 * builder-util-runtime / js-yaml / lazy-val, so require() threw for installer users).
 *
 * Does not call GitHub. Dist checks run only when win-unpacked exists; the
 * installer build re-runs this after electron-builder so a missing dep fails the pack.
 * Run with: node test_updater_packaging.js
 */
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const {
  UNPACKAGED_UPDATER_MESSAGE,
  PACKAGED_LOAD_FAILURE_MESSAGE,
  REQUIRED_PACKAGED_UPDATER_MODULES,
  autoUpdaterGate,
  packagedLoadFailure
} = require("./updater_availability");

const root = __dirname;
const repoRoot = path.resolve(root, "..");
const mainJs = fs.readFileSync(path.join(root, "main.js"), "utf8");
const rendererJs = fs.readFileSync(path.join(root, "renderer.js"), "utf8");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));

assert.strictEqual(UNPACKAGED_UPDATER_MESSAGE, "Electron updater is not available in this build.");
assert.notStrictEqual(PACKAGED_LOAD_FAILURE_MESSAGE, UNPACKAGED_UPDATER_MESSAGE);

const unpackaged = autoUpdaterGate(false);
assert.strictEqual(unpackaged.enabled, false);
assert.strictEqual(unpackaged.message, UNPACKAGED_UPDATER_MESSAGE);
assert.strictEqual(autoUpdaterGate(true).enabled, true);

const loadFail = packagedLoadFailure(Object.assign(new Error("Cannot find module 'builder-util-runtime'"), { code: "MODULE_NOT_FOUND" }));
assert.strictEqual(loadFail.enabled, false);
assert.match(loadFail.message, /builder-util-runtime/);
assert.match(loadFail.message, /MODULE_NOT_FOUND/);
assert.ok(!String(loadFail.message).includes("not available in this build"));
assert.ok(!String(loadFail.error).includes("not available in this build"));

assert.match(mainJs, /require\("\.\/updater_availability"\)/, "main.js must use the updater availability gate");
assert.match(
  mainJs,
  /autoUpdaterGate\(app\.isPackaged\)/,
  "main.js must skip electron-updater when app.isPackaged is false"
);
assert.match(
  mainJs,
  /updaterProbe/,
  "packaged --smoke must probe electron-updater load so missing asar deps fail closed"
);
assert.ok(
  !mainJs.includes(`message: "${UNPACKAGED_UPDATER_MESSAGE}"`),
  "unpackaged-only updater copy must not be hardcoded as a packaged load-failure"
);
assert.ok(
  !rendererJs.includes(UNPACKAGED_UPDATER_MESSAGE),
  "renderer must not invent the unpackaged updater string"
);
assert.match(
  rendererJs,
  /updaterError/,
  "Updates UI must surface the real packaged updater error next to the installer line"
);

const publish = Array.isArray(pkg.build && pkg.build.publish) ? pkg.build.publish : [];
assert.ok(
  publish.some((entry) => entry && entry.provider === "github" && entry.owner === "funkyoushift" && entry.repo === "MattsSDKBoostingTools"),
  "electron-builder must publish via GitHub so packaged autoUpdater has a feed"
);
assert.ok(
  (pkg.build.extraResources || []).some((entry) => entry && entry.from === "../docs/releases/latest.json" && entry.to === "releases/latest.json"),
  "extraResources must bundle docs/releases/latest.json"
);

const deps = pkg.dependencies || {};
for (const name of REQUIRED_PACKAGED_UPDATER_MODULES) {
  if (name === "fs-extra" || name === "semver") continue;
  assert.ok(
    deps[name],
    `${name} must be a direct production dependency so electron-builder cannot drop it from app.asar`
  );
}

const unpacked = path.join(repoRoot, "dist_electron", "win-unpacked", "resources");
if (fs.existsSync(unpacked)) {
  const appUpdate = fs.readFileSync(path.join(unpacked, "app-update.yml"), "utf8");
  assert.match(appUpdate, /^provider:\s*github\s*$/m, "packaged app-update.yml must use the GitHub provider");
  assert.match(appUpdate, /^owner:\s*funkyoushift\s*$/m);
  assert.match(appUpdate, /^repo:\s*MattsSDKBoostingTools\s*$/m);

  const bundledManifest = JSON.parse(fs.readFileSync(path.join(unpacked, "releases", "latest.json"), "utf8"));
  assert.ok(bundledManifest.electron_updater_manifest_url, "bundled latest.json must point at latest.yml");
  if (bundledManifest.package_version !== pkg.version) {
    console.log(`stale dist package_version ${bundledManifest.package_version} (source ${pkg.version}); still requiring updater asar graph`);
  } else {
    assert.strictEqual(bundledManifest.package_version, pkg.version);
  }

  const asarPath = path.join(unpacked, "app.asar");
  assert.ok(fs.existsSync(asarPath), "packaged app.asar must exist");
  const asar = require("@electron/asar");
  const files = asar.listPackage(asarPath).map((entry) => String(entry).split("\\").join("/").replace(/^\//, ""));
  for (const name of REQUIRED_PACKAGED_UPDATER_MODULES) {
    const needle = `node_modules/${name}/package.json`;
    assert.ok(
      files.some((entry) => entry === needle || entry.endsWith(`/${needle}`)),
      `packaged app.asar must include ${name} (v2.12.1 installer omitted electron-updater runtime deps)`
    );
  }
  console.log("packaged updater artifacts ok");
} else {
  console.log("skip packaged asar checks; dist_electron/win-unpacked missing");
}

console.log("updater packaging ok");
