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
// File identity is independent of the displayed SemVer. Do not read the private
// protected-player JSON here: only integration files and the enable switch.
async function inspectPak(bundleRoot, gameRoot) {
  try {
    const manifest = JSON.parse(await fs.readFile(path.join(bundleRoot, 'manifest.json'), 'utf8'));
    const paks = path.join(gameRoot, 'OakGame', 'Content', 'Paks');
    const mods = path.join(gameRoot, 'sdk_mods');
    const expected = [
      ['pak', path.join(paks, PAK_NAME), manifest.sha256],
      ['companion', path.join(mods, COMPANION_NAME), manifest.companion_sha256]
    ];
    const files = {};
    for (const [name, file, hash] of expected) {
      if (!/^[a-f0-9]{64}$/i.test(hash || '')) throw new Error('SHiFT bundle manifest is incomplete.');
      const bytes = await readOptional(file);
      files[name] = { path: file, sha256: bytes ? digest(bytes) : '', matches: Boolean(bytes && digest(bytes) === hash) };
    }
    const enabledBytes = await readOptional(path.join(mods, 'settings', 'ShiftManagement.json'));
    const enabled = Boolean(enabledBytes && JSON.parse(enabledBytes.toString('utf8')).enabled === true);
    const conflicts = [], pending = [paks];
    let directories = 0;
    while (pending.length) {
      if (++directories > 256) throw new Error('SHiFT PAK conflict scan exceeded its limit.');
      const folder = pending.pop();
      let entries;
      try { entries = await fs.readdir(folder, {withFileTypes:true}); }
      catch (error) { if (error.code === 'ENOENT') continue; throw error; }
      for (const entry of entries) {
        const file = path.join(folder, entry.name);
        if (entry.isDirectory()) pending.push(file);
        else if (entry.isFile() && /^pakchunk90-Windows_90_P(?: ?\(\d+\))?\.pak$/i.test(entry.name)
          && file.toLowerCase() !== expected[0][1].toLowerCase()) conflicts.push(file);
      }
    }
    const ok = files.pak.matches && files.companion.matches && enabled && !conflicts.length;
    const issues = [];
    if (!files.pak.matches) issues.push('SHiFT PAK is missing or differs from this app');
    if (!files.companion.matches) issues.push('SHiFT companion is missing or differs from this app');
    if (!enabled) issues.push('SHiFT companion is disabled');
    if (conflicts.length) issues.push('additional SHiFT PAK copies may override the bundled file');
    return {ok, status:ok ? 'current' : 'attention', files, enabled, conflicts,
      message:ok ? 'SHiFT PAK and companion match this app and the companion is enabled. Loaded page identity still requires a fresh game session.'
        : issues.join('; ') + '. Check the listed files in Updates before testing settings or background play.'};
  } catch (error) {
    return {ok:false, status:'unverified', conflicts:[], message:`SHiFT integration could not be verified: ${error.message}`};
  }
}
module.exports = { installPak, inspectPak };
