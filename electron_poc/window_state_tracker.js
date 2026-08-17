"use strict";

/**
 * Track restorable window bounds so fullscreen and maximize never overwrite the
 * windowed geometry the user actually chose (including Windows Aero-Snap
 * halves/quadrants, which are plain windows with snapped bounds).
 *
 * Windows event ordering notes that shape this logic:
 * - `enter-full-screen` fires while `isFullScreen()` is still false and
 *   `getBounds()` still reports the pre-fullscreen rect.
 * - `leave-full-screen` fires while `isFullScreen()` is still true and
 *   `getBounds()` still reports the fullscreen rect; the OS restore lands a few
 *   milliseconds later, so the restore has to be re-asserted after the event.
 *
 * Dependency injection keeps this behavior testable without a real display
 * while main.js remains responsible for writing the state file.
 */
function bindWindowState(win, saveState, options = {}) {
  const saveDelay = Number.isFinite(options.saveDelay) ? options.saveDelay : 500;
  const restoreDelay = Number.isFinite(options.restoreDelay) ? options.restoreDelay : 120;
  let saveTimer = null;
  let restoreTimers = [];
  let preFullscreen = null;

  const isDestroyed = () => typeof win.isDestroyed === "function" && win.isDestroyed();
  const isMinimized = () => (typeof win.isMinimized === "function" ? win.isMinimized() : false);
  const readWindowedBounds = () =>
    typeof win.getNormalBounds === "function" ? win.getNormalBounds() : win.getBounds();
  const boundsEqual = (a, b) =>
    Boolean(a) && Boolean(b) && a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;

  let normalBounds = { ...readWindowedBounds() };

  const captureNormalBounds = () => {
    if (isDestroyed() || win.isFullScreen() || win.isMaximized() || isMinimized()) return;
    const next = readWindowedBounds();
    if (next && next.width > 0 && next.height > 0) normalBounds = { ...next };
  };

  const snapshot = () => {
    if (preFullscreen) {
      return { bounds: { ...preFullscreen.bounds }, maximized: preFullscreen.maximized };
    }
    return { bounds: { ...normalBounds }, maximized: Boolean(win.isMaximized()) };
  };

  const save = () => {
    if (saveTimer) {
      clearTimeout(saveTimer);
      saveTimer = null;
    }
    if (isDestroyed()) return;
    if (typeof saveState === "function") saveState(snapshot());
  };

  const scheduleSave = () => {
    captureNormalBounds();
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(save, saveDelay);
  };

  const clearRestoreTimers = () => {
    for (const timer of restoreTimers) clearTimeout(timer);
    restoreTimers = [];
  };

  win.on("resize", scheduleSave);
  win.on("move", scheduleSave);
  win.on("maximize", scheduleSave);
  win.on("unmaximize", scheduleSave);

  win.on("enter-full-screen", () => {
    clearRestoreTimers();
    if (saveTimer) clearTimeout(saveTimer);
    preFullscreen = { bounds: { ...normalBounds }, maximized: Boolean(win.isMaximized()) };
    save();
  });

  win.on("leave-full-screen", () => {
    clearRestoreTimers();
    const target = preFullscreen;
    preFullscreen = null;
    if (!target) {
      scheduleSave();
      return;
    }
    normalBounds = { ...target.bounds };

    const applyRestore = () => {
      if (isDestroyed() || win.isFullScreen()) return false;
      if (target.maximized) {
        if (!win.isMaximized()) win.maximize();
        return true;
      }
      if (win.isMaximized()) win.unmaximize();
      if (!boundsEqual(win.getBounds(), target.bounds)) win.setBounds({ ...target.bounds });
      return true;
    };

    // The OS finishes its own restore after this event, so re-assert until the
    // window actually sits on the pre-fullscreen rect.
    applyRestore();
    for (const delay of [restoreDelay, restoreDelay * 3, restoreDelay * 6]) {
      restoreTimers.push(setTimeout(applyRestore, delay));
    }
    restoreTimers.push(setTimeout(scheduleSave, restoreDelay * 6 + 1));
  });

  win.on("close", () => {
    clearRestoreTimers();
    save();
  });
}

module.exports = { bindWindowState };
