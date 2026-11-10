'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises'), path = require('node:path'), os = require('node:os');
const {createHash} = require('node:crypto');
const {inspectPak} = require('./pak_install');
const vm = require('node:vm');
const hash = value => createHash('sha256').update(value).digest('hex');

test('SHiFT health checks the complete pair, enabled state and duplicate PAKs without modifying files', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'shift-health-'));
  const bundle = path.join(root, 'bundle'), game = path.join(root, 'game');
  const paks = path.join(game, 'OakGame', 'Content', 'Paks'), mods = path.join(game, 'sdk_mods');
  try {
    await fs.mkdir(bundle, {recursive:true}); await fs.mkdir(paks, {recursive:true});
    await fs.mkdir(path.join(mods, 'settings'), {recursive:true});
    await fs.writeFile(path.join(bundle, 'manifest.json'), JSON.stringify({sha256:hash('pak'), companion_sha256:hash('companion')}));
    assert.equal((await inspectPak(bundle, game)).ok, false);
    await fs.writeFile(path.join(paks, 'pakchunk90-Windows_90_P.pak'), 'pak');
    await fs.writeFile(path.join(mods, 'ShiftManagement.sdkmod'), 'companion');
    const enable = path.join(mods, 'settings', 'ShiftManagement.json');
    await fs.writeFile(enable, '{"enabled":true}');
    assert.equal((await inspectPak(bundle, game)).ok, true);
    await fs.writeFile(path.join(mods, 'ShiftManagement.sdkmod'), 'same version, different bytes');
    const stale = await inspectPak(bundle, game);
    assert.equal(stale.ok, false); assert.equal(stale.files.pak.matches, true); assert.equal(stale.files.companion.matches, false);
    await fs.writeFile(path.join(mods, 'ShiftManagement.sdkmod'), 'companion');
    await fs.writeFile(enable, '{"enabled":false}'); assert.equal((await inspectPak(bundle, game)).enabled, false);
    await fs.writeFile(enable, '{"enabled":true}');
    const duplicate = path.join(paks, 'pakchunk90-Windows_90_P (1).pak');
    await fs.writeFile(duplicate, 'other dashboard');
    assert.deepEqual((await inspectPak(bundle, game)).conflicts, [duplicate]);
    assert.equal(await fs.readFile(duplicate, 'utf8'), 'other dashboard');
    await fs.writeFile(enable, '{bad'); assert.equal((await inspectPak(bundle, game)).status, 'unverified');
    assert.equal(await fs.readFile(enable, 'utf8'), '{bad');
  } finally { await fs.rm(root, {recursive:true, force:true}); }
});

test('a matching SDK with stale SHiFT files gets actionable integration guidance', async () => {
  const source = await fs.readFile(path.join(__dirname, 'renderer.js'), 'utf8');
  const section = source.slice(source.indexOf('function sdkModNeedsAttention('), source.indexOf('function renderBoostUpdateNotice('));
  const context = {state:{latestUpdateState:{}}};
  vm.runInNewContext(section, context);
  const info = {installedSdkmod:{status:'current', message:'SDK matches'},
    shiftIntegration:{ok:false, message:'SHiFT companion differs from this app.'}};
  assert.equal(context.sdkModNeedsAttention(info), false);
  const notice = context.updateNoticeInfo(info);
  assert.equal(notice.title, 'SHiFT Integration Needs Attention');
  assert.match(notice.message, /companion differs/);
  assert.match(notice.message, /complete game integration/);
  assert.equal(notice.showUpdates, true);
  info.shiftIntegration.ok = true;
  assert.equal(context.updateNoticeInfo(info), null);
  info.installedSdkmod.status = 'different';
  assert.equal(context.updateNoticeInfo(info).title, 'SDK Mod Needs Attention');
});
