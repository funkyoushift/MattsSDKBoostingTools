#!/usr/bin/env node
"use strict";

/**
 * Headless self-test for MSBT remote data catalogs (no Electron GUI).
 *
 * Usage:
 *   node electron_poc/test_remote_data_catalogs.js
 */

const assert = require("assert");
const fs = require("fs");
const fsp = require("fs/promises");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const ROOT = path.resolve(__dirname, "..");
const DATA_DIR = path.join(ROOT, "docs", "data");
const RESOURCE_DIR = path.join(ROOT, "external_app", "v22_parts_codes_fixed", "resources");

const {
  loadBl4Catalog,
  preferLongerBase85Serial,
  validSerial
} = require("./bl4_codes_catalog");
const {
  cachedFilePath,
  getDataCatalogStatus,
  refreshRemoteDataCatalogs,
  resolveLocalCatalogPath,
  sha256File
} = require("./remote_data_catalogs");

const results = [];

function record(name, ok, detail = "") {
  results.push({ name, ok, detail });
  const mark = ok ? "PASS" : "FAIL";
  console.log(`[${mark}] ${name}${detail ? ` — ${detail}` : ""}`);
}

async function withTempUserData(fn) {
  const dir = await fsp.mkdtemp(path.join(os.tmpdir(), "msbt-data-catalog-"));
  try {
    return await fn(dir);
  } finally {
    await fsp.rm(dir, { recursive: true, force: true });
  }
}

async function testManifestHashes() {
  const manifest = JSON.parse(await fsp.readFile(path.join(DATA_DIR, "catalog_manifest.json"), "utf8"));
  assert.ok(manifest.data_version, "data_version missing");
  assert.ok(Array.isArray(manifest.files) && manifest.files.length >= 3, "expected Phase 1 files");
  for (const entry of manifest.files) {
    const filePath = path.join(DATA_DIR, entry.path);
    assert.ok(fs.existsSync(filePath), `missing ${entry.path}`);
    const digest = await sha256File(filePath);
    assert.strictEqual(digest, entry.sha256, `sha256 mismatch ${entry.id}`);
    assert.strictEqual(fs.statSync(filePath).size, entry.bytes, `bytes mismatch ${entry.id}`);
  }
  record("manifest sha256/bytes match docs/data", true, `data-v${manifest.data_version}, ${manifest.files.length} files`);
}

async function testRaidenSerial() {
  const loot = JSON.parse(
    await fsp.readFile(path.join(DATA_DIR, "MattsSDKBoostingTools_lootlemon_codes.json"), "utf8")
  );
  const entries = loot.entries || [];
  const raiden = entries.find((row) => String(row.name || "").toLowerCase() === "raiden");
  assert.ok(raiden, "Raiden missing from lootlemon seed");
  assert.ok(validSerial(raiden.serial), "Raiden serial invalid");
  assert.ok(raiden.serial.length >= 50, `Raiden serial looks truncated (${raiden.serial.length})`);
  // Prefer-longer helper still recovers manufacturer swaps if present.
  const recovered = preferLongerBase85Serial(raiden.serial.slice(0, 20), raiden.serial);
  assert.strictEqual(recovered.serial, raiden.serial);
  record("Lootlemon Raiden serial full in seed", true, `len=${raiden.serial.length}`);
}

async function testOfflineBundledLoad() {
  await withTempUserData(async (userData) => {
    // Empty cache → must fall back to bundled/docs seed.
    const resolved = await resolveLocalCatalogPath(userData, "MattsSDKBoostingTools_lootlemon_codes.json", {
      resourceDir: RESOURCE_DIR,
      docsDataDir: DATA_DIR
    });
    assert.strictEqual(resolved.source, "bundled");
    assert.ok(resolved.path);
    const catalog = await loadBl4Catalog(RESOURCE_DIR, {
      filePaths: {
        lootlemon: resolved.path,
        custom: path.join(RESOURCE_DIR, "custom_bl4_codes.json")
      }
    });
    assert.ok(catalog.ok);
    assert.ok(catalog.counts.lootlemon > 0);
    record("offline load uses bundled seed (no cache)", true, `lootlemon=${catalog.counts.lootlemon}`);
  });
}

async function testSimulatedRefreshUpdatesCache() {
  await withTempUserData(async (userData) => {
    const manifestUrl = pathToFileURL(path.join(DATA_DIR, "catalog_manifest.json")).href;
    const first = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(first.ok, first.message);
    assert.ok(first.updated.length > 0, "expected first refresh to populate cache");
    const lootCache = cachedFilePath(userData, "MattsSDKBoostingTools_lootlemon_codes.json");
    assert.ok(fs.existsSync(lootCache));
    const beforeHash = await sha256File(lootCache);

    // Second refresh should skip unchanged files.
    const second = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(second.ok);
    assert.ok(second.skipped.includes("lootlemon"));

    // Simulate upstream hash change: rewrite cache with different bytes, then restore seed via refresh.
    await fsp.writeFile(lootCache, `${JSON.stringify({ entries: [], note: "stale" }, null, 2)}\n`);
    const staleHash = await sha256File(lootCache);
    assert.notStrictEqual(staleHash, beforeHash);

    const third = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(third.ok, third.message);
    assert.ok(third.updated.includes("lootlemon"), `expected lootlemon update, got ${JSON.stringify(third)}`);
    const afterHash = await sha256File(lootCache);
    assert.strictEqual(afterHash, beforeHash);

    // Soft-fail: poison manifest URL and ensure previous cache survives.
    const poisoned = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      manifestUrls: ["https://example.invalid/catalog_manifest.json"],
      fetch: async () => {
        throw new Error("network down");
      }
    });
    assert.ok(poisoned.ok && poisoned.offline, "offline soft path should keep cached manifest");
    assert.ok(fs.existsSync(lootCache), "cache must not be wiped on failed refresh");
    record("simulated refresh updates cache by sha256; offline keeps last good", true, `data=${first.dataVersion}`);
  });
}

async function testStatusHelper() {
  await withTempUserData(async (userData) => {
    const status = await getDataCatalogStatus(userData, {
      resourceDir: RESOURCE_DIR,
      docsDataDir: DATA_DIR
    });
    assert.ok(status.ok);
    assert.ok(status.bundledManifest);
    assert.strictEqual(status.files.lootlemon.resolvedSource, "bundled");
    record("getDataCatalogStatus reports bundled sources", true, status.bundledManifest.data_version_label);
  });
}

async function main() {
  console.log("MSBT remote data catalog self-test");
  console.log(`ROOT=${ROOT}`);
  const started = new Date().toISOString();
  console.log(`started=${started}`);

  const tests = [
    testManifestHashes,
    testRaidenSerial,
    testOfflineBundledLoad,
    testSimulatedRefreshUpdatesCache,
    testStatusHelper
  ];

  for (const test of tests) {
    try {
      await test();
    } catch (error) {
      record(test.name, false, error && error.stack ? error.stack : String(error));
    }
  }

  const failed = results.filter((row) => !row.ok);
  console.log(`\n${results.length - failed.length}/${results.length} passed`);
  if (failed.length) {
    process.exitCode = 1;
  }

  return {
    started,
    finished: new Date().toISOString(),
    results,
    failed: failed.length
  };
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
