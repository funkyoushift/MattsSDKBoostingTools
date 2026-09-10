"use strict";

const assert = require("assert");
const fs = require("fs/promises");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");
const {
  cachedFilePath, cachedManifestPath, normalizeManifest,
  refreshRemoteDataCatalogs, resolveLocalCatalogPath, sha256Buffer
} = require("./remote_data_catalogs");

async function main() {
  const userData = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-game-build-"));
  try {
    const bundle = path.join(userData, "bundle");
    const payloads = path.join(userData, "payloads");
    await fs.mkdir(bundle, { recursive: true });
    await fs.mkdir(payloads);
    let sequence = 0;
    async function entry(id, name, value, gameBuild) {
      const bytes = Buffer.from(JSON.stringify({ value }));
      const payload = path.join(payloads, `${++sequence}.json`);
      await fs.writeFile(payload, bytes);
      return { id, path: name, kind: "catalog_json", url: pathToFileURL(payload).href,
        sha256: sha256Buffer(bytes), bytes: bytes.length, ...(gameBuild ? { game_build: gameBuild } : {}) };
    }
    const gameName = "gzo_parts_map.json";
    const freeName = "MattsSDKBoostingTools_lootlemon_codes.json";
    const seed = await entry("gzo_parts_map", gameName, "current bundled game", "25234898");
    const old = await entry("gzo_parts_map", gameName, "old cached game", "25234897");
    const free = await entry("lootlemon", freeName, "old community catalog");
    const manifest = files => ({ schema_version: 1, data_version: "1.0.3", files });
    await fs.writeFile(path.join(bundle, "catalog_manifest.json"), JSON.stringify(manifest([seed, free])));
    await fs.copyFile(new URL(seed.url), path.join(bundle, gameName));
    await fs.copyFile(new URL(free.url), path.join(bundle, freeName));
    await fs.mkdir(path.dirname(cachedFilePath(userData, gameName)), { recursive: true });
    await fs.copyFile(new URL(old.url), cachedFilePath(userData, gameName));
    await fs.writeFile(cachedManifestPath(userData), JSON.stringify(manifest([old])));
    const resolve = () => resolveLocalCatalogPath(userData, gameName, { docsDataDir: bundle });
    assert.strictEqual((await resolve()).source, "bundled", "old cache must not hide fresh seed");
    assert.strictEqual(normalizeManifest(manifest([seed])).files[0].game_build, "25234898");

    const remotePath = path.join(userData, "remote-manifest.json");
    async function refresh(entries) {
      await fs.writeFile(remotePath, JSON.stringify(manifest(entries)));
      return refreshRemoteDataCatalogs({
        userDataPath: userData, docsDataDir: bundle, localSeedDir: bundle, electronAppDir: bundle, retries: 1,
        manifestUrls: [pathToFileURL(remotePath).href], fetch: globalThis.fetch
      });
    }
    let result = await refresh([old, free]);
    assert(result.skipped.includes("gzo_parts_map"));
    assert(result.updated.includes("lootlemon"), "untagged community assets must remain refreshable");
    assert.strictEqual((await resolve()).source, "bundled");
    const missingBuild = { ...old };
    delete missingBuild.game_build;
    result = await refresh([missingBuild]);
    assert(result.skipped.includes("gzo_parts_map"));
    assert.strictEqual((await resolve()).source, "bundled");

    const newer = await entry("gzo_parts_map", gameName, "next game data", "25234899");
    result = await refresh([newer]);
    assert(result.updated.includes("gzo_parts_map"));
    assert.strictEqual((await resolve()).source, "cache", "verified newer cache must win");
    const newerBytes = await fs.readFile(cachedFilePath(userData, gameName), "utf8");
    result = await refresh([seed]);
    assert(result.skipped.includes("gzo_parts_map"), "older remote must not replace newer cache");
    assert.strictEqual(await fs.readFile(cachedFilePath(userData, gameName), "utf8"), newerBytes);

    const broken = await entry("gzo_parts_map", gameName, "bad future data", "25234900");
    broken.sha256 = "a".repeat(64);
    const updatedFree = await entry("lootlemon", freeName, "new community catalog");
    result = await refresh([broken, updatedFree]);
    assert(result.failed.some(row => row.id === "gzo_parts_map"));
    assert(result.updated.includes("lootlemon"));
    const cachedManifest = JSON.parse(await fs.readFile(cachedManifestPath(userData), "utf8"));
    assert.strictEqual(cachedManifest.files.find(row => row.id === "gzo_parts_map").game_build, "25234899",
      "partial failure must preserve metadata for the actual retained bytes");
    assert.strictEqual((await resolve()).source, "cache");
    await fs.writeFile(cachedFilePath(userData, gameName), "corrupt");
    assert.strictEqual((await resolve()).source, "bundled", "cache build metadata alone cannot verify content");
    await refresh([newer]);
    assert.strictEqual((await resolve()).source, "cache", "same-build download can repair corrupted bytes");
    console.log("catalog game-build tests passed: stale/missing, newer, partial failure, hash check, repair");
  } finally {
    await fs.rm(userData, { recursive: true, force: true });
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
