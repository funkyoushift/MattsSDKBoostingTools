const fs = require("fs/promises");
const path = require("path");

const FAVORITES_VERSION = 1;
const FAVORITES_FILENAME = "dev_spawner_favorites.json";
const ACTOR_KEY_RE = /^[A-Za-z0-9_]+$/;

function favoritesFilePath(userDataPath) {
  return path.join(userDataPath, FAVORITES_FILENAME);
}

function emptyFavorites() {
  return { version: FAVORITES_VERSION, favorites: {} };
}

function normalizeActorKey(value) {
  const actorKey = String(value || "").trim();
  if (!actorKey || actorKey.length > 160 || !ACTOR_KEY_RE.test(actorKey)) {
    return "";
  }
  return actorKey;
}

function normalizeFavoriteLabel(value, fallback = "") {
  const label = String(value || fallback || "")
    .replace(/\s+/g, " ")
    .trim();
  return label.slice(0, 160);
}

function normalizeIsoDate(value, fallback) {
  const text = String(value || "").trim();
  if (text && !Number.isNaN(Date.parse(text))) {
    return text;
  }
  return fallback;
}

function normalizeFavoritesPayload(payload, now = new Date().toISOString()) {
  const source = payload && typeof payload === "object" ? payload : {};
  const rawFavorites = source.favorites && typeof source.favorites === "object" ? source.favorites : {};
  const normalized = emptyFavorites();
  const warnings = [];

  Object.entries(rawFavorites).forEach(([rawKey, rawValue]) => {
    const actorKey = normalizeActorKey(rawKey);
    if (!actorKey) {
      warnings.push(`Skipped invalid actor key: ${rawKey}`);
      return;
    }

    const value = rawValue && typeof rawValue === "object" ? rawValue : { label: rawValue };
    const label = normalizeFavoriteLabel(value.label, actorKey);
    normalized.favorites[actorKey] = {
      label,
      created_at: normalizeIsoDate(value.created_at, now),
      updated_at: normalizeIsoDate(value.updated_at, now)
    };
  });

  return { data: normalized, warnings };
}

async function readFavorites(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    if (!text.trim()) {
      return { ok: true, data: emptyFavorites(), warnings: ["Favorites file was empty; started a clean list."] };
    }
    const parsed = JSON.parse(text);
    const normalized = normalizeFavoritesPayload(parsed);
    return { ok: true, data: normalized.data, warnings: normalized.warnings };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { ok: true, data: emptyFavorites(), warnings: [] };
    }
    if (error instanceof SyntaxError) {
      return {
        ok: true,
        data: emptyFavorites(),
        warnings: [`Favorites file was malformed and was ignored: ${error.message}`]
      };
    }
    return { ok: false, data: emptyFavorites(), warnings: [], message: String(error && error.message ? error.message : error) };
  }
}

async function writeFavorites(filePath, payload) {
  const normalized = normalizeFavoritesPayload(payload);
  const directory = path.dirname(filePath);
  const tempPath = `${filePath}.tmp`;
  await fs.mkdir(directory, { recursive: true });
  await fs.writeFile(tempPath, `${JSON.stringify(normalized.data, null, 2)}\n`, "utf8");
  await fs.rename(tempPath, filePath);
  return { ok: true, data: normalized.data, warnings: normalized.warnings };
}

module.exports = {
  FAVORITES_FILENAME,
  FAVORITES_VERSION,
  emptyFavorites,
  favoritesFilePath,
  normalizeActorKey,
  normalizeFavoriteLabel,
  normalizeFavoritesPayload,
  readFavorites,
  writeFavorites
};
