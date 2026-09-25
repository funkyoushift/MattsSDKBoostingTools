"use strict";
const fs = require("fs/promises");
const path = require("path");
const { createHash } = require("crypto");
const digest = bytes => createHash("sha256").update(bytes).digest("hex");

async function installPak(bundleRoot, gameRoot) {
  const manifest = JSON.parse(await fs.readFile(path.join(bundleRoot, "manifest.json"), "utf8"));
  const name = "pakchunk90-Windows_90_P.pak";
  const bytes = await fs.readFile(path.join(bundleRoot, name));
  if (digest(bytes) !== manifest.sha256) throw new Error("Bundled AFK SHiFT PAK failed verification.");
  const destination = path.join(gameRoot, "OakGame", "Content", "Paks", name);
  let previous;
  try { previous = await fs.readFile(destination); }
  catch (error) { if (error.code !== "ENOENT") throw error; }
  if (previous && digest(previous) === manifest.sha256) return { installed: true, unchanged: true, destination };
  let backup = "";
  if (previous) {
    const backupDir = path.join(gameRoot, "MSBT-backups", "afk-shift");
    await fs.mkdir(backupDir, { recursive: true });
    backup = path.join(backupDir, `${digest(previous)}.pak`);
    try { await fs.writeFile(backup, previous, { flag: "wx" }); }
    catch (error) { if (error.code !== "EEXIST" || digest(await fs.readFile(backup)) !== digest(previous)) throw error; }
  }
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, bytes);
  if (digest(await fs.readFile(destination)) !== manifest.sha256) throw new Error("Installed AFK SHiFT PAK verification failed.");
  return { installed: true, destination, backup };
}
module.exports = { installPak };
