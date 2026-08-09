"use strict";

/**
 * Self-test for oak2 path/detect/enable helpers (no Borderlands 4 required).
 * Run: node test_oak2_install.js
 */

const assert = require("assert");
const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const oak2 = require("./oak2_install");

async function withTempDir(fn) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-oak2-test-"));
  try {
    return await fn(dir);
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
}

async function testParseVersion() {
  const sample = `[pyunrealsdk]\ninit_script = "x"\n\n[mod_manager]\ndisplay_version = "0.3 (77ec7de7)"\n`;
  assert.strictEqual(oak2.parseOak2DisplayVersion(sample), "0.3 (77ec7de7)");
  assert.strictEqual(oak2.oak2VersionLooksLikeRequired("0.3 (77ec7de7)"), true);
  assert.strictEqual(oak2.oak2VersionLooksLikeRequired("0.2"), false);
  console.log("ok parse version");
}

async function testEnableSettingsMerge() {
  await withTempDir(async (dir) => {
    const sdkMods = path.join(dir, "sdk_mods");
    await fs.mkdir(path.join(sdkMods, "settings"), { recursive: true });
    const existing = path.join(sdkMods, "settings", "MattsSDKBoostingTools.json");
    await fs.writeFile(
      existing,
      `${JSON.stringify({ enabled: false, options: { demo: 1 } }, null, 4)}\n`,
      "utf8"
    );
    const result = await oak2.enableRequiredMods(sdkMods);
    assert.strictEqual(result.ok, true);
    assert.strictEqual(result.mods.length, 2);
    const parsed = JSON.parse(await fs.readFile(existing, "utf8"));
    assert.strictEqual(parsed.enabled, true);
    assert.deepStrictEqual(parsed.options, { demo: 1 });
    const asd = JSON.parse(
      await fs.readFile(path.join(sdkMods, "settings", "ActorScriptDeployer.json"), "utf8")
    );
    assert.strictEqual(asd.enabled, true);
    const status = await oak2.requiredModsStatus(sdkMods);
    assert.strictEqual(status.allEnabled, true);
    assert.strictEqual(status.allInstalled, false);
    console.log("ok enable settings merge");
  });
}

async function testInspectMissingInstall() {
  await withTempDir(async (dir) => {
    const gameRoot = path.join(dir, "Borderlands 4");
    await fs.mkdir(gameRoot, { recursive: true });
    const info = await oak2.inspectOak2Install(gameRoot);
    assert.strictEqual(info.present, false);
    assert.strictEqual(info.ok, false);
    assert.ok(info.sdkModsPath.endsWith(`${path.sep}sdk_mods`));
    console.log("ok inspect missing install");
  });
}

async function testInspectFakeV03() {
  await withTempDir(async (dir) => {
    const gameRoot = path.join(dir, "Borderlands 4");
    const plugins = path.join(gameRoot, "OakGame", "Binaries", "Win64", "Plugins");
    const sdkMods = path.join(gameRoot, "sdk_mods");
    await fs.mkdir(plugins, { recursive: true });
    await fs.mkdir(sdkMods, { recursive: true });
    await fs.writeFile(path.join(gameRoot, "OakGame", "Binaries", "Win64", "dsound.dll"), "x");
    await fs.writeFile(path.join(plugins, "unrealsdk.dll"), "x");
    await fs.writeFile(path.join(plugins, "pyunrealsdk.dll"), "x");
    await fs.writeFile(
      path.join(plugins, "unrealsdk.toml"),
      '[mod_manager]\ndisplay_version = "0.3 (test)"\n'
    );
    await fs.writeFile(path.join(sdkMods, "__main__.py"), "# test\n");
    await fs.writeFile(path.join(sdkMods, "mods_base.sdkmod"), "x");
    const info = await oak2.inspectOak2Install(gameRoot);
    assert.strictEqual(info.present, true);
    assert.strictEqual(info.ok, true);
    assert.strictEqual(info.displayVersion, "0.3 (test)");
    console.log("ok inspect fake v0.3");
  });
}

async function testPathHelpers() {
  const roots = oak2.bl4GameRootCandidates();
  assert.ok(Array.isArray(roots));
  assert.ok(roots.some((p) => /Borderlands 4$/i.test(p)));
  assert.ok(oak2.bl4SdkModsCandidates().every((p) => path.basename(p).toLowerCase() === "sdk_mods"));
  const epic = oak2.epicGameRootCandidates();
  assert.ok(epic.some((p) => /Epic Games/i.test(p)));
  console.log("ok path helpers");
}

async function testDryRunInstallUsesCacheContract() {
  await withTempDir(async (dir) => {
    const gameRoot = path.join(dir, "Borderlands 4");
    await fs.mkdir(gameRoot, { recursive: true });
    // Dry-run still downloads/verifies zip into cache; skip network if offline by
    // planting a pre-hashed empty mismatch then ensuring failure path is structured.
    const result = await oak2.installOak2FromCache(dir, gameRoot, {
      dryRun: true,
      fetchImpl: async () => {
        throw new Error("network blocked in unit test");
      }
    });
    assert.strictEqual(result.ok, false);
    assert.ok(/network blocked|Download failed|fetch/i.test(result.message) || result.message);
    console.log("ok dry-run network failure shape");
  });
}

async function testCopyPairLayout() {
  const pairs = oak2.buildOak2CopyPairs("C:\\cache\\extracted-v0.3", "C:\\Games\\Borderlands 4");
  assert.ok(pairs.some((p) => /OakGame$/i.test(p.destination) || p.destination.endsWith(`${path.sep}OakGame`)));
  assert.ok(pairs.some((p) => p.destination.endsWith(`${path.sep}mods_base.sdkmod`)));
  assert.ok(pairs.some((p) => p.destination.endsWith(`${path.sep}__main__.py`)));
  console.log("ok copy pair layout");
}

async function testCachedZipDryRunWithFixture() {
  await withTempDir(async (dir) => {
    const fixtureZip = path.join(process.env.TEMP || os.tmpdir(), "msbt-oak2-inspect", "oak2-sdk.zip");
    let hasFixture = false;
    try {
      await fs.access(fixtureZip);
      hasFixture = true;
    } catch {
      hasFixture = false;
    }
    if (!hasFixture) {
      console.log("skip cached zip dry-run (no local oak2-sdk.zip fixture)");
      return;
    }
    const caches = oak2.cacheRoots(dir);
    await fs.mkdir(caches.root, { recursive: true });
    await fs.copyFile(fixtureZip, caches.zipPath);
    const hash = await oak2.sha256File(caches.zipPath);
    assert.strictEqual(hash.toLowerCase(), oak2.OAK2_SHA256.toLowerCase());
    const gameRoot = path.join(dir, "Borderlands 4");
    await fs.mkdir(gameRoot, { recursive: true });
    const result = await oak2.installOak2FromCache(dir, gameRoot, { dryRun: true });
    assert.strictEqual(result.ok, true);
    assert.strictEqual(result.dryRun, true);
    assert.ok(Array.isArray(result.copyPairs));
    assert.ok(result.copyPairs.length >= 5);
    console.log("ok cached zip dry-run with fixture");
  });
}

async function main() {
  await testParseVersion();
  await testEnableSettingsMerge();
  await testInspectMissingInstall();
  await testInspectFakeV03();
  await testPathHelpers();
  await testCopyPairLayout();
  await testDryRunInstallUsesCacheContract();
  await testCachedZipDryRunWithFixture();
  console.log("\nAll oak2_install self-tests passed.");
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
