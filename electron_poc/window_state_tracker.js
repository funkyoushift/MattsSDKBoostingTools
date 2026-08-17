"use strict";

/**
 * Track restorable window bounds without letting fullscreen resize events
 * overwrite them. Dependency injection keeps this behavior testable without a
 * real display while main.js remains responsible for writing the state file.
 */
function bindWindowState(win, saveState, options = {}) {
  const saveDelay = Number.isFinite(options.saveDelay) ? options.saveDelay : 500;
  const restoreDelay = Number.isFinite(options.restoreDelay) ? options.restoreDelay : 100;
  let saveTimer = null;
  let normalBounds = typeof win.getNormalBounds === "function" ? win.getNormalBounds() : win.getBounds();
  let preFullscreenBounds = null;
  let preFullscreenMaximized = false;

  const save = (snapshot) => {
    if (typeof saveState === "function") saveState(snapshot || {});
  };
  const scheduleSave = () => {
    if (win.isFullScreen()) return;
    if (!win.isMaximized()) {
      normalBounds = typeof win.getNormalBounds === "function" ? win.getNormalBounds() : win.getBounds();
    }
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => save(), saveDelay);
  };

  win.on("resize", scheduleSave);
  win.on("move", scheduleSave);
  win.on("maximize", scheduleSave);
  win.on("unmaximize", scheduleSave);
  win.on("enter-full-screen", () => {
    if (saveTimer) clearTimeout(saveTimer);
    preFullscreenBounds = { ...normalBounds };
    preFullscreenMaximized = win.isMaximized();
    save({
      bounds: preFullscreenBounds,
      maximized: preFullscreenMaximized
    });
  });
  win.on("leave-full-screen", () => {
    if (!preFullscreenBounds) {
      scheduleSave();
      return;
    }
    const restoreBounds = { ...preFullscreenBounds };
    const restoreMaximized = preFullscreenMaximized;
    preFullscreenBounds = null;
    preFullscreenMaximized = false;
    if (restoreMaximized) {
      win.maximize();
    } else {
      if (win.isMaximized()) win.unmaximize();
      win.setBounds(restoreBounds);
      normalBounds = restoreBounds;
    }
    setTimeout(scheduleSave, restoreDelay);
  });
  win.on("close", () => {
    save(preFullscreenBounds ? {
      bounds: preFullscreenBounds,
      maximized: preFullscreenMaximized
    } : {});
  });
}

module.exports = { bindWindowState };
