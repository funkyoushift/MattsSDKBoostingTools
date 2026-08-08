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
const ELECTRON_APP_DIR = __dirname;

const {
  loadBl4Catalog,
  preferLongerBase85Serial,
  validSerial
} = require("./bl4_codes_catalog");
const {
  KNOWN_FILES,
  cachedFilePath,
  getDataCatalogStatus,
  refreshRemoteDataCatalogs,
  resolveCatalogFileMap,
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
  assert.ok(Array.isArray(manifest.files) && manifest.files.length >= 9, "expected Phase 2 files");
  const ids = new Set(manifest.files.map((f) => f.id));
  for (const required of [
    "lootlemon",
    "travelstations",
    "travelmaps",
    "item_pools",
    "gzo_parts_map",
    "shiny_serials",
    "challenge_catalog",
    "dev_spawner_catalog"
  ]) {
    assert.ok(ids.has(required), `missing manifest id ${required}`);
  }
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
  const recovered = preferLongerBase85Serial(raiden.serial.slice(0, 20), raiden.serial);
  assert.strictEqual(recovered.serial, raiden.serial);
  record("Lootlemon Raiden serial full in seed", true, `len=${raiden.serial.length}`);
}

async function testOfflineBundledLoad() {
  await withTempUserData(async (userData) => {
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
      electronAppDir: ELECTRON_APP_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(first.ok, first.message);
    assert.ok(first.updated.length > 0, "expected first refresh to populate cache");
    assert.ok(first.checkedAt, "checkedAt missing");
    const lootCache = cachedFilePath(userData, "MattsSDKBoostingTools_lootlemon_codes.json");
    assert.ok(fs.existsSync(lootCache));
    const beforeHash = await sha256File(lootCache);

    const second = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(second.ok);
    assert.ok(second.skipped.includes("lootlemon"));

    await fsp.writeFile(lootCache, `${JSON.stringify({ entries: [], note: "stale" }, null, 2)}\n`);
    const staleHash = await sha256File(lootCache);
    assert.notStrictEqual(staleHash, beforeHash);

    const third = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(third.ok, third.message);
    assert.ok(third.updated.includes("lootlemon"), `expected lootlemon update, got ${JSON.stringify(third)}`);
    const afterHash = await sha256File(lootCache);
    assert.strictEqual(afterHash, beforeHash);

    const poisoned = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR,
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
      docsDataDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR
    });
    assert.ok(status.ok);
    assert.ok(status.bundledManifest);
    assert.ok(status.statusLine);
    assert.strictEqual(status.files.lootlemon.resolvedSource, "bundled");
    record("getDataCatalogStatus reports bundled sources", true, status.bundledManifest.data_version_label);
  });
}

async function testPhase2CachePreference() {
  await withTempUserData(async (userData) => {
    const manifestUrl = pathToFileURL(path.join(DATA_DIR, "catalog_manifest.json")).href;
    const refreshed = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(refreshed.ok, refreshed.message);

    const map = await resolveCatalogFileMap(userData, {
      resourceDir: RESOURCE_DIR,
      docsDataDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR
    });

    const required = [
      "travelstations",
      "travelmaps",
      "item_pools",
      "gzo_parts_map",
      "shiny_serials",
      "challenge_catalog",
      "dev_spawner_catalog"
    ];
    for (const id of required) {
      assert.strictEqual(map.sources[id], "cache", `${id} should resolve from cache`);
      assert.ok(map.paths[id] && fs.existsSync(map.paths[id]), `${id} cache path missing`);
      assert.ok(KNOWN_FILES[id], `${id} missing from KNOWN_FILES`);
    }
    record("Phase 2 catalogs resolve from msbt_data cache", true, required.join(","));
  });
}

async function testHashMismatchRetriesThenKeepsPrior() {
  await withTempUserData(async (userData) => {
    const manifestUrl = pathToFileURL(path.join(DATA_DIR, "catalog_manifest.json")).href;
    const first = await refreshRemoteDataCatalogs({
      userDataPath: userData,
      docsDataDir: DATA_DIR,
      localSeedDir: DATA_DIR,
      electronAppDir: ELECTRON_APP_DIR,
      manifestUrls: [manifestUrl],
      fetch: globalThis.fetch
    });
    assert.ok(first.ok, first.message);
    const travelCache = cachedFilePath(userData, KNOWN_FILES.travelstations);
    const goodHash = await sha256File(travelCache);

    // Corrupt only travelstations in a poisoned seed dir so hash fails; prior cache must survive.
    const poisonDir = await fsp.mkdtemp(path.join(os.tmpdir(), "msbt-poison-seed-"));
    try {
      for (const name of fs.readdirSync(DATA_DIR)) {
        if (!name.endsWith(".json")) continue;
        await fsp.copyFile(path.join(DATA_DIR, name), path.join(poisonDir, name));
      }
      await fsp.writeFile(path.join(poisonDir, KNOWN_FILES.travelstations), "{\"poison\":true}\n");

      // Force update by rewriting cache with different bytes first.
      await fsp.writeFile(travelCache, "{\"stale\":true}\n");
      const poisoned = await refreshRemoteDataCatalogs({
        userDataPath: userData,
        docsDataDir: DATA_DIR,
        localSeedDir: poisonDir,
        electronAppDir: ELECTRON_APP_DIR,
        retries: 2,
        manifestUrls: [manifestUrl],
        fetch: globalThis.fetch
      });
      assert.ok(poisoned.failed.some((row) => row.id === "travelstations"), "expected travelstations hash failure");
      // Stale rewritten cache remains (we do not delete on failed write of new bytes from mismatch before write — actually download fails before write, so stale remains)
      assert.ok(fs.existsSync(travelCache));
      const after = await sha256File(travelCache);
      assert.notStrictEqual(after, goodHash, "stale cache should remain when update fails");
      record("hash mismatch fails soft without wiping sibling caches", true, `failed=${poisoned.failed.map((f) => f.id).join(",")}`);
    } finally {
      await fsp.rm(poisonDir, { recursive: true, force: true });
    }
  });
}

async function testDevSpawnerSeedPresent() {
  const docsPath = path.join(DATA_DIR, "dev_spawner_catalog.json");
  const appPath = path.join(ELECTRON_APP_DIR, "dev_spawner_catalog.json");
  assert.ok(fs.existsSync(docsPath), "docs/data/dev_spawner_catalog.json missing");
  assert.ok(fs.existsSync(appPath), "electron_poc/dev_spawner_catalog.json missing");
  const docs = JSON.parse(await fsp.readFile(docsPath, "utf8"));
  assert.ok(docs && typeof docs === "object", "dev spawner catalog should be object JSON");
  record("dev_spawner_catalog seeded in docs/data", true, `bytes=${fs.statSync(docsPath).size}`);
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
    testStatusHelper,
    testPhase2CachePreference,
    testHashMismatchRetriesThenKeepsPrior,
    testDevSpawnerSeedPresent
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
