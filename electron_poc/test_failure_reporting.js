"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const {createFailureReporter} = require("./failure_reporting");
const {redact, collect} = require("./failure_report_bundle");

test("redacts identifiers, secrets, paths, addresses and item serials", () => {
  const text = "LoginId: 123\nEpicAccountId: abc\nAuthorization: Bearer xyz\nC:\\Users\\Martin\\save.sav\nmartin@example.com\n192.168.1.2\n@U123abc.def,ghi\n<CommandLine>private-launch-args</CommandLine>\n0123456789abcdef0123456789abcdef";
  const clean = redact(text);
  for (const value of ["123", "abc", "xyz", "Martin", "martin@example.com", "192.168.1.2", "@U123abc", "def,ghi", "private-launch-args", "0123456789abcdef0123456789abcdef"])
    assert.equal(clean.includes(value), false, value);
});

test("disabled reporting sends nothing; enabled command report omits inputs", async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-report-"));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  const sent = [];
  const reporter = createFailureReporter({userData: root, appVersion: "2.39.4", savedRoot: path.join(root, "Saved"),
    sdkLog: async () => "EpicAccountId: private-id\nError: failed",
    fetchImpl: async (_url, options) => { sent.push(JSON.parse(options.body)); return {ok: true}; }});
  await reporter.commandFailure({action: "mission_complete", status: 500, message: "Failed with LoginId: 123"});
  assert.equal(sent.length, 0);
  await reporter.set({enabled: true, includeDumps: false});
  await reporter.commandFailure({action: "mission_complete", status: 500, message: "Failed with LoginId: 123"});
  for (let i = 0; i < 30 && sent.length === 0; i++) await new Promise(resolve => setTimeout(resolve, 10));
  assert.equal(sent.length, 1);
  assert.equal(sent[0].kind, "command_failure");
  assert.equal(sent[0].action, "mission_complete");
  assert.equal(JSON.stringify(sent[0]).includes("private-id"), false);
  assert.equal(JSON.stringify(sent[0]).includes("LoginId: 123"), false);
  await reporter.set({enabled: false});
  await reporter.commandFailure({action: "another", status: 500, message: "Failed"});
  assert.equal(sent.length, 1);
});

test("crash collection includes bounded text; memory dump only by separate choice", async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-crash-"));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  const folder = path.join(root, "Crashes", "crash-1");
  await fs.mkdir(folder, {recursive: true});
  await fs.mkdir(path.join(root, "Logs"));
  await fs.writeFile(path.join(folder, "CrashContext.runtime-xml"), "<LoginId>secret</LoginId>\nEXCEPTION_ACCESS_VIOLATION");
  await fs.writeFile(path.join(folder, "UEMinidump.dmp"), Buffer.from([1, 2, 3]));
  await fs.writeFile(path.join(root, "Logs", "game.log"), "password=secret\nerror");
  const normal = await collect({savedRoot: root});
  assert.deepEqual(normal.files.map(file => file.name), ["CrashContext.runtime-xml", "recent-game.log"]);
  assert.equal(JSON.stringify(normal).includes("secret"), false);
  const dumps = await collect({savedRoot: root, includeDumps: true});
  assert.deepEqual(dumps.files.find(file => file.name === "UEMinidump.dmp").bytes, Buffer.from([1, 2, 3]));
});

test("turning reporting off aborts an upload and clears its pending file", async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "msbt-optout-"));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  let started;
  let aborted;
  const began = new Promise(resolve => { started = resolve; });
  const stopped = new Promise(resolve => { aborted = resolve; });
  const reporter = createFailureReporter({userData: root, appVersion: "2.39.4", savedRoot: path.join(root, "Saved"),
    sdkLog: async () => "", fetchImpl: (_url, {signal}) => {
      started();
      return new Promise((_resolve, reject) => signal.addEventListener("abort", () => {
        aborted(); reject(new Error("aborted"));
      }, {once: true}));
    }});
  await reporter.set({enabled: true});
  await reporter.commandFailure({action: "test", status: 500, message: "failed"});
  await began;
  await reporter.set({enabled: false});
  await stopped;
  assert.deepEqual(await fs.readdir(path.join(root, "failure-report-outbox")), []);
});
