const assert = require("assert");
const os = require("os");
const path = require("path");
const {
  emptyPrefs,
  normalizePrefsPayload,
  normalizeSteamId,
  steamIdFromSavePath,
  allowedSaveExtension,
  folderFromFile
} = require("./matt_editor_prefs_store");

const steamId = normalizeSteamId("  76561198000000000  ");
assert.strictEqual(steamId, "76561198000000000");

assert.strictEqual(
  steamIdFromSavePath("C:\\Users\\x\\Documents\\My Games\\Bl4\\Saved\\SaveGames\\76561198000000000\\Profiles\\client\\1.sav"),
  "76561198000000000"
);
assert.strictEqual(
  steamIdFromSavePath("G:/OneDrive/Documents/My Games/Borderlands 4/Saved/SaveGames/76561198123456789/1007.sav"),
  "76561198123456789"
);
assert.strictEqual(
  steamIdFromSavePath("D:/Saves/SaveGames/0123456789abcdef0123456789abcdef/Profiles/client/profile.sav"),
  "0123456789abcdef0123456789abcdef"
);
assert.strictEqual(steamIdFromSavePath("C:\\Users\\x\\Desktop\\1007.sav"), "");
assert.strictEqual(steamIdFromSavePath("C:\\Users\\x\\Desktop\\export.yaml"), "");

const saveFile = path.join(os.homedir(), "Documents", "My Games", "Bl4", "Save4.sav");
const normalized = normalizePrefsPayload({
  steamId,
  lastSaveFile: saveFile,
  lastProfileFile: path.join(os.homedir(), "Documents", "My Games", "Bl4", "profile.sav"),
  unexpected: "drop"
});
assert.strictEqual(normalized.data.steamId, steamId);
assert.strictEqual(normalized.data.lastSaveFile, path.resolve(saveFile));
assert.strictEqual(normalized.data.lastSaveFolder, folderFromFile(saveFile));
assert.ok(allowedSaveExtension(normalized.data.lastSaveFile));
assert.strictEqual(emptyPrefs().lastSaveFile, "");
assert.ok(!("unexpected" in normalized.data));

console.log("matt editor prefs store tests passed");
