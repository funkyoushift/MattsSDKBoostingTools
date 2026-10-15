'use strict';

// Runs the save worker without the desktop app.
const fs = require('node:fs/promises');
const path = require('node:path');
const readline = require('node:readline');
const { createSaveReplayService } = require('./replay_service');
const { run } = require('./codec');

const endpoint = process.env.MSBT_SELECTOR_ENDPOINT;
const token = process.env.MSBT_SELECTOR_TOKEN;
if (!/^http:\/\/127\.0\.0\.1:[0-9]+$/.test(endpoint || '') || !token) {
  throw Error('Missing local game transport');
}

const emit = value => process.stdout.write(JSON.stringify(value) + '\n');

async function rpc(route, payload) {
  const r = await fetch(endpoint + route, {
    method: 'POST',
    headers: {
      Authorization: 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(25000)
  });
  if (!r.ok) throw Error('Local game transport rejected request');
  return r.json();
}

function codec(command, value, account) {
  const result = run(command === 'decrypt'
    ? { command, steamid: account, sav_data: Buffer.from(value).toString('base64') }
    : { command, steamid: account, yaml_content: value });
  if (!result.success) throw Error(result.error || 'Local save codec failed');
  return command === 'decrypt'
    ? result.yaml_content
    : Buffer.from(result.sav_data, 'base64');
}

const service = createSaveReplayService({
  request: (action, payload) => rpc('/native', { action, payload }),
  helper: payload => rpc('/helper', payload),
  codec,
  saveRoot: process.env.MSBT_SELECTOR_SAVE_ROOT,
  storage: process.env.MSBT_SELECTOR_STORAGE
});

let running = false;
let shuttingDown = false;
let last = '';

function report(result) {
  const key = JSON.stringify(result);
  if (key !== last) {
    last = key;
    emit(result);
  }
  return result;
}

async function pump() {
  if (running || shuttingDown) return;
  running = true;
  try {
    const s = await service.dispatch('status');
    if (s.active && !['failed', 'uncertain', 'interrupted'].includes(s.state)) {
      report(await service.dispatch('advance'));
    }
  } catch (e) {
    emit({ ok: false, message: e.message });
  } finally {
    running = false;
  }
}

const timer = setInterval(pump, 1500);
const lines = readline.createInterface({ input: process.stdin });
let commands = Promise.resolve();

lines.on('line', line => {
  commands = commands.then(async () => {
    try {
      const value = JSON.parse(line);
      if (![
        'start', 'status', 'stop', 'restore',
        'bookmark_save', 'bookmark_list', 'bookmark_start'
      ].includes(value.action)) {
        throw Error('Unsupported command');
      }
      report(await service.dispatch(value.action, value.payload || {}));
    } catch (e) {
      emit({ ok: false, message: e.message });
    }
  });
});

async function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  clearInterval(timer);

  // Finish the current command before releasing the replay lease.
  await commands;
  try {
    await service.dispatch('stop');
  } catch {}
  process.exit(0);
}

lines.on('close', shutdown);
const parent = Number(process.env.MSBT_SELECTOR_PARENT_PID);
if (Number.isSafeInteger(parent) && parent > 0) {
  setInterval(() => {
    try {
      process.kill(parent, 0);
    } catch {
      process.exit(0);
    }
  }, 3000).unref();
}

emit({ ok: true, message: 'Standalone replay worker ready.' });
