'use strict';
// Run with Node: a child Electron process exercises real ASAR filesystem semantics.
const assert = require('assert/strict');
const fs = require('fs/promises');
const path = require('path');

if (process.versions.electron) {
  const {app} = require('electron');
  const {EventEmitter} = require('events');
  const updaterModule = process.env.MSBT_UPDATER_ASAR
    ? path.join(process.env.MSBT_UPDATER_ASAR, 'platform_release_updater.js')
    : './platform_release_updater';
  const {WindowsReleaseUpdater} = require(updaterModule);
  (async () => {
    const root = process.argv[2];
    const archive = path.join(root, 'install', 'resources', 'app.asar');
    await assert.rejects(fs.access(archive), {code: 'ENOENT'});
    await require('original-fs').promises.access(archive);
    let starts = 0, quits = 0;
    const fakeApp = {getPath: () => root, quit: () => { quits++; }};
    let payload;
    const start = (_exe,args,options) => {
      starts++;
      assert.equal(options.windowsHide,true);
      assert.equal(options.detached,undefined);
      const bootstrapData=JSON.parse(Buffer.from(args.at(-1),'base64').toString());
      payload=JSON.parse(Buffer.from(bootstrapData.payload,'base64').toString());
      const child=new EventEmitter();child.kill=()=>{};
      setImmediate(async()=>{await fs.writeFile(payload.readyFile,payload.readyToken);child.emit('exit',0,null);});
      return child;
    };
    const makeUpdater = executable => {
      const updater = new WindowsReleaseUpdater({app: fakeApp, isNewer: () => true, executable, start});
      updater.ready = true;
      updater.downloaded = path.join(root, 'verified-installer.exe');
      return updater;
    };
    const concurrent=makeUpdater(path.join(root,'install','MSBT.exe'));
    const first=concurrent.quitAndInstall(),second=concurrent.quitAndInstall();
    assert.equal(first,second);
    await Promise.all([first,second]);
    assert.equal(starts, 1);
    assert.equal(quits, 1);
    assert.equal((await fs.readFile(payload.authorizeFile,'utf8')).trim(),payload.readyToken);
    const failed=makeUpdater(path.join(root,'install','MSBT.exe'));
    failed.start=()=>{throw Error('Bootstrap startup failed');};
    await assert.rejects(failed.quitAndInstall(),/Bootstrap startup failed/);
    assert.equal(failed.ready,true);assert.equal(quits,1);
    await assert.rejects(makeUpdater(path.join(root, 'missing', 'MSBT.exe')).quitAndInstall(), {code: 'ENOENT'});
    assert.equal(starts, 1);
    assert.equal(quits, 1);
    failed.start=start;await failed.quitAndInstall();
    assert.equal(starts,2);assert.equal(quits,2);
    console.log(`PASS Electron ASAR physical access and guarded Windows handoff (${process.env.MSBT_UPDATER_ASAR ? 'packaged' : 'source'} updater)`);
    app.exit(0);
  })().catch(error => { console.error(error); app.exit(1); });
} else {
  const os = require('os');
  const {execFile} = require('child_process');
  const exec = require('util').promisify(execFile);
  (async () => {
    if (process.platform !== 'win32') throw Error('Windows is required for the Windows handoff fixture.');
    const root = await fs.mkdtemp(path.join(os.tmpdir(), 'msbt-electron-asar-'));
    try {
      const source = path.join(root, 'source');
      await fs.mkdir(source);
      await fs.writeFile(path.join(source, 'fixture.txt'), 'fixture');
      await fs.mkdir(path.join(root, 'install', 'resources'), {recursive: true});
      await fs.mkdir(path.join(root, 'missing'));
      await fs.writeFile(path.join(root, 'install', 'MSBT.exe'), 'fixture');
      await fs.writeFile(path.join(root, 'missing', 'MSBT.exe'), 'fixture');
      await require('@electron/asar').createPackage(source, path.join(root, 'install', 'resources', 'app.asar'));
      const {stdout, stderr} = await exec(require('electron'), [__filename, root], {timeout: 30000});
      process.stdout.write(stdout);
      if (stderr) process.stderr.write(stderr);
    } finally {
      await fs.rm(root, {recursive: true, force: true});
    }
  })().catch(error => { console.error(error); process.exitCode = 1; });
}
