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
    const start = () => {
      starts++;
      const child = new EventEmitter();
      child.unref = () => {};
      setImmediate(() => child.emit('spawn'));
      return child;
    };
    const makeUpdater = executable => {
      const updater = new WindowsReleaseUpdater({app: fakeApp, isNewer: () => true, executable, start});
      updater.ready = true;
      updater.downloaded = path.join(root, 'verified-installer.exe');
      return updater;
    };
    await makeUpdater(path.join(root, 'install', 'MSBT.exe')).quitAndInstall();
    assert.equal(starts, 1);
    assert.equal(quits, 1);
    await assert.rejects(makeUpdater(path.join(root, 'missing', 'MSBT.exe')).quitAndInstall(), {code: 'ENOENT'});
    assert.equal(starts, 1);
    assert.equal(quits, 1);
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
