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
  // Prefer tag-specific data release assets (never /releases/latest — that is the app channel).
  "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/data-v1.0.2/catalog_manifest.json",
  "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/docs/data/catalog_manifest.json",
  // Older data tag fallbacks while newer tags propagate.
  "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/data-v1.0.1/catalog_manifest.json",
  "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/data-v1.0.0/catalog_manifest.json"
];

const CACHE_DIR_NAME = "msbt_data";
const CACHED_MANIFEST_NAME = "catalog_manifest.json";
const REFRESH_STATE_NAME = "refresh_state.json";
const TUTORIAL_COPY_NAME = "tutorial_copy.json";
const DEFAULT_FETCH_RETRIES = 3;
const RETRY_BASE_DELAY_MS = 400;

const ALLOWED_ASSET_KINDS = new Set(["catalog_json", "json_copy", "markdown_doc"]);
const REJECTED_ASSET_EXTENSIONS = new Set([
  ".js",
  ".mjs",
  ".cjs",
  ".py",
  ".exe",
  ".dll",
  ".so",
  ".dylib",
  ".sdkmod",
  ".bat",
  ".cmd",
  ".ps1",
  ".sh"
]);

const KNOWN_FILES = {
  lootlemon: "MattsSDKBoostingTools_lootlemon_codes.json",
  custom_bl4_codes: "custom_bl4_codes.json",
  gzo_codes: "MattsSDKBoostingTools_gzo_codes.json",
  travelstations: "travelstations.json",
  travelmaps: "travelmaps_flat.json",
  item_pools: "item_pools.json",
  gzo_parts_map: "gzo_parts_map.json",
  shiny_serials: "shiny_serials.json",
  challenge_catalog: "challenge_catalog.json",
  dev_spawner_catalog: "dev_spawner_catalog.json"
};

/** Files Electron UI loaders may resolve via readResourceJson / catalog helpers. */
const ELECTRON_RESOURCE_FILES = new Set([
  KNOWN_FILES.lootlemon,
  KNOWN_FILES.custom_bl4_codes,
  KNOWN_FILES.gzo_codes,
  KNOWN_FILES.travelstations,
  KNOWN_FILES.travelmaps,
  KNOWN_FILES.item_pools,
  KNOWN_FILES.gzo_parts_map,
  KNOWN_FILES.shiny_serials,
  KNOWN_FILES.challenge_catalog,
  KNOWN_FILES.dev_spawner_catalog
]);

