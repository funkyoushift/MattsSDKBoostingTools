const fs = require("fs/promises");
const path = require("path");

const FAVORITES_VERSION = 1;
const FAVORITES_FILENAME = "travel_favorites.json";
const KIND_MAP = "map";
const KIND_STATION = "station";

function favoritesFilePath(userDataPath) {
  return path.join(userDataPath, FAVORITES_FILENAME);
}

function emptyFavorites() {
  return { version: FAVORITES_VERSION, favorites: {} };
}

function normalizeKind(value) {
  const kind = String(value || "").trim().toLowerCase();
  if (kind === KIND_MAP || kind === KIND_STATION) return kind;
  return "";
}

function normalizeLocationId(value) {
  const id = String(value || "").trim();
  if (!id || id.length > 240) return "";
  // Maps/stations use dotted Unreal names; keep a permissive but bounded charset.
  if (!/^[A-Za-z0-9_./:-]+$/.test(id)) return "";
  return id;
}

function favoriteKey(kind, id) {
  const safeKind = normalizeKind(kind);
  const safeId = normalizeLocationId(id);
  if (!safeKind || !safeId) return "";
  return `${safeKind}:${safeId}`;
}

function normalizeFavoriteLabel(value, fallback = "") {
  const label = String(value || fallback || "")
    .replace(/\s+/g, " ")
    .trim();
  return label.slice(0, 160);
}

function normalizeFavoriteNote(value) {
  const note = String(value || "")
    .replace(/\s+/g, " ")
    .trim();
  return note.slice(0, 320);
}

function normalizeIsoDate(value, fallback) {
  const text = String(value || "").trim();
  if (text && !Number.isNaN(Date.parse(text))) {
    return text;
  }
  return fallback;
}

function normalizeWorld(value) {
  return String(value || "").trim().slice(0, 160);
}

function normalizeFavoritesPayload(payload, now = new Date().toISOString()) {
  const source = payload && typeof payload === "object" ? payload : {};
  const rawFavorites = source.favorites && typeof source.favorites === "object" ? source.favorites : {};
  const normalized = emptyFavorites();
  const warnings = [];

  Object.entries(rawFavorites).forEach(([rawKey, rawValue]) => {
    const value = rawValue && typeof rawValue === "object" ? rawValue : { label: rawValue };
    let kind = normalizeKind(value.kind);
    let id = normalizeLocationId(value.id);

    if ((!kind || !id) && typeof rawKey === "string" && rawKey.includes(":")) {
      const splitAt = rawKey.indexOf(":");
      kind = kind || normalizeKind(rawKey.slice(0, splitAt));
      id = id || normalizeLocationId(rawKey.slice(splitAt + 1));
    }

    const key = favoriteKey(kind, id);
    if (!key) {
      warnings.push(`Skipped invalid travel favorite: ${rawKey}`);
      return;
    }

    const defaultLabel = kind === KIND_STATION ? id : id;
    normalized.favorites[key] = {
      kind,
      id,
      world: kind === KIND_STATION ? normalizeWorld(value.world) : "",
      label: normalizeFavoriteLabel(value.label, defaultLabel),
      note: normalizeFavoriteNote(value.note),
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
      return { ok: true, data: emptyFavorites(), warnings: ["Travel favorites file was empty; started a clean list."] };
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
        warnings: [`Travel favorites file was malformed and was ignored: ${error.message}`]
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
  KIND_MAP,
  KIND_STATION,
  emptyFavorites,
  favoriteKey,
  favoritesFilePath,
  normalizeFavoriteLabel,
  normalizeFavoriteNote,
  normalizeFavoritesPayload,
  normalizeKind,
  normalizeLocationId,
  readFavorites,
  writeFavorites
};
