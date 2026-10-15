const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { steamIdFromSavePath, normalizePrefsPayload } = require('./matt_editor_prefs_store');
const helper = path.resolve(__dirname, '../external_app/v22_parts_codes_fixed/matt_editor_blcrypt.js');
function call(payload) {
  const result = spawnSync(process.execPath, [helper], { input: JSON.stringify(payload), encoding: 'utf8' });
  assert.equal(result.status, 0);
  return JSON.parse(result.stdout);
}
const yaml = 'state:\n  char_name: Synthetic Epic fixture\n  inventory: {serial: "@USyntheticCase"}\n';
for (const account of ['0123456789abcdef0123456789abcdef', '0123456789ABCDEF0123456789ABCDEF', 'aBcDeFaBcDeFaBcD0123456789abcdef']) {
  const save = path.join('C:', 'Synthetic', 'SaveGames', account, 'Profiles', 'client', '1.sav');
  assert.equal(steamIdFromSavePath(save), account);
  assert.equal(normalizePrefsPayload({ steamId: account }).data.steamId, account);
  const encrypted = call({ command: 'encrypt', steamid: account, yaml_content: yaml });
  assert.equal(encrypted.success, true);
  const ciphertext = encrypted.sav_data || encrypted.encrypted;
  const restored = call({ command: 'decrypt', steamid: steamIdFromSavePath(save), sav_data: ciphertext });
  assert.equal(restored.success, true);
  assert.equal(restored.yaml_content, yaml);
  const wrongCase = account === account.toUpperCase() ? account.toLowerCase() : account.toUpperCase();
  assert.equal(call({ command: 'decrypt', steamid: wrongCase, sav_data: ciphertext }).success, false);
}
console.log('PASS lowercase, uppercase and mixed-case Epic account paths and encrypted-save round trips; incorrect casing rejected');
