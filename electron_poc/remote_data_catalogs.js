"use strict";

/**
 * MSBT-owned remote data catalogs (GitHub-hosted JSON refresh).
 *
 * Preference for each file:
 *   1) userData/msbt_data/ cache (last good)
 *   2) bundled seed (resources / docs/data)
 *   3) GZO only: live save-editor.be, then GitHub snapshot
 *
 * Offline: never wipe last-good cache; refresh failures are soft.
 */

const crypto = require("crypto");
const fs = require("fs/promises");
const path = require("path");
const { fileURLToPath } = require("url");

const DEFAULT_MANIFEST_URLS = [
  "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/download/catalog_manifest.json",
  "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/docs/data/catalog_manifest.json"
];

const CACHE_DIR_NAME = "msbt_data";
const CACHED_MANIFEST_NAME = "catalog_manifest.json";

const KNOWN_FILES = {
  lootlemon: "MattsSDKBoostingTools_lootlemon_codes.json",
  custom_bl4_codes: "custom_bl4_codes.json",
  gzo_codes: "MattsSDKBoostingTools_gzo_codes.json",
  travelstations: "travelstations.json",
  travelmaps: "travelmaps_flat.json",
  item_pools: "item_pools.json",
  gzo_parts_map: "gzo_parts_map.json",
  shiny_serials: "shiny_serials.json",
  challenge_catalog: "challenge_catalog.json"
};

const ELECTRON_RESOURCE_FILES = new Set([
  KNOWN_FILES.lootlemon,
  KNOWN_FILES.custom_bl4_codes,
  KNOWN_FILES.gzo_codes,
  KNOWN_FILES.travelstations,
  KNOWN_FILES.travelmaps,
  KNOWN_FILES.item_pools,
  KNOWN_FILES.gzo_parts_map
]);

function text(value) {
  return String(value ?? "").trim();
}

function dataCacheDir(userDataPath) {
  return path.join(userDataPath, CACHE_DIR_NAME);
}

function cachedManifestPath(userDataPath) {
  return path.join(dataCacheDir(userDataPath), CACHED_MANIFEST_NAME);
}

function cachedFilePath(userDataPath, fileName) {
  return path.join(dataCacheDir(userDataPath), path.basename(fileName));
}

function sha256Buffer(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

async function sha256File(filePath) {
  const buffer = await fs.readFile(filePath);
  return sha256Buffer(buffer);
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJsonFile(filePath) {
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw);
}

async function writeFileAtomic(filePath, bufferOrString) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const tmp = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(tmp, bufferOrString);
  await fs.rename(tmp, filePath);
}

function defaultDocsDataDir(sourceRoot) {
  return path.join(sourceRoot, "docs", "data");
}

function bundledCandidates(fileName, resourceDir, docsDataDir, modDataDir) {
  const name = path.basename(fileName);
  const out = [];
  if (resourceDir) out.push(path.join(resourceDir, name));
  if (docsDataDir) out.push(path.join(docsDataDir, name));
  if (modDataDir) out.push(path.join(modDataDir, name));
  return out;
}

/**
 * Resolve best local path for a catalog file without network I/O.
 * Prefer user cache → first existing bundled seed.
 */
async function resolveLocalCatalogPath(userDataPath, fileName, options = {}) {
  const name = path.basename(fileName);
  const cachePath = cachedFilePath(userDataPath, name);
  if (await fileExists(cachePath)) {
    return { path: cachePath, source: "cache" };
  }
  for (const candidate of bundledCandidates(
    name,
    options.resourceDir,
    options.docsDataDir,
    options.modDataDir
  )) {
    if (await fileExists(candidate)) {
      return { path: candidate, source: "bundled" };
    }
  }
  return { path: null, source: "missing" };
}

/**
 * Build path map used by BL4 catalog + resource JSON loaders.
 */
async function resolveCatalogFileMap(userDataPath, options = {}) {
  const map = {};
  const sources = {};
  for (const [id, fileName] of Object.entries(KNOWN_FILES)) {
    const resolved = await resolveLocalCatalogPath(userDataPath, fileName, options);
    map[id] = resolved.path;
    sources[id] = resolved.source;
  }
  // GZO live cache (from Refresh GZO) still wins over GitHub snapshot when present.
  if (options.gzoLiveCachePath && (await fileExists(options.gzoLiveCachePath))) {
    map.gzo_codes = options.gzoLiveCachePath;
    sources.gzo_codes = "gzo_live_cache";
  }
  return { paths: map, sources };
}

function normalizeManifest(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Catalog manifest is not an object.");
  }
  const files = Array.isArray(payload.files) ? payload.files : [];
  if (!files.length) throw new Error("Catalog manifest has no files.");
  return {
    schema_version: Number(payload.schema_version) || 1,
    data_version: text(payload.data_version) || "0.0.0",
    data_version_label: text(payload.data_version_label) || `data-v${text(payload.data_version) || "0.0.0"}`,
    published_at: text(payload.published_at),
    min_app_version: text(payload.min_app_version),
    files: files.map((entry) => ({
      id: text(entry.id),
      path: path.basename(text(entry.path)),
      url: text(entry.url),
      sha256: text(entry.sha256).toLowerCase(),
      bytes: Number(entry.bytes) || 0,
      schema_version: Number(entry.schema_version) || 1,
      primary_url: text(entry.primary_url),
      notes: text(entry.notes)
    })).filter((entry) => entry.id && entry.path && entry.url && entry.sha256)
  };
}

