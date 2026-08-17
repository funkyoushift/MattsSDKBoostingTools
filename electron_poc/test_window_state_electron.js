"use strict";

/**
 * Behavioral window-state test against a real BrowserWindow. Run with:
 *   electron test_window_state_electron.js
 * It drives real fullscreen and maximize transitions and asserts that the
 * windowed (half-screen style) bounds survive both the transition and the
 * snapshot that main.js would persist.
 */
const assert = require("assert");
const { app, BrowserWindow, screen } = require("electron");
const { bindWindowState } = require("./window_state_tracker");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const fmt = (b) => (b ? `{x:${b.x},y:${b.y},w:${b.width},h:${b.height}}` : "null");
const sameBounds = (a, b) => a && b && a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;

function waitForEvent(win, event, timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      win.removeListener(event, onEvent);
      reject(new Error(`timed out waiting for "${event}"`));
    }, timeoutMs);
    function onEvent() {
      clearTimeout(timer);
      resolve();
    }
    win.once(event, onEvent);
  });
}

async function run() {
  const work = screen.getPrimaryDisplay().workArea;
  // Half-screen-shaped windowed bounds, like a Windows left-edge snap.
  const halfScreen = {
    x: work.x,
    y: work.y,
    width: Math.max(960, Math.floor(work.width / 2)),
    height: work.height
  };

  const win = new BrowserWindow({
    ...halfScreen,
    minWidth: 960,
    minHeight: 700,
    show: true,
    backgroundColor: "#090d17"
  });
  win.loadURL("data:text/html,<body style='background:%23090d17'></body>");

  const saves = [];
  bindWindowState(win, (snapshot) => saves.push(snapshot));
  await sleep(1200);

  const windowed = win.getBounds();
  console.log(`[test] windowed bounds        ${fmt(windowed)}`);

  // --- fullscreen round trip from a windowed (snap-shaped) window ---
  const entered = waitForEvent(win, "enter-full-screen");
  win.setFullScreen(true);
  await entered;
  await sleep(900);
  const fullscreenBounds = win.getBounds();
  console.log(`[test] fullscreen bounds      ${fmt(fullscreenBounds)}`);
  assert.ok(
    fullscreenBounds.width > windowed.width,
    `fullscreen should fill the display (got ${fmt(fullscreenBounds)})`
  );

  const left = waitForEvent(win, "leave-full-screen");
  win.setFullScreen(false);
  await left;
  await sleep(1500);
  const afterFullscreen = win.getBounds();
  console.log(`[test] after leave fullscreen ${fmt(afterFullscreen)}`);
  assert.ok(
    sameBounds(afterFullscreen, windowed),
    `leaving fullscreen must restore exact windowed bounds: expected ${fmt(windowed)}, got ${fmt(afterFullscreen)}`
  );

  const fullscreenSave = saves[saves.length - 1];
  assert.ok(
    fullscreenSave && sameBounds(fullscreenSave.bounds, windowed),
    `saved bounds after fullscreen must stay windowed: expected ${fmt(windowed)}, got ${fmt(fullscreenSave && fullscreenSave.bounds)}`
  );
  assert.strictEqual(fullscreenSave.maximized, false, "window must not be flagged maximized after fullscreen exit");

  // --- maximize must never persist the maximized rect as the windowed size ---
  saves.length = 0;
  const maximized = waitForEvent(win, "maximize");
  win.maximize();
  await maximized;
  await sleep(1200);
  const maximizedBounds = win.getBounds();
  console.log(`[test] maximized bounds       ${fmt(maximizedBounds)}`);
  const maximizedSave = saves[saves.length - 1];
  console.log(`[test] saved while maximized  ${fmt(maximizedSave && maximizedSave.bounds)} maximized=${maximizedSave && maximizedSave.maximized}`);
  assert.ok(
    maximizedSave && sameBounds(maximizedSave.bounds, windowed),
    `maximizing must persist windowed bounds: expected ${fmt(windowed)}, got ${fmt(maximizedSave && maximizedSave.bounds)}`
  );
  assert.strictEqual(maximizedSave.maximized, true, "maximized flag must be persisted");

  // --- fullscreen from maximized returns to maximized, windowed bounds intact ---
  const entered2 = waitForEvent(win, "enter-full-screen");
  win.setFullScreen(true);
  await entered2;
  await sleep(900);
  const left2 = waitForEvent(win, "leave-full-screen");
  win.setFullScreen(false);
  await left2;
  await sleep(1500);
  assert.strictEqual(win.isMaximized(), true, "fullscreen exit from maximized must stay maximized");

  const unmaximized = waitForEvent(win, "unmaximize");
  win.unmaximize();
  await unmaximized;
  await sleep(800);
  const afterUnmaximize = win.getBounds();
  console.log(`[test] after unmaximize       ${fmt(afterUnmaximize)}`);
  assert.ok(
    sameBounds(afterUnmaximize, windowed),
    `un-maximizing must return to windowed bounds: expected ${fmt(windowed)}, got ${fmt(afterUnmaximize)}`
  );

  console.log("window state electron tests passed");
}

app.whenReady().then(async () => {
  try {
    await run();
    app.exit(0);
  } catch (error) {
    console.error(error && error.stack ? error.stack : error);
    app.exit(1);
  }
});
