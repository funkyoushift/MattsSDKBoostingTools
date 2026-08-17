const assert = require("assert");
const { EventEmitter } = require("events");
const { bindWindowState } = require("./window_state_tracker");

const DISPLAY = { x: 0, y: 0, width: 2560, height: 1440 };
const MAXIMIZED_RECT = { x: -8, y: -8, width: 2576, height: 1408 };
const FULLSCREEN_RECT = { x: 0, y: 0, width: 2560, height: 1440 };
// Real numbers measured on Windows: left-half Aero snap of a 2560x1440 display.
const HALF_SCREEN = { x: -7, y: 0, width: 1294, height: 1399 };

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Mimics the Windows/Electron behavior that broke real restores:
 * - fullscreen and maximize events fire before the state flag flips,
 * - getBounds() reports the screen-filling rect while fullscreen/maximized,
 * - the OS applies its own restore a few milliseconds after
 *   `leave-full-screen`, and that restore can land on the wrong rect when the
 *   window was Aero-snapped.
 */
class FakeWindow extends EventEmitter {
  constructor(bounds) {
    super();
    this.bounds = { ...bounds };
    this.normal = { ...bounds };
    this.fullscreen = false;
    this.maximized = false;
    this.minimized = false;
    this.destroyed = false;
  }
  getBounds() { return { ...this.bounds }; }
  getNormalBounds() { return this.fullscreen || this.maximized ? { ...this.normal } : { ...this.bounds }; }
  isFullScreen() { return this.fullscreen; }
  isMaximized() { return this.maximized; }
  isMinimized() { return this.minimized; }
  isDestroyed() { return this.destroyed; }
  setBounds(bounds) {
    this.bounds = { ...bounds };
    if (!this.fullscreen && !this.maximized) this.normal = { ...bounds };
    this.emit("resize");
    this.emit("move");
  }
  maximize() {
    if (this.maximized) return;
    if (!this.fullscreen) this.normal = { ...this.bounds };
    this.maximized = true;
    this.bounds = { ...MAXIMIZED_RECT };
    this.emit("resize");
    this.emit("move");
    this.emit("maximize");
  }
  unmaximize() {
    if (!this.maximized) return;
    this.maximized = false;
    this.bounds = { ...this.normal };
    this.emit("resize");
    this.emit("move");
    this.emit("unmaximize");
  }
  async enterFullScreen() {
    this.normal = this.maximized ? { ...this.normal } : { ...this.bounds };
    this.emit("enter-full-screen"); // Windows: still fullscreen=false here
    await sleep(2);
    this.fullscreen = true;
    this.wasMaximized = this.maximized;
    this.maximized = false;
    this.bounds = { ...FULLSCREEN_RECT };
    this.emit("resize");
    this.emit("move");
  }
  async leaveFullScreen(osRestoreBounds) {
    this.emit("leave-full-screen"); // Windows: still fullscreen=true, bounds=fullscreen rect
    await sleep(4);
    this.fullscreen = false;
    if (this.wasMaximized) {
      this.maximized = true;
      this.bounds = { ...MAXIMIZED_RECT };
    } else {
      this.bounds = { ...(osRestoreBounds || this.normal) };
      this.normal = { ...this.bounds };
    }
    this.emit("resize");
    this.emit("move");
  }
}

// Mirrors how main.js resolves a snapshot into the persisted state file. The
// tracker must always hand over explicit bounds: main.js's getBounds() fallback
// reports the screen-filling rect while maximized or fullscreen.
function persistedFrom(win, snapshot) {
  assert.ok(
    snapshot && snapshot.bounds && Number.isFinite(snapshot.bounds.width),
    "tracker must emit explicit windowed bounds with every save"
  );
  assert.strictEqual(
    typeof snapshot.maximized,
    "boolean",
    "tracker must emit an explicit maximized flag with every save"
  );
  return { bounds: { ...snapshot.bounds }, maximized: snapshot.maximized };
}