async function fetchText(url, fetchImpl, headers = {}) {
  if (String(url).startsWith("file:")) {
    const body = await fs.readFile(fileURLToPath(url), "utf8");
    return { body, url, status: 200 };
  }
  const response = await fetchImpl(url, {
    headers: {
      "User-Agent": "MattsBoostingToolsElectron/1.0",
      Accept: "application/json,text/plain,*/*",
      ...headers
    },
    cache: "no-store"
  });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} from ${url}`);
  }
  return { body, url, status: response.status };
}

async function fetchBuffer(url, fetchImpl) {
  if (String(url).startsWith("file:")) {
    return fs.readFile(fileURLToPath(url));
  }
  const response = await fetchImpl(url, {
    headers: {
      "User-Agent": "MattsBoostingToolsElectron/1.0",
      Accept: "application/octet-stream,application/json,*/*"
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} from ${url}`);
  }
  const arrayBuffer = await response.arrayBuffer();
  return Buffer.from(arrayBuffer);
}

async function fetchRemoteManifest(fetchImpl, manifestUrls = DEFAULT_MANIFEST_URLS) {
  const urls = (manifestUrls || []).map(text).filter(Boolean);
  let lastError = null;
  for (const url of urls) {
    try {
      const { body } = await fetchText(url, fetchImpl);
      const manifest = normalizeManifest(JSON.parse(body));
      return { manifest, url };
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error("Catalog manifest could not be loaded.");
}

async function loadCachedManifest(userDataPath) {
  const filePath = cachedManifestPath(userDataPath);
  if (!(await fileExists(filePath))) return null;
  try {
    return normalizeManifest(await readJsonFile(filePath));
  } catch {
    return null;
  }
}

async function loadBundledManifest(docsDataDir) {
  if (!docsDataDir) return null;
  const filePath = path.join(docsDataDir, CACHED_MANIFEST_NAME);
  if (!(await fileExists(filePath))) return null;
  try {
    return normalizeManifest(await readJsonFile(filePath));
  } catch {
    return null;
  }
}

async function cacheNeedsUpdate(userDataPath, entry) {
  const target = cachedFilePath(userDataPath, entry.path);
  if (!(await fileExists(target))) return true;
  try {
    const digest = await sha256File(target);
    return digest.toLowerCase() !== entry.sha256;
  } catch {
    return true;
  }
}

/**
 * Soft refresh: download changed files by sha256 into userData/msbt_data/.
 * Never deletes existing good cache on failure.
 */
async function refreshRemoteDataCatalogs(options = {}) {
  const userDataPath = options.userDataPath;
  if (!userDataPath) throw new Error("userDataPath is required.");
  const fetchImpl = options.fetch || globalThis.fetch;
  if (typeof fetchImpl !== "function") {
    throw new Error("No fetch implementation available.");
  }

  const cacheDir = dataCacheDir(userDataPath);
  await fs.mkdir(cacheDir, { recursive: true });

  const warnings = [];
  const updated = [];
  const skipped = [];
  const failed = [];

  let manifest;
  let manifestUrl = "";
  try {
    const remote = await fetchRemoteManifest(fetchImpl, options.manifestUrls || DEFAULT_MANIFEST_URLS);
    manifest = remote.manifest;
    manifestUrl = remote.url;
  } catch (error) {
    const cached = await loadCachedManifest(userDataPath);
    const bundled = cached ? null : await loadBundledManifest(options.docsDataDir);
    manifest = cached || bundled;
    if (!manifest) {
      return {
        ok: false,
        offline: true,
        message: `Catalog refresh failed and no local manifest is available: ${error && error.message ? error.message : error}`,
        warnings,
        updated,
        skipped,
        failed,
        cacheDir
      };
    }
    warnings.push(
      `Remote manifest unreachable (${error && error.message ? error.message : error}). Using ${cached ? "cached" : "bundled"} manifest.`
    );
    return {
      ok: true,
      offline: true,
      soft: true,
      message: warnings[0],
      manifest,
      manifestUrl: cached ? "cache" : "bundled",
      dataVersion: manifest.data_version_label,
      warnings,
      updated,
      skipped: manifest.files.map((f) => f.id),
      failed,
      cacheDir
    };
  }

  // Persist manifest only after a successful remote fetch.
  try {
    await writeFileAtomic(
      cachedManifestPath(userDataPath),
      `${JSON.stringify(manifest, null, 2)}\n`
    );
  } catch (error) {
    warnings.push(`Could not cache manifest: ${error && error.message ? error.message : error}`);
  }

  for (const entry of manifest.files) {
    try {
      const needs = await cacheNeedsUpdate(userDataPath, entry);
      if (!needs) {
        skipped.push(entry.id);
        continue;
      }
      let buffer;
      const localSeed = options.localSeedDir
        ? path.join(options.localSeedDir, entry.path)
        : "";
      if (localSeed && (await fileExists(localSeed))) {
        buffer = await fs.readFile(localSeed);
      } else {
        buffer = await fetchBuffer(entry.url, fetchImpl);
      }
      const digest = sha256Buffer(buffer).toLowerCase();
      if (digest !== entry.sha256) {
        throw new Error(
          `sha256 mismatch for ${entry.id}: expected ${entry.sha256.slice(0, 12)}… got ${digest.slice(0, 12)}…`
        );
      }
      if (entry.bytes > 0 && buffer.length !== entry.bytes) {
        warnings.push(
          `${entry.id}: byte size ${buffer.length} != manifest ${entry.bytes} (sha256 matched; keeping file).`
        );
      }
      await writeFileAtomic(cachedFilePath(userDataPath, entry.path), buffer);
      updated.push(entry.id);
    } catch (error) {
      failed.push({ id: entry.id, message: String(error && error.message ? error.message : error) });
      // Keep prior cache file untouched.
    }
  }

  const ok = failed.length === 0 || updated.length > 0 || skipped.length > 0;
  const parts = [];
  if (updated.length) parts.push(`updated ${updated.length}`);
  if (skipped.length) parts.push(`unchanged ${skipped.length}`);
  if (failed.length) parts.push(`failed ${failed.length}`);
  return {
    ok,
    offline: false,
    soft: failed.length > 0,
    message: `Data catalogs ${manifest.data_version_label}: ${parts.join(", ") || "no files"}.`,
    manifest,
    manifestUrl,
    dataVersion: manifest.data_version_label,
    publishedAt: manifest.published_at,
    warnings,
    updated,
    skipped,
    failed,
    cacheDir
  };
}

async function getDataCatalogStatus(userDataPath, options = {}) {
  const cacheDir = dataCacheDir(userDataPath);
  const cachedManifest = await loadCachedManifest(userDataPath);
  const bundledManifest = await loadBundledManifest(options.docsDataDir);
  const fileMap = await resolveCatalogFileMap(userDataPath, options);
  const cacheFiles = {};
  for (const [id, fileName] of Object.entries(KNOWN_FILES)) {
    const filePath = cachedFilePath(userDataPath, fileName);
    const exists = await fileExists(filePath);
    let sha256 = "";
    let bytes = 0;
    if (exists) {
      try {
        const st = await fs.stat(filePath);
        bytes = st.size;
        sha256 = await sha256File(filePath);
      } catch {
        // ignore
      }
    }
    cacheFiles[id] = {
      fileName,
      cached: exists,
      path: exists ? filePath : null,
      bytes,
      sha256,
      resolvedSource: fileMap.sources[id] || "missing",
      resolvedPath: fileMap.paths[id] || null
    };
  }
  return {
    ok: true,
    cacheDir,
    cachedManifest: cachedManifest
      ? {
          data_version: cachedManifest.data_version,
          data_version_label: cachedManifest.data_version_label,
          published_at: cachedManifest.published_at,
          file_count: cachedManifest.files.length
        }
      : null,
    bundledManifest: bundledManifest
      ? {
          data_version: bundledManifest.data_version,
          data_version_label: bundledManifest.data_version_label,
          published_at: bundledManifest.published_at,
          file_count: bundledManifest.files.length
        }
      : null,
    files: cacheFiles
  };
}

/**
 * Read JSON preferring cache → bundled seeds. Soft-fail to null.
 */
async function readCatalogJson(userDataPath, fileName, options = {}) {
  const resolved = await resolveLocalCatalogPath(userDataPath, fileName, options);
  if (!resolved.path) {
    return { ok: false, message: `${path.basename(fileName)} not found in cache or bundled seeds.`, source: "missing" };
  }
  try {
    const data = await readJsonFile(resolved.path);
    return { ok: true, data, source: resolved.source, path: resolved.path, name: path.basename(fileName) };
  } catch (error) {
    return {
      ok: false,
      message: String(error && error.message ? error.message : error),
      source: resolved.source,
      path: resolved.path
    };
  }
}

function isElectronResourceFile(name) {
  return ELECTRON_RESOURCE_FILES.has(path.basename(String(name || "")));
}

module.exports = {
  CACHE_DIR_NAME,
  DEFAULT_MANIFEST_URLS,
  KNOWN_FILES,
  cachedFilePath,
  cachedManifestPath,
  dataCacheDir,
  defaultDocsDataDir,
  getDataCatalogStatus,
  isElectronResourceFile,
  normalizeManifest,
  readCatalogJson,
  refreshRemoteDataCatalogs,
  resolveCatalogFileMap,
  resolveLocalCatalogPath,
  sha256Buffer,
  sha256File
};
