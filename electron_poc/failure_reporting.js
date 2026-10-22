"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");
const {collect, preferences, setPreferences, redact} = require("./failure_report_bundle");

const ENDPOINT = "https://msbt-failure-reports.screename53.workers.dev/v1/reports";
const MAX_PENDING = 20;
const MAX_LOG = 64 * 1024;

function createFailureReporter({userData, appVersion, savedRoot, sdkLog, fetchImpl = fetch, endpoint = ENDPOINT}) {
  const outbox = path.join(userData, "failure-report-outbox");
  let active = false;
  let again = false;
  let currentController = null;
  let revoked = false;
  let lastFailure = "";
  let lastFailureAt = 0;

  async function safeOutbox() {
    const stat = await fs.lstat(outbox).catch(() => null);
    return !stat || (stat.isDirectory() && !stat.isSymbolicLink());
  }

  async function post(report) {
    if (revoked || !(await preferences(userData)).enabled) throw new Error("Reporting was turned off");
    const controller = new AbortController();
    currentController = controller;
    try {
      const response = await fetchImpl(endpoint, {
        method: "POST", redirect: "error", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(report), signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)])
      });
      if (!response.ok) throw new Error(`Report inbox returned ${response.status}`);
    } finally { if (currentController === controller) currentController = null; }
  }

  async function flush() {
    if (active) { again = true; return; }
    if (revoked || !(await preferences(userData)).enabled || !(await safeOutbox())) return;
    active = true;
    try {
      const names = (await fs.readdir(outbox).catch(() => [])).filter(name => /^[a-f0-9-]{36}\.json$/.test(name)).sort();
      for (const name of names.slice(0, MAX_PENDING)) {
        if (revoked || !(await preferences(userData)).enabled) break;
        const file = path.join(outbox, name);
        const stat = await fs.lstat(file).catch(() => null);
        if (!stat?.isFile() || stat.isSymbolicLink() || stat.size > 30 * 1024 * 1024) continue;
        let report;
        try { report = JSON.parse(await fs.readFile(file, "utf8")); }
        catch { console.error("[MSBT] Skipping unreadable queued report"); continue; }
        const consent = await preferences(userData);
        if (revoked || !consent.enabled) break;
        const occurredAt = Date.parse(report.occurredAt);
        if (!Number.isFinite(occurredAt) || (consent.enabledAt && occurredAt < Date.parse(consent.enabledAt))) {
          await fs.rm(file, {force: true});
          continue;
        }
        try { await post(report); await fs.rm(file, {force: true}); } catch { break; }
      }
    } catch (error) { console.error("[MSBT] Report outbox error:", error.message); }
    finally {
      active = false;
      if (again) { again = false; void flush(); }
    }
  }

  async function enqueue(report) {
    if (revoked || !(await preferences(userData)).enabled) return false;
    await fs.mkdir(outbox, {recursive: true});
    if (!(await safeOutbox())) return false;
    const names = (await fs.readdir(outbox)).filter(name => /^[a-f0-9-]{36}\.json$/.test(name));
    if (names.length >= MAX_PENDING) return false;
    const file = path.join(outbox, `${crypto.randomUUID()}.json`);
    await fs.writeFile(file, JSON.stringify({version: 1, appVersion, ...report}), {flag: "wx", mode: 0o600});
    void flush();
    return true;
  }

  async function commandFailure({action, status, message}) {
    if (revoked || !(await preferences(userData)).enabled) return;
    const safeAction = String(action || "unknown").replace(/[^A-Za-z0-9_.:-]/g, "_").slice(0, 80);
    const safeMessage = redact(String(message || "Command failed")).slice(0, 2048);
    const signature = `${safeAction}:${status}:${safeMessage}`;
    if (signature === lastFailure && Date.now() - lastFailureAt < 10 * 60 * 1000) return;
    lastFailure = signature; lastFailureAt = Date.now();
    let log = "";
    try { log = redact(String(await sdkLog())).slice(-MAX_LOG); } catch {}
    await enqueue({kind: "command_failure", occurredAt: new Date().toISOString(),
      action: safeAction, status: Number(status) || 0, message: safeMessage,
      files: log ? [{name: "recent-sdk.log", kind: "text", text: log}] : []});
  }

  async function desktopFailure(kind, error) {
    if (revoked || !(await preferences(userData)).enabled) return;
    await enqueue({kind: "desktop_failure", occurredAt: new Date().toISOString(),
      action: String(kind).slice(0, 80), message: redact(error?.stack || String(error)).slice(0, 8192), files: []});
  }

  async function scanGameCrashes() {
    const pref = await preferences(userData);
    if (revoked || !pref.enabled) return;
    const bundle = await collect({savedRoot, includeDumps: pref.includeDumps}).catch(() => null);
    if (!bundle) return;
    if (Date.now() - Date.parse(bundle.occurredAt) < 15000) return;
    const marker = path.join(userData, "failure-report-last-crash.txt");
    if ((await fs.readFile(marker, "utf8").catch(() => "")) === bundle.id) return;
    if (pref.enabledAt && Date.parse(bundle.occurredAt) < Date.parse(pref.enabledAt)) return;
    const files = bundle.files.map(file => file.kind === "binary"
      ? {name: file.name, kind: "binary", base64: file.bytes.toString("base64")}
      : file);
    if (await enqueue({kind: "game_crash", occurredAt: bundle.occurredAt, files}))
      await fs.writeFile(marker, bundle.id, "utf8");
  }

  async function set(value) {
    if (value?.enabled !== true) { revoked = true; currentController?.abort(); }
    const result = await setPreferences(userData, value);
    if (!result.enabled) {
      if (!(await safeOutbox())) return result;
      const names = await fs.readdir(outbox).catch(() => []);
      for (const name of names) if (/^[a-f0-9-]{36}\.json$/.test(name)) await fs.rm(path.join(outbox, name), {force: true});
    } else { revoked = false; void scanGameCrashes(); void flush(); }
    return result;
  }
  return {get: () => preferences(userData), set, commandFailure, desktopFailure, scanGameCrashes, flush};
}

module.exports = {createFailureReporter, ENDPOINT};