async function fullscreenRestoresSnappedBounds() {
  const win = new FakeWindow(HALF_SCREEN);
  const saves = [];
  bindWindowState(win, (snapshot) => saves.push(persistedFrom(win, snapshot)), {
    saveDelay: 1,
    restoreDelay: 10
  });

  await win.enterFullScreen();
  await sleep(20);
  assert.deepStrictEqual(
    saves[0],
    { bounds: HALF_SCREEN, maximized: false },
    "entering fullscreen must persist the pre-fullscreen half-screen bounds"
  );

  // The OS drops the snap and restores a stale rect; the tracker must win.
  await win.leaveFullScreen({ x: 640, y: 286, width: 1280, height: 820 });
  await sleep(120);
  assert.deepStrictEqual(
    win.getBounds(),
    HALF_SCREEN,
    "leaving fullscreen must restore the exact pre-fullscreen half-screen bounds"
  );
  assert.strictEqual(win.isMaximized(), false, "normal fullscreen restore must not maximize");
  assert.deepStrictEqual(
    saves[saves.length - 1],
    { bounds: HALF_SCREEN, maximized: false },
    "post-fullscreen save must keep the half-screen bounds"
  );
}

async function maximizeKeepsWindowedBounds() {
  const win = new FakeWindow(HALF_SCREEN);
  const saves = [];
  bindWindowState(win, (snapshot) => saves.push(persistedFrom(win, snapshot)), {
    saveDelay: 1,
    restoreDelay: 10
  });

  win.maximize();
  await sleep(20);
  const saved = saves[saves.length - 1];
  assert.deepStrictEqual(
    saved,
    { bounds: HALF_SCREEN, maximized: true },
    "maximizing must persist the windowed bounds, not the maximized rect"
  );

  // Restart simulation: relaunch from the persisted state and un-maximize.
  const relaunched = new FakeWindow(saved.bounds);
  bindWindowState(relaunched, () => {}, { saveDelay: 1, restoreDelay: 10 });
  relaunched.maximize();
  relaunched.unmaximize();
  assert.deepStrictEqual(
    relaunched.getBounds(),
    HALF_SCREEN,
    "leaving maximized after a restart must return to the saved half-screen bounds"
  );
}

async function maximizedFullscreenRoundTrip() {
  const win = new FakeWindow(HALF_SCREEN);
  const saves = [];
  bindWindowState(win, (snapshot) => saves.push(persistedFrom(win, snapshot)), {
    saveDelay: 1,
    restoreDelay: 10
  });

  win.maximize();
  await win.enterFullScreen();
  await sleep(20);
  assert.deepStrictEqual(
    saves[saves.length - 1],
    { bounds: HALF_SCREEN, maximized: true },
    "fullscreen from maximized must remember both the maximized flag and windowed bounds"
  );

  await win.leaveFullScreen();
  await sleep(120);
  assert.strictEqual(win.isMaximized(), true, "fullscreen exit must preserve prior maximized state");
  win.unmaximize();
  assert.deepStrictEqual(
    win.getBounds(),
    HALF_SCREEN,
    "un-maximizing after a fullscreen round trip must return to the windowed bounds"
  );
}

async function resizeDuringFullscreenDoesNotClobber() {
  const win = new FakeWindow(HALF_SCREEN);
  const saves = [];
  bindWindowState(win, (snapshot) => saves.push(persistedFrom(win, snapshot)), {
    saveDelay: 1,
    restoreDelay: 10
  });

  await win.enterFullScreen();
  win.emit("resize");
  win.emit("move");
  await sleep(20);
  for (const entry of saves) {
    assert.deepStrictEqual(
      entry.bounds,
      HALF_SCREEN,
      "resize events while fullscreen must never persist the fullscreen rect"
    );
  }

  win.emit("close");
  assert.deepStrictEqual(
    saves[saves.length - 1],
    { bounds: HALF_SCREEN, maximized: false },
    "closing while fullscreen must persist the pre-fullscreen bounds"
  );
}

const TESTS = {
  fullscreenRestoresSnappedBounds,
  maximizeKeepsWindowedBounds,
  maximizedFullscreenRoundTrip,
  resizeDuringFullscreenDoesNotClobber
};

async function run() {
  const only = process.argv[2];
  for (const [name, test] of Object.entries(TESTS)) {
    if (only && name !== only) continue;
    await test();
  }
  console.log("window state persistence tests passed");
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
