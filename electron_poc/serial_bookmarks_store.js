const crypto = require("crypto");
const fs = require("fs/promises");
const path = require("path");

const BOOKMARKS_VERSION = 1;
const BOOKMARKS_FILENAME = "serial_bookmarks.json";
const ID_RE = /^[A-Za-z0-9_.:-]{1,96}$/;

function bookmarksFilePath(userDataPath) {
  return path.join(userDataPath, BOOKMARKS_FILENAME);
}

function emptyBookmarks() {
  return { version: BOOKMARKS_VERSION, bookmarks: [], folders: [] };
}

function normalizeText(value, fallback = "", maxLength = 4096) {
  return String(value || fallback || "")
    .replace(/\r\n/g, "\n")
    .trim()
    .slice(0, maxLength);
}

function normalizeName(value) {
  return normalizeText(value, "Untitled Serial", 180).replace(/\s+/g, " ") || "Untitled Serial";
}

function normalizeGroup(value) {
  return normalizeText(value, "Default", 180).replace(/\s+/g, " ") || "Default";
}

function normalizeIsoDate(value, fallback) {
  const text = String(value || "").trim();
  if (text && !Number.isNaN(Date.parse(text))) return text;
  return fallback;
}

function generatedBookmarkId(record) {
  const basis = ["serial", "name", "group", "source", "url"]
    .map((key) => String((record && record[key]) || ""))
    .join("|");
  const digest = crypto.createHash("sha1").update(basis).digest("hex").slice(0, 16);
  return `bm_${digest}`;
}

function normalizeBookmarkRecord(record, now = new Date().toISOString(), fallbackIndex = 0) {
  const source = record && typeof record === "object" ? record : {};
  const idText = String(source.id || "").trim();
  const id = ID_RE.test(idText) ? idText : `${generatedBookmarkId(source)}_${fallbackIndex}`;
  const createdAt = normalizeIsoDate(source.created_at, now);
  const updatedAt = normalizeIsoDate(source.updated_at, now);
  const normalized = {
    id,
    name: normalizeName(source.name || source.title),
    group: normalizeGroup(source.group || source.category),
    serial: normalizeText(source.serial, "", 20000),
    created_at: createdAt,
    updated_at: updatedAt
  };

  [
    "source",
    "listing",
    "type",
    "manufacturer",
    "rarity",
    "creator",
    "classification",
    "url",
    "tags",
    "notes",
    "mattmab_validator",
    "mattmab_validator_detail"
  ].forEach((key) => {
    const value = normalizeText(source[key], "", 4096);
    if (value) normalized[key] = value;
  });

  if (source.decoded_identity && typeof source.decoded_identity === "object" && !Array.isArray(source.decoded_identity)) {
    normalized.decoded_identity = source.decoded_identity;
  }

  return normalized;
}

function rawBookmarkList(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === "object") {
    if (Array.isArray(payload.bookmarks)) return payload.bookmarks;
    if (Array.isArray(payload.entries)) return payload.entries;
  }
  return [];
}

function normalizeBookmarksPayload(payload, now = new Date().toISOString()) {
  const warnings = [];
  const seenIds = new Set();
  const bookmarks = [];

  rawBookmarkList(payload).forEach((raw, index) => {
    if (!raw || typeof raw !== "object") {
      warnings.push(`Skipped invalid bookmark record at index ${index}.`);
      return;
    }
    const normalized = normalizeBookmarkRecord(raw, now, index);
    if (!normalized.serial) {
      warnings.push(`Skipped bookmark without serial at index ${index}.`);
      return;
    }
    let id = normalized.id;
    let suffix = 2;
    while (seenIds.has(id)) {
      id = `${normalized.id}_${suffix}`;
      suffix += 1;
    }
    normalized.id = id;
    seenIds.add(id);
    bookmarks.push(normalized);
  });

  return {
    data: { version: BOOKMARKS_VERSION, bookmarks, folders: Array.from(new Set([
      ...(Array.isArray(payload?.folders) ? payload.folders.filter(value => typeof value === "string").map(normalizeGroup) : []),
      ...bookmarks.map(row => row.group)
    ])) },
    warnings
  };
}

async function readBookmarks(filePath) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    if (!text.trim()) {
      return { ok: true, data: emptyBookmarks(), warnings: ["Bookmarks file was empty; started a clean list."] };
    }
    const parsed = JSON.parse(text);
    const normalized = normalizeBookmarksPayload(parsed);
    return { ok: true, data: normalized.data, warnings: normalized.warnings };
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return { ok: true, data: emptyBookmarks(), warnings: [] };
    }
    if (error instanceof SyntaxError) {
      return {
        ok: true,
        data: emptyBookmarks(),
        warnings: [`Bookmarks file was malformed and was ignored: ${error.message}`]
      };
    }
    return { ok: false, data: emptyBookmarks(), warnings: [], message: String(error && error.message ? error.message : error) };
  }
}

async function writeBookmarks(filePath, payload) {
  // Older desktop/mobile callers know only bookmarks. Preserve empty folders.
  if (!Array.isArray(payload?.folders)) {
    const previous = await readBookmarks(filePath);
    payload = { bookmarks: rawBookmarkList(payload), folders: previous.data.folders || [] };
  }
  const normalized = normalizeBookmarksPayload(payload);
  const directory = path.dirname(filePath);
  const tempPath = `${filePath}.tmp`;
  await fs.mkdir(directory, { recursive: true });
  await fs.writeFile(tempPath, `${JSON.stringify(normalized.data, null, 2)}\n`, "utf8");
  await fs.rename(tempPath, filePath);
  return { ok: true, data: normalized.data, warnings: normalized.warnings };
}

module.exports = {
  BOOKMARKS_FILENAME,
  BOOKMARKS_VERSION,
  bookmarksFilePath,
  emptyBookmarks,
  generatedBookmarkId,
  normalizeBookmarkRecord,
  normalizeBookmarksPayload,
  readBookmarks,
  writeBookmarks
};
