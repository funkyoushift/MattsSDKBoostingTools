const assert = require("assert/strict");
const { EventEmitter } = require("events");
const { PersistentUpdater } = require("./persistent_updater");
(async () => {
  let quit = false; let spawnOptions;
  const calls = [];
  const child = new EventEmitter(); child.unref = () => {};
  const updater = new PersistentUpdater({
    setupPath: "C:\\MSBT\\MSBT-Setup.exe",
    prepare: () => "C:\\MSBT\\MSBT-Update.exe",
    app: { getVersion: () => "2.15.0", quit: () => { quit = true; } },
    isNewer: (a, b) => a !== b,
    run: (exe, args, options, done) => { calls.push(args); done(null, JSON.stringify({ ok: true, version: "2.15.1" }), ""); },
    start: (exe, args, options) => { spawnOptions=options; calls.push(args); return child; }
  });
  let status = "";
  updater.on("update-available", () => { status = "available"; });
  updater.on("update-downloaded", () => { status = "downloaded"; });
  await updater.checkForUpdates(); assert.equal(status, "available");
  assert.throws(() => updater.quitAndInstall(), /Download/);
  await updater.downloadUpdate(); assert.equal(status, "downloaded");
  updater.quitAndInstall(); assert.equal(quit, false);
  assert.equal(spawnOptions.cwd, require("path").dirname("C:\\MSBT\\MSBT-Update.exe"));
  child.emit("spawn"); assert.equal(quit, true);
  assert.deepEqual(calls.map(c => c[0]), ["--check", "--download", "--apply"]);
  assert.equal(calls[2][2], String(process.pid));
  updater.run = (e, a, o, done) => done(new Error("failed"), "", "checksum mismatch");
  await assert.rejects(updater.downloadUpdate(), /checksum mismatch/);
  assert.equal(updater.ready, false); assert.equal(updater.busy, false);
  console.log("Persistent updater integration checks passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