function text(value) {
  return String(value ?? "").trim();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function dataCacheDir(userDataPath) {
  return path.join(userDataPath, CACHE_DIR_NAME);
}

function cachedManifestPath(userDataPath) {
  return path.join(dataCacheDir(userDataPath), CACHED_MANIFEST_NAME);
}

function refreshStatePath(userDataPath) {
  return path.join(dataCacheDir(userDataPath), REFRESH_STATE_NAME);
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

function bundledCandidates(fileName, resourceDir, docsDataDir, modDataDir, electronAppDir) {
  const name = path.basename(fileName);
  const out = [];
  if (resourceDir) out.push(path.join(resourceDir, name));
  if (docsDataDir) out.push(path.join(docsDataDir, name));
  if (modDataDir) out.push(path.join(modDataDir, name));
  // Dev Spawner catalog ships next to main.js in electron_poc/.
  if (electronAppDir) out.push(path.join(electronAppDir, name));
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
    options.modDataDir,
    options.electronAppDir
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

function normalizeManifestEntry(entry, { requireKind = false } = {}) {
  const pathName = path.basename(text(entry && entry.path));
  const kind = text(entry && entry.kind) || (requireKind ? "" : "catalog_json");
  const ext = path.extname(pathName).toLowerCase();
  if (!pathName || !text(entry && entry.url) || !text(entry && entry.sha256)) return null;
  if (REJECTED_ASSET_EXTENSIONS.has(ext)) return null;
  if (kind && !ALLOWED_ASSET_KINDS.has(kind)) return null;
  return {
    id: text(entry.id) || pathName.replace(/\.[^.]+$/, ""),
    path: pathName,
    url: text(entry.url),
    raw_url: text(entry.raw_url),
    sha256: text(entry.sha256).toLowerCase(),
    bytes: Number(entry.bytes) || 0,
    schema_version: Number(entry.schema_version) || 1,
    primary_url: text(entry.primary_url),
    notes: text(entry.notes),
    kind: kind || "catalog_json",
    min_app_version: text(entry.min_app_version)
  };
}

function normalizeManifest(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Catalog manifest is not an object.");
  }
  const files = Array.isArray(payload.files) ? payload.files : [];
  if (!files.length) throw new Error("Catalog manifest has no files.");
  const normalizedFiles = files
    .map((entry) => normalizeManifestEntry(entry))
    .filter(Boolean);
  if (!normalizedFiles.length) throw new Error("Catalog manifest has no usable files.");

  const rawAssets = [
    ...(Array.isArray(payload.assets) ? payload.assets : []),
    ...(Array.isArray(payload.packs) ? payload.packs : [])
  ];
  const assets = rawAssets
    .map((entry) => normalizeManifestEntry(entry, { requireKind: true }))
    .filter(Boolean);

  // Combined download list: catalogs + allowlisted hotfix assets (dedupe by path).
  const downloadables = normalizedFiles.slice();
  for (const asset of assets) {
    if (!downloadables.some((row) => row.path === asset.path)) {
      downloadables.push(asset);
    }
  }

  return {
    schema_version: Number(payload.schema_version) || 1,
    data_version: text(payload.data_version) || "0.0.0",
    data_version_label: text(payload.data_version_label) || `data-v${text(payload.data_version) || "0.0.0"}`,
    published_at: text(payload.published_at),
    min_app_version: text(payload.min_app_version),
    files: normalizedFiles,
    assets,
    downloadables
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

async function withRetries(label, attempts, fn) {
  let lastError = null;
  const max = Math.max(1, Number(attempts) || 1);
  for (let i = 0; i < max; i += 1) {
    try {
      return await fn(i);
    } catch (error) {
      lastError = error;
      if (i < max - 1) {
        await sleep(RETRY_BASE_DELAY_MS * (i + 1));
      }
    }
  }
  throw lastError || new Error(`${label} failed after ${max} attempt(s)`);
}

async function fetchRemoteManifest(fetchImpl, manifestUrls = DEFAULT_MANIFEST_URLS, retries = DEFAULT_FETCH_RETRIES) {
  const urls = (manifestUrls || []).map(text).filter(Boolean);
  let lastError = null;
  for (const url of urls) {
    try {
      const { body } = await withRetries(`manifest ${url}`, retries, () => fetchText(url, fetchImpl));
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

async function loadRefreshState(userDataPath) {
  const filePath = refreshStatePath(userDataPath);
  if (!(await fileExists(filePath))) return null;
  try {
    const payload = await readJsonFile(filePath);
    if (!payload || typeof payload !== "object") return null;
    return payload;
  } catch {
    return null;
  }
}

async function writeRefreshState(userDataPath, state) {
  await writeFileAtomic(refreshStatePath(userDataPath), `${JSON.stringify(state, null, 2)}\n`);
}

function summarizeRefreshResult(result) {
  return {
    ok: Boolean(result && result.ok),
    soft: Boolean(result && result.soft),
    offline: Boolean(result && result.offline),
    quiet: Boolean(result && result.quiet),
    message: text(result && result.message),
    dataVersion: text(result && result.dataVersion),
    publishedAt: text(result && result.publishedAt),
    manifestUrl: text(result && result.manifestUrl),
    updatedCount: Array.isArray(result && result.updated) ? result.updated.length : 0,
    skippedCount: Array.isArray(result && result.skipped) ? result.skipped.length : 0,
    failedCount: Array.isArray(result && result.failed) ? result.failed.length : 0,
    updated: Array.isArray(result && result.updated) ? result.updated.slice() : [],
    skipped: Array.isArray(result && result.skipped) ? result.skipped.slice() : [],
    failed: Array.isArray(result && result.failed) ? result.failed.slice() : [],
    warnings: Array.isArray(result && result.warnings) ? result.warnings.slice() : [],
    checkedAt: text(result && result.checkedAt) || new Date().toISOString(),
    cacheDir: text(result && result.cacheDir)
  };
}

function formatDataCatalogStatusLine(summary) {
  if (!summary) return "Data catalogs not checked yet.";
  const version = summary.dataVersion || "unknown";
  const when = summary.checkedAt ? ` · last check ${summary.checkedAt}` : "";
  const counts = ` · updated ${summary.updatedCount || 0}, unchanged ${summary.skippedCount || 0}, failed ${summary.failedCount || 0}`;
  const mode = summary.offline ? " (offline/cached)" : summary.quiet ? " (startup)" : "";
  const base = summary.message || `${version}${counts}`;
  if (summary.message && summary.message.includes(version)) {
    return `${summary.message}${mode}${when}`;
  }
  return `${version}${counts}${mode}${when}${summary.message ? ` — ${summary.message}` : ""}`;
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

async function downloadCatalogEntry(entry, options, attemptHint = 0) {
  const fetchImpl = options.fetch || globalThis.fetch;
  const retries = Number.isFinite(options.retries) ? options.retries : DEFAULT_FETCH_RETRIES;
  const localSeed = options.localSeedDir ? path.join(options.localSeedDir, entry.path) : "";
  const electronSeed = options.electronAppDir ? path.join(options.electronAppDir, entry.path) : "";

  return withRetries(`file ${entry.id}`, retries, async (attempt) => {
    if (typeof options.onProgress === "function") {
      options.onProgress({
        phase: "download",
        id: entry.id,
        path: entry.path,
        bytes: entry.bytes,
        attempt: attempt + 1,
        attemptHint: attemptHint + attempt + 1
      });
    }
    let buffer;
    if (localSeed && (await fileExists(localSeed))) {
      buffer = await fs.readFile(localSeed);
    } else if (electronSeed && (await fileExists(electronSeed))) {
      buffer = await fs.readFile(electronSeed);
    } else {
      try {
        buffer = await fetchBuffer(entry.url, fetchImpl);
      } catch (primaryError) {
        if (entry.raw_url && entry.raw_url !== entry.url) {
          buffer = await fetchBuffer(entry.raw_url, fetchImpl);
        } else {
          throw primaryError;
        }
      }
    }
    const digest = sha256Buffer(buffer).toLowerCase();
    if (digest !== entry.sha256) {
      throw new Error(
        `sha256 mismatch for ${entry.id}: expected ${entry.sha256.slice(0, 12)}… got ${digest.slice(0, 12)}…`
      );
    }
    return buffer;
  });
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
  const checkedAt = new Date().toISOString();
  const retries = Number.isFinite(options.retries) ? options.retries : DEFAULT_FETCH_RETRIES;

  const warnings = [];
  const updated = [];
  const skipped = [];
  const failed = [];

  let manifest;
  let manifestUrl = "";
  try {
    if (typeof options.onProgress === "function") {
      options.onProgress({ phase: "manifest", message: "Fetching catalog manifest..." });
    }
    const remote = await fetchRemoteManifest(
      fetchImpl,
      options.manifestUrls || DEFAULT_MANIFEST_URLS,
      retries
    );
    manifest = remote.manifest;
    manifestUrl = remote.url;
  } catch (error) {
    const cached = await loadCachedManifest(userDataPath);
    const bundled = cached ? null : await loadBundledManifest(options.docsDataDir);
    manifest = cached || bundled;
    if (!manifest) {
      const result = {
        ok: false,
        offline: true,
        quiet: Boolean(options.quiet),
        message: `Catalog refresh failed and no local manifest is available: ${error && error.message ? error.message : error}`,
        warnings,
        updated,
        skipped,
        failed,
        cacheDir,
        checkedAt
      };
      try {
        await writeRefreshState(userDataPath, summarizeRefreshResult(result));
      } catch {
        // ignore
      }
      return result;
    }
    warnings.push(
      `Remote manifest unreachable (${error && error.message ? error.message : error}). Using ${cached ? "cached" : "bundled"} manifest.`
    );
    const result = {
      ok: true,
      offline: true,
      soft: true,
      quiet: Boolean(options.quiet),
      message: warnings[0],
      manifest,
      manifestUrl: cached ? "cache" : "bundled",
      dataVersion: manifest.data_version_label,
      publishedAt: manifest.published_at,
      warnings,
      updated,
      skipped: manifest.files.map((f) => f.id),
      failed,
      cacheDir,
      checkedAt
    };
    try {
      await writeRefreshState(userDataPath, summarizeRefreshResult(result));
    } catch {
      // ignore
    }
    return result;
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

  const total = (manifest.downloadables || manifest.files).length;
  let index = 0;
  for (const entry of manifest.downloadables || manifest.files) {
    index += 1;
    try {
      if (typeof options.onProgress === "function") {
        options.onProgress({
          phase: "file",
          id: entry.id,
          path: entry.path,
          kind: entry.kind || "catalog_json",
          index,
          total,
          bytes: entry.bytes,
          message: `Checking ${entry.id} (${index}/${total})...`
        });
      }
      const needs = await cacheNeedsUpdate(userDataPath, entry);
      if (!needs) {
        skipped.push(entry.id);
        continue;
      }
      const buffer = await downloadCatalogEntry(entry, { ...options, fetch: fetchImpl, retries });
      if (entry.bytes > 0 && buffer.length !== entry.bytes) {
        warnings.push(
          `${entry.id}: byte size ${buffer.length} != manifest ${entry.bytes} (sha256 matched; keeping file).`
        );
      }
      await writeFileAtomic(cachedFilePath(userDataPath, entry.path), buffer);
      updated.push(entry.id);
      if (typeof options.onProgress === "function") {
        options.onProgress({
          phase: "saved",
          id: entry.id,
          path: entry.path,
          kind: entry.kind || "catalog_json",
          index,
          total,
          bytes: buffer.length,
          message: `Updated ${entry.id}`
        });
      }
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
  const result = {
    ok,
    offline: false,
    soft: failed.length > 0,
    quiet: Boolean(options.quiet),
    message: `Data catalogs ${manifest.data_version_label}: ${parts.join(", ") || "no files"}.`,
    manifest,
    manifestUrl,
    dataVersion: manifest.data_version_label,
    publishedAt: manifest.published_at,
    warnings,
    updated,
    skipped,
    failed,
    cacheDir,
    checkedAt
  };
  try {
    await writeRefreshState(userDataPath, summarizeRefreshResult(result));
  } catch (error) {
    warnings.push(`Could not write refresh state: ${error && error.message ? error.message : error}`);
    result.warnings = warnings;
  }
  return result;
}

async function getDataCatalogStatus(userDataPath, options = {}) {
  const cacheDir = dataCacheDir(userDataPath);
  const cachedManifest = await loadCachedManifest(userDataPath);
  const bundledManifest = await loadBundledManifest(options.docsDataDir);
  const refreshState = await loadRefreshState(userDataPath);
  const fileMap = await resolveCatalogFileMap(userDataPath, options);
  const cacheFiles = {};
  let cachedCount = 0;
  for (const [id, fileName] of Object.entries(KNOWN_FILES)) {
    const filePath = cachedFilePath(userDataPath, fileName);
    const exists = await fileExists(filePath);
    let sha256 = "";
    let bytes = 0;
    if (exists) {
      cachedCount += 1;
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

  const activeManifest = cachedManifest || bundledManifest;
  const summary = refreshState || {
    dataVersion: activeManifest ? activeManifest.data_version_label : "",
    publishedAt: activeManifest ? activeManifest.published_at : "",
    updatedCount: 0,
    skippedCount: 0,
    failedCount: 0,
    checkedAt: "",
    message: activeManifest
      ? `Local ${activeManifest.data_version_label} available (${cachedCount} cached file(s)).`
      : "No data catalog manifest found yet."
  };

  return {
    ok: true,
    cacheDir,
    cachedCount,
    knownFileCount: Object.keys(KNOWN_FILES).length,
    lastRefresh: refreshState,
    statusLine: formatDataCatalogStatusLine(summary),
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

/**
 * Read allowlisted tutorial copy JSON (cache → docs/data seed). Soft-fail.
 * Only title/body overlays are consumed by the renderer — never executable fields.
 */
async function loadTutorialCopy(userDataPath, options = {}) {
  const resolved = await resolveLocalCatalogPath(userDataPath, TUTORIAL_COPY_NAME, {
    docsDataDir: options.docsDataDir,
    resourceDir: options.resourceDir,
    electronAppDir: options.electronAppDir
  });
  if (!resolved.path) {
    return { ok: false, source: "missing", message: "tutorial_copy.json not found." };
  }
  try {
    const data = await readJsonFile(resolved.path);
    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return { ok: false, source: resolved.source, message: "tutorial_copy.json is not an object." };
    }
    const kind = text(data.kind) || "json_copy";
    if (kind !== "json_copy") {
      return { ok: false, source: resolved.source, message: `Unsupported tutorial copy kind: ${kind}` };
    }
    return {
      ok: true,
      source: resolved.source,
      path: resolved.path,
      data: {
        schema_version: Number(data.schema_version) || 1,
        kind,
        min_app_version: text(data.min_app_version),
        notes: text(data.notes),
        tours: data.tours && typeof data.tours === "object" ? data.tours : {}
      }
    };
  } catch (error) {
    return {
      ok: false,
      source: resolved.source,
      path: resolved.path,
      message: String(error && error.message ? error.message : error)
    };
  }
}

/**
 * Apply allowlisted title/body overlays onto a local tutorial tour map (mutates in place).
 */
function applyTutorialCopyOverlay(tourMap, copyPayload) {
  if (!tourMap || typeof tourMap !== "object") return { applied: 0 };
  const tours = copyPayload && copyPayload.tours;
  if (!tours || typeof tours !== "object") return { applied: 0 };
  let applied = 0;
  for (const [tourId, patches] of Object.entries(tours)) {
    const steps = tourMap[tourId];
    if (!Array.isArray(steps) || !Array.isArray(patches)) continue;
    for (const patch of patches) {
      if (!patch || typeof patch !== "object") continue;
      const idx = Number(patch.index);
      if (!Number.isInteger(idx) || idx < 0 || !steps[idx]) continue;
      if (typeof patch.title === "string" && patch.title.trim()) {
        steps[idx].title = patch.title;
        applied += 1;
      }
      if (typeof patch.body === "string" && patch.body.trim()) {
        steps[idx].body = patch.body;
        applied += 1;
      }
    }
  }
  return { applied };
}

function isElectronResourceFile(name) {
  return ELECTRON_RESOURCE_FILES.has(path.basename(String(name || "")));
}

module.exports = {
  ALLOWED_ASSET_KINDS,
  CACHE_DIR_NAME,
  DEFAULT_FETCH_RETRIES,
  DEFAULT_MANIFEST_URLS,
  KNOWN_FILES,
  REFRESH_STATE_NAME,
  REJECTED_ASSET_EXTENSIONS,
  TUTORIAL_COPY_NAME,
  applyTutorialCopyOverlay,
  cachedFilePath,
  cachedManifestPath,
  dataCacheDir,
  defaultDocsDataDir,
  formatDataCatalogStatusLine,
  getDataCatalogStatus,
  isElectronResourceFile,
  loadRefreshState,
  loadTutorialCopy,
  normalizeManifest,
  readCatalogJson,
  refreshRemoteDataCatalogs,
  refreshStatePath,
  resolveCatalogFileMap,
  resolveLocalCatalogPath,
  sha256Buffer,
  sha256File,
  summarizeRefreshResult,
  writeRefreshState
};
