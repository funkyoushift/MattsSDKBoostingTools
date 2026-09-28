const assert = require('node:assert/strict');
const cryptoNode = require('node:crypto');
globalThis.crypto ??= cryptoNode.webcrypto;
const send = require('./afk_config_upload');
(async () => {
  const payload = { loot: true, guaranteed_codes: '@UCase`\\\n@UCase`\\\n'.repeat(160000), codes: '@UPool', label: 'España 🎁' };
  const chunks = [];
  const calls = [];
  const request = async (action, body) => {
    calls.push(action);
    assert(Buffer.byteLength(JSON.stringify({ action, payload: body })) < 2097152);
    if (body.mode === 'begin') return { data: { ok: true, token: 'test' } };
    if (body.mode === 'append') {
      assert.equal(body.index, chunks.length);
      chunks.push(Buffer.from(body.data, 'base64'));
      return { data: { ok: true, count: chunks.length } };
    }
    assert.equal(action, 'afk_lobby_start_uploaded');
    const all = Buffer.concat(chunks);
    assert.equal(body.size, all.length);
    assert.equal(body.count, chunks.length);
    assert.equal(body.sha256, cryptoNode.createHash('sha256').update(all).digest('hex'));
    assert.deepEqual(JSON.parse(all), payload);
    return { data: { ok: true, queued: true } };
  };
  await send('afk_lobby_start', payload, request, true);
  assert.equal(calls.at(-1), 'afk_lobby_start_uploaded'); // no cancellation of queued commit
  await assert.rejects(send('afk_lobby_start', payload, request, false), /Update the SDK/);
  let cancelled = false;
  await assert.rejects(send('afk_lobby_start', payload, async (_, body) => {
    if (body.mode === 'begin') return { ok: true, token: 'test' };
    if (body.mode === 'cancel') { cancelled = true; return { ok: true }; }
    return { ok: false, message: 'disk full' };
  }, true), /disk full/);
  assert(cancelled);
  let original;
  await send('afk_lobby_start', { codes: '@USmall' }, async (action, data) => { original = { action, data }; }, false);
  assert.deepEqual(original, { action: 'afk_lobby_start', data: { codes: '@USmall' } });
  console.log('PASS AFK large-list transfer, integrity, interruption, queued commit, old SDK, small requests');
})().catch(error => { console.error(error); process.exitCode = 1; });
