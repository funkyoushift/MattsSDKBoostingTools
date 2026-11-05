"use strict";
const fs = require("fs/promises");
const path = require("path");
const { createHash } = require("crypto");
const os = require("os");
const digest = bytes => createHash("sha256").update(bytes).digest("hex");
const PAK_NAME = "pakchunk90-Windows_90_P.pak";
const COMPANION_NAME = "ShiftManagement.sdkmod";
const MODULE_NAME = "ShiftManagement";

async function readOptional(file) {
  try { return await fs.readFile(file); }
  catch (error) { if (error.code === "ENOENT") return null; throw error; }
}

async function saveBackup(gameRoot, bytes, suffix) {
  if (!bytes) return "";
  const backupDir = path.join(gameRoot, "MSBT-backups", "afk-shift");
  const backup = path.join(backupDir, `${digest(bytes)}.${suffix}`);
  await fs.mkdir(backupDir, { recursive: true });
  try { await fs.writeFile(backup, bytes, { flag: "wx" }); }
  catch (error) { if (error.code !== "EEXIST" || digest(await fs.readFile(backup)) !== digest(bytes)) throw error; }
  return backup;
}

// Preserve existing file identities (including PAK hardlinks) when replacing bytes.
async function overwriteExisting(file, bytes) {
  const handle = await fs.open(file, "r+");
  try {
    await handle.truncate(0);
    await handle.writeFile(bytes);
  } finally { await handle.close(); }
}

async function installPak(bundleRoot, gameRoot, options = {}) {
  const manifest = JSON.parse(await fs.readFile(path.join(bundleRoot, "manifest.json"), "utf8"));
  const bytes = await fs.readFile(path.join(bundleRoot, PAK_NAME));
  const companionBytes = await fs.readFile(path.join(bundleRoot, COMPANION_NAME));
  if (digest(bytes) !== manifest.sha256) throw new Error("Bundled AFK SHiFT PAK failed verification.");
  if (digest(companionBytes) !== manifest.companion_sha256) throw new Error("Bundled SHiFT storage companion failed verification.");
  const destination = path.join(gameRoot, "OakGame", "Content", "Paks", PAK_NAME);
  const sdkMods = path.join(gameRoot, "sdk_mods");
  const companionDestination = path.join(sdkMods, COMPANION_NAME);
  const settingsPath = path.join(sdkMods, "settings", `${MODULE_NAME}.json`);
  const [previous, previousCompanion, settingsBytes] = await Promise.all([
    readOptional(destination), readOptional(companionDestination), readOptional(settingsPath)
  ]);
  let parsed = {};
  if (settingsBytes) {
    parsed = JSON.parse(settingsBytes.toString("utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Invalid SHiFT companion settings; existing file preserved.");
  }
  const enabledBytes = Buffer.from(`${JSON.stringify({ ...parsed, enabled: true }, null, 4)}\n`, "utf8");
  const pakUnchanged = Boolean(previous && digest(previous) === manifest.sha256);
  const companionUnchanged = Boolean(previousCompanion && digest(previousCompanion) === manifest.companion_sha256);
  const backup = !pakUnchanged ? await saveBackup(gameRoot, previous, "pak") : "";
  const companionBackup = !companionUnchanged ? await saveBackup(gameRoot, previousCompanion, "sdkmod") : "";
  const settingsBackup = await saveBackup(gameRoot, settingsBytes, "json");
  const entries = [
    { name: "pak", file: destination, before: previous, next: bytes, unchanged: pakUnchanged },
    { name: "companion", file: companionDestination, before: previousCompanion, next: companionBytes, unchanged: companionUnchanged },
    { name: "settings", file: settingsPath, before: settingsBytes, next: enabledBytes,
      unchanged: Boolean(settingsBytes && settingsBytes.equals(enabledBytes)) }
  ];
  const staging = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-shift-stage-"));
  const changed = [];
  let result = null, primaryError = null;
  try {
    for (const entry of entries) {
      entry.stage = path.join(staging, entry.name);
      await fs.writeFile(entry.stage, entry.next, { flag: "wx" });
      if (digest(await fs.readFile(entry.stage)) !== digest(entry.next)) throw new Error(`Staged ${entry.name} verification failed.`);
    }
    for (const entry of entries) {
      if (entry.unchanged) continue;
      await fs.mkdir(path.dirname(entry.file), { recursive: true });
      const current = await readOptional(entry.file);
      if ((entry.before === null) !== (current === null) || (current && !current.equals(entry.before))) {
        throw new Error(`SHiFT ${entry.name} changed during installation; installation stopped.`);
      }
      if (entry.before) {
        changed.push(entry);
        await overwriteExisting(entry.file, entry.next);
      } else {
        const handle = await fs.open(entry.file, "wx");
        changed.push(entry);
        try { await handle.writeFile(entry.next); }
        finally { await handle.close(); }
      }
      if (digest(await fs.readFile(entry.file)) !== digest(entry.next)) throw new Error(`Installed SHiFT ${entry.name} verification failed.`);
      if (options.checkpoint) await options.checkpoint(entry.name);
    }
    const enabled = { ok: true, path: sdkMods, settingsDir: path.dirname(settingsPath),
      mods: [{ moduleName: MODULE_NAME, path: settingsPath, enabled: true }],
      message: `Enabled ${MODULE_NAME} via sdk_mods/settings/*.json.` };
    result = { installed: true, unchanged: pakUnchanged && companionUnchanged, destination, backup,
      companionDestination, companionBackup, settingsBackup, enabled };
    return result;
  } catch (error) {
    const failures = [];
    for (const entry of changed.reverse()) {
      try {
        if (entry.before) {
          await overwriteExisting(entry.file, entry.before);
          const restored = await readOptional(entry.file);
          if (!restored || !restored.equals(entry.before)) throw new Error("restored bytes differ from original");
        } else {
          await fs.unlink(entry.file);
          if (await readOptional(entry.file) !== null) throw new Error("created file remains after rollback");
        }
      } catch (rollbackError) { failures.push(`${entry.name}: ${rollbackError.message}`); }
    }
    if (failures.length) error.message += `; rollback incomplete: ${failures.join("; ")}. Backups: ${[backup, companionBackup, settingsBackup].filter(Boolean).join(", ") || "none"}`;
    primaryError = error;
    throw error;
  } finally {
    try {
      if (options.cleanupStage) await options.cleanupStage(staging);
      else await fs.rm(staging, { recursive: true, force: true });
    } catch (cleanupError) {
      const warning = `Could not remove temporary SHiFT staging directory ${staging}: ${cleanupError.message}`;
      if (result) result.warnings = [...(result.warnings || []), warning];
      else if (primaryError) primaryError.message += `; ${warning}`;
    }
  }
}
module.exports = { installPak };
