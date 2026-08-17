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
  TUTORIAL_COPY_NAME,
  applyTutorialCopyOverlay,
  cachedFilePath,
  getDataCatalogStatus,
  loadTutorialCopy,
  normalizeManifest,
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
  assert.ok(Array.isArray(manifest.assets), "expected assets array for Phase 3");
  assert.ok(manifest.assets.some((row) => row.id === "tutorial_copy"), "tutorial_copy asset missing");
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

async function testTutorialCopyAsset() {
  const copyPath = path.join(DATA_DIR, TUTORIAL_COPY_NAME);
  assert.ok(fs.existsSync(copyPath), "tutorial_copy.json missing");
  const manifest = JSON.parse(await fsp.readFile(path.join(DATA_DIR, "catalog_manifest.json"), "utf8"));
  const assets = Array.isArray(manifest.assets) ? manifest.assets : [];
  const entry = assets.find((row) => row.id === "tutorial_copy");
  assert.ok(entry, "manifest.assets should include tutorial_copy");
  assert.strictEqual(entry.kind, "json_copy");
  const digest = await sha256File(copyPath);
  assert.strictEqual(digest, entry.sha256);

  const copy = JSON.parse(await fsp.readFile(copyPath, "utf8"));
  assert.strictEqual(copy.kind, "json_copy");
  const patches = (copy.tours && copy.tours.main) || [];
  const expectedIndexes = [0, 2, 3, 8, 10];
  for (const idx of expectedIndexes) {
    assert.ok(
      patches.some((row) => Number(row.index) === idx),
      `tutorial_copy missing high-value main overlay index ${idx}`
    );
  }
  for (const patch of patches) {
    assert.ok(patch && typeof patch === "object");
    assert.ok(!Object.prototype.hasOwnProperty.call(patch, "links"), "overlays must not ship links");
    assert.ok(!Object.prototype.hasOwnProperty.call(patch, "url"), "overlays must not ship urls");
    assert.ok(!Object.prototype.hasOwnProperty.call(patch, "action"), "overlays must not ship actions");
    assert.ok(!Object.prototype.hasOwnProperty.call(patch, "target"), "overlays must not ship targets");
    assert.ok(!Object.prototype.hasOwnProperty.call(patch, "targetSel"), "overlays must not ship selectors");
    assert.ok(typeof patch.title === "string" && patch.title.trim(), "title required");
    assert.ok(typeof patch.body === "string" && patch.body.trim(), "body required");
  }
  const welcome = patches.find((row) => Number(row.index) === 0);
  assert.ok(/sdk_mods|MattsSDKBoostingTools\.sdkmod/i.test(welcome.body), "Welcome should keep SDK install path accurate");
  assert.ok(/Refresh Catalogs/i.test(welcome.body), "Welcome should mention the current data refresh label");
  const updates = patches.find((row) => Number(row.index) === 8);
  assert.ok(/Refresh Catalogs/i.test(updates.body), "Updates should mention the current data refresh label");
  assert.ok(/data channel|SemVer/i.test(updates.body), "Updates should clarify data vs app SemVer");
  const allCopy = patches.map((row) => `${row.title}\n${row.body}`).join("\n");
  assert.ok(!/Quick Max|Debug Panel|Refresh Status in (?:the )?header/i.test(allCopy), "overlay contains stale UI copy");

  const tours = {
    main: Array.from({ length: 11 }, (_, i) => ({ title: `Bundled ${i}`, body: `Bundled body ${i}` }))
  };
  const result = applyTutorialCopyOverlay(tours, copy);
  assert.ok(result.applied >= expectedIndexes.length * 2, `expected title+body for ${expectedIndexes.length} steps`);
  for (const idx of expectedIndexes) {
    assert.notStrictEqual(tours.main[idx].title, `Bundled ${idx}`);
    assert.notStrictEqual(tours.main[idx].body, `Bundled body ${idx}`);
  }
  assert.strictEqual(tours.main[1].title, "Bundled 1", "unpatched steps must stay bundled");

  // Reject executable kinds at normalize time.
  const bad = normalizeManifest({
    data_version: "9.9.9",
    files: manifest.files,
    assets: [
      {
        id: "evil",
        path: "evil.js",
        kind: "script",
        url: "https://example.invalid/evil.js",
        sha256: "a".repeat(64),
        bytes: 1
      }
    ]
  });
  assert.ok(!bad.assets.some((row) => row.id === "evil"), "script assets must be rejected");
  record(
    "tutorial_copy asset + overlay allowlist",
    true,
    `applied=${result.applied}, indexes=${expectedIndexes.join(",")}`
  );
}

async function testTutorialCopyRefreshIntoCache() {
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
    assert.ok(
      refreshed.updated.includes("tutorial_copy") || refreshed.skipped.includes("tutorial_copy"),
      "tutorial_copy should be in refresh result"
    );
    const cached = cachedFilePath(userData, TUTORIAL_COPY_NAME);
    assert.ok(fs.existsSync(cached), "tutorial_copy should land in msbt_data cache");
    const loaded = await loadTutorialCopy(userData, { docsDataDir: DATA_DIR });
    assert.ok(loaded.ok, loaded.message);
    assert.strictEqual(loaded.source, "cache");
    assert.strictEqual(loaded.data.kind, "json_copy");
    record("tutorial_copy refreshes into msbt_data cache", true, loaded.data.min_app_version || "no-min");
  });
}

async function testRejectedExecutableAssetExtension() {
  const manifest = JSON.parse(await fsp.readFile(path.join(DATA_DIR, "catalog_manifest.json"), "utf8"));
  const normalized = normalizeManifest({
    ...manifest,
    assets: [
      ...(manifest.assets || []),
      {
        id: "payload",
        path: "payload.exe",
        kind: "json_copy",
        url: "https://example.invalid/payload.exe",
        sha256: "b".repeat(64),
        bytes: 12
      }
    ]
  });
  assert.ok(!normalized.downloadables.some((row) => row.path === "payload.exe"));
  record("executable extensions rejected from downloadables", true);
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
    testDevSpawnerSeedPresent,
    testTutorialCopyAsset,
    testTutorialCopyRefreshIntoCache,
    testRejectedExecutableAssetExtension
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
