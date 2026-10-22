"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");

const MAX_LOG_BYTES = 64 * 1024;
const MAX_CONTEXT_BYTES = 256 * 1024;
const MAX_DUMP_BYTES = 20 * 1024 * 1024;
const PREFERENCES_FILE = "failure_reporting.json";

function redact(text) {
  return String(text)
    .replace(/@U[^\s<>"']+/g, "[redacted serial]")
    .replace(/\b(Authorization|Cookie|Set-Cookie|access[_ -]?token|refresh[_ -]?token|password|api[_ -]?key)\s*[:=]\s*[^\r\n]+/gi, "$1: [redacted]")
    .replace(/\b(LoginId|EpicAccountId|SteamId|account[_ -]?id|user[_ -]?id|DisplayName|UserName|PlayerName|ComputerName|MachineId|SessionId|DeviceId|PlatformUserId|CommandLine|UserDescription)\s*[:=]\s*[^\r\n<]+/gi, "$1: [redacted]")
    .replace(/(<(?:LoginId|EpicAccountId|SteamId|AccountId|UserId|DisplayName|UserName|PlayerName|ComputerName|MachineId|SessionId|DeviceId|PlatformUserId|CommandLine|UserDescription)>)[^<]*(<\/)/gi, "$1[redacted]$2")
    .replace(/\b[A-Z]:\\Users\\[^\\\r\n]+/gi, "C:\\Users\\[redacted]")
    .replace(/\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/g, "[redacted email]")
    .replace(/\b[a-f0-9]{32,40}\b/gi, "[redacted identifier]")
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "[redacted IP]");
}

async function preferences(userData) {
  try {
    const file = path.join(userData, PREFERENCES_FILE);
    const data = JSON.parse(await fs.readFile(file, "utf8"));
    const enabled = data.version === 1 && data.enabled === true;
    const fileTime = enabled && !data.enabledAt ? new Date((await fs.stat(file)).mtimeMs).toISOString() : "";
    return {enabled,
      includeDumps: enabled && data.includeDumps === true,
      enabledAt: typeof data.enabledAt === "string" && data.enabledAt ? data.enabledAt : fileTime};
  } catch {
    return {enabled: false, includeDumps: false, enabledAt: ""};
  }
}

async function setPreferences(userData, value) {
  const file = path.join(userData, PREFERENCES_FILE);
  await fs.mkdir(userData, {recursive: true});
  const current = await fs.lstat(file).catch(() => null);
  if (current?.isSymbolicLink()) throw new Error("Reporting preference path is a link");
  const old = await preferences(userData);
  const enabled = value?.enabled === true;
  const data = {version: 1, enabled, includeDumps: enabled && value?.includeDumps === true,
    enabledAt: enabled ? (old.enabled ? old.enabledAt : "") || new Date().toISOString() : ""};
  const temporary = `${file}.${process.pid}.${crypto.randomUUID()}.tmp`;
  try {
    await fs.writeFile(temporary, JSON.stringify(data), {encoding: "utf8", flag: "wx", mode: 0o600});
    await fs.rename(temporary, file);
  } finally { await fs.rm(temporary, {force: true}).catch(() => {}); }
  return data;
}

async function latestFile(folder, predicate) {
  let entries;
  try { entries = await fs.readdir(folder, {withFileTypes: true}); } catch { return null; }
  const files = [];
  for (const entry of entries) {
    if (!entry.isFile() || !predicate(entry.name)) continue;
    const file = path.join(folder, entry.name);
    const stat = await fs.lstat(file).catch(() => null);
    if (stat?.isFile() && !stat.isSymbolicLink()) files.push({file, mtime: stat.mtimeMs});
  }
  files.sort((a, b) => b.mtime - a.mtime);
  return files[0]?.file || null;
}

async function latestCrashFolder(savedRoot) {
  const root = path.join(savedRoot, "Crashes");
  let entries;
  try { entries = await fs.readdir(root, {withFileTypes: true}); } catch { return null; }
  const folders = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const folder = path.join(root, entry.name);
    const stat = await fs.lstat(folder).catch(() => null);
    if (stat?.isDirectory() && !stat.isSymbolicLink()) folders.push({folder, mtime: stat.mtimeMs});
  }
  folders.sort((a, b) => b.mtime - a.mtime);
  return folders[0]?.folder || null;
}

async function readBounded(file, limit, tail = false) {
  const stat = await fs.lstat(file).catch(() => null);
  if (!stat?.isFile() || stat.isSymbolicLink() || stat.size === 0) return null;
  if (!tail && stat.size > limit) return null;
  const length = Math.min(stat.size, limit);
  const handle = await fs.open(file, "r");
  try {
    const buffer = Buffer.alloc(length);
    const {bytesRead} = await handle.read(buffer, 0, length, tail ? stat.size - length : 0);
    return buffer.subarray(0, bytesRead);
  } finally { await handle.close(); }
}

async function collect({savedRoot, includeDumps = false}) {
  const crashFolder = await latestCrashFolder(savedRoot);
  if (!crashFolder) return null;
  const contextFile = path.join(crashFolder, "CrashContext.runtime-xml");
  const context = await readBounded(contextFile, MAX_CONTEXT_BYTES);
  if (!context) return null;
  const files = [{name: "CrashContext.runtime-xml", kind: "text", text: redact(context.toString("utf8"))}];
  const log = await latestFile(path.join(savedRoot, "Logs"), name => name.toLowerCase().endsWith(".log"));
  if (log) {
    const bytes = await readBounded(log, MAX_LOG_BYTES, true);
    if (bytes) files.push({name: "recent-game.log", kind: "text", text: redact(bytes.toString("utf8"))});
  }
  if (includeDumps) {
    const dump = await readBounded(path.join(crashFolder, "UEMinidump.dmp"), MAX_DUMP_BYTES);
    if (dump) files.push({name: "UEMinidump.dmp", kind: "binary", bytes: dump});
  }
  const contextStat = await fs.lstat(contextFile);
  return {id: crypto.createHash("sha256").update(context).update(String(contextStat.mtimeMs)).digest("hex"),
    occurredAt: new Date(contextStat.mtimeMs).toISOString(), files};
}

module.exports = {collect, preferences, setPreferences, redact, MAX_LOG_BYTES, MAX_CONTEXT_BYTES, MAX_DUMP_BYTES};
