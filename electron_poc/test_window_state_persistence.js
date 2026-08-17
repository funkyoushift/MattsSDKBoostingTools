const assert = require("assert");
const { EventEmitter } = require("events");
const { bindWindowState } = require("./window_state_tracker");

class FakeWindow extends EventEmitter {
  constructor(bounds, maximized = false) {
    super();
    this.bounds = { ...bounds };
    this.normalBounds = { ...bounds };
    this.fullscreen = false;
    this.maximized = maximized;
  }
  getBounds() { return { ...this.bounds }; }
  getNormalBounds() { return { ...this.normalBounds }; }
  isFullScreen() { return this.fullscreen; }
  isMaximized() { return this.maximized; }
  setBounds(bounds) { this.bounds = { ...bounds }; }
  maximize() { this.maximized = true; }
  unmaximize() { this.maximized = false; }
}

async function run() {
  const halfScreen = { x: 0, y: 0, width: 960, height: 1040 };
  const win = new FakeWindow(halfScreen);
  const saves = [];
  bindWindowState(win, (snapshot) => saves.push(snapshot), { saveDelay: 0, restoreDelay: 0 });
  win.fullscreen = true;
  win.bounds = { x: 0, y: 0, width: 1920, height: 1080 };
  win.emit("enter-full-screen");
  win.fullscreen = false;
  win.emit("leave-full-screen");
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.deepStrictEqual(win.getBounds(), halfScreen, "fullscreen exit must restore half-screen bounds");
  assert.strictEqual(win.isMaximized(), false, "normal fullscreen restore must not maximize");
  assert.deepStrictEqual(saves[0], { bounds: halfScreen, maximized: false });

  const maxWin = new FakeWindow({ x: 80, y: 60, width: 1280, height: 820 }, true);
  bindWindowState(maxWin, () => {}, { saveDelay: 0, restoreDelay: 0 });
  maxWin.fullscreen = true;
  maxWin.emit("enter-full-screen");
  maxWin.fullscreen = false;
  maxWin.maximized = false;
  maxWin.emit("leave-full-screen");
  assert.strictEqual(maxWin.isMaximized(), true, "fullscreen exit must preserve prior maximized state");

  console.log("window state persistence tests passed");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
