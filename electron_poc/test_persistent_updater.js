const assert = require("assert/strict");
const { EventEmitter } = require("events");
const { PersistentUpdater, prepareRunner } = require("./persistent_updater");
(async () => {
  let quit = false; let spawnOptions;
  const calls = [];
  const child = new EventEmitter(); child.unref = () => {};
  const updater = new PersistentUpdater({
    setupPath: "C:\\MSBT\\MSBT-Setup.exe",
    prepare: () => "C:\\MSBT\\MSBT-Update.exe",
    app: { getVersion: () => "2.15.0", quit: () => { quit = true; } },
    isNewer: (a, b) => a.localeCompare(b,undefined,{numeric:true}) > 0,
    run: (exe, args, options, done) => { calls.push(args); done(null, JSON.stringify({ ok: true, version: "2.15.1" }), ""); },
    start: (exe, args, options) => { spawnOptions=options; calls.push(args); return child; }
  });
  const mixed = new PersistentUpdater({
    setupPath:'fixture',app:{getVersion:()=> '2.17.11'},
    isNewer:(a,b)=>a.localeCompare(b,undefined,{numeric:true})>0,
    installedVersions:()=>['2.17.11','2.17.10'],
    run:(_e,_a,_o,done)=>done(null,JSON.stringify({ok:true,version:'2.17.11'}),'')
  });
  let mixedState='';mixed.on('update-available',()=>mixedState='available');mixed.on('update-not-available',()=>mixedState='none');
  await mixed.checkForUpdates();assert.equal(mixedState,'available');
  mixed.installedVersions=()=>['2.17.11','2.17.11'];await mixed.checkForUpdates();assert.equal(mixedState,'none');
  mixed.app.getVersion=()=> '2.17.12';mixed.installedVersions=()=>['2.17.12','2.17.10'];await mixed.checkForUpdates();assert.equal(mixedState,'none');
  let status = "";
  updater.on("update-available", () => { status = "available"; });
  updater.on("update-downloaded", () => { status = "downloaded"; });
  await updater.checkForUpdates(); assert.equal(status, "available");
  assert.throws(() => updater.quitAndInstall(), /Download/);
  await updater.downloadUpdate(); assert.equal(status, "downloaded");
  updater.gameRoot = 'C:\\Steam Library\\Borderlands 4';
  const launching = updater.quitAndInstall(); assert.equal(quit, false);
  assert.equal(spawnOptions.cwd, require("path").dirname("C:\\MSBT\\MSBT-Update.exe"));
  child.emit("spawn"); await launching; assert.equal(quit, true);
  assert.deepEqual(calls.map(c => c[0]), ["--check", "--download", "--apply"]);
  assert.equal(calls[2][2], String(process.pid));
  assert.deepEqual(calls[2].slice(3), ['--game-root', updater.gameRoot]);
  quit = false;
  const failedChild = new EventEmitter();
  updater.start = () => failedChild;
  const failedLaunch = updater.quitAndInstall();
  failedChild.emit('error', new Error('access denied'));
  await assert.rejects(failedLaunch, /access denied/);
  assert.equal(quit, false); assert.equal(updater.ready, true);
  const fs=require('fs'), os=require('os'), path=require('path');
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'msbt-runner-test-'));
  const prior=process.env.LOCALAPPDATA;
  try {
    process.env.LOCALAPPDATA=temp;
    const setup=path.join(temp,'setup.exe');fs.writeFileSync(setup,'test setup');
    const old=path.join(temp,'Programs','MSBT','MSBT-Update.exe');fs.mkdirSync(path.dirname(old),{recursive:true});fs.writeFileSync(old,'old runner');
    const one=prepareRunner(setup),two=prepareRunner(setup);
    assert.notEqual(one,two);assert.notEqual(one,old);
    assert.equal(fs.readFileSync(old,'utf8'),'old runner');assert.equal(fs.readFileSync(two,'utf8'),'test setup');
  } finally { if(prior===undefined)delete process.env.LOCALAPPDATA;else process.env.LOCALAPPDATA=prior; }
  updater.run = (e, a, o, done) => done(new Error("failed"), "", "checksum mismatch");
  await assert.rejects(updater.downloadUpdate(), /checksum mismatch/);
  assert.equal(updater.ready, false); assert.equal(updater.busy, false);
  console.log("Persistent updater integration checks passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
