(function () {
  const LOCAL_STEAM_KEY = "lastSteamEpicId";
  const PARENT_TIMEOUT_MS = 120000;
  let cachedPrefs = null;
  let requestSeq = 0;

  function inMsbtFrame() {
    try {
      return Boolean(window.parent && window.parent !== window && window.IS_ELECTRON_APP);
    } catch (_err) {
      return false;
    }
  }

  function requestParent(type, payload) {
    return new Promise(function (resolve, reject) {
      if (!inMsbtFrame()) {
        reject(new Error("Matt Editor is not inside the desktop app."));
        return;
      }
      const id = "msbt-editor-" + String(Date.now()) + "-" + String(++requestSeq);
      const timer = setTimeout(function () {
        window.removeEventListener("message", onMessage);
        reject(new Error("Desktop app did not answer in time."));
      }, PARENT_TIMEOUT_MS);
      function onMessage(event) {
        const data = event && event.data;
        if (!data || data.msbtEditorReply !== id) return;
        window.removeEventListener("message", onMessage);
        clearTimeout(timer);
        if (data.ok) resolve(data.result);
        else if (data.result && data.result.canceled) resolve(data.result);
        else reject(new Error(data.message || "Desktop app request failed."));
      }
      window.addEventListener("message", onMessage);
      window.parent.postMessage({ msbtEditorRequest: type, id: id, payload: payload || {} }, "*");
    });
  }

  function fileFromBase64(name, base64) {
    const binary = atob(String(base64 || ""));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return new File([bytes], name || "save.sav");
  }

  function localSteamId() {
    try {
      return String(localStorage.getItem(LOCAL_STEAM_KEY) || "").trim();
    } catch (_err) {
      return "";
    }
  }

  function writeLocalSteamId(steamId) {
    const value = String(steamId || "").trim();
    if (!value) return;
    try {
      localStorage.setItem(LOCAL_STEAM_KEY, value);
    } catch (_err) {
      // ignore quota / private mode
    }
  }

  function looksLikeUserId(value) {
    const id = String(value || "").trim().replace(/\s+/g, "");
    if (/^7656119\d{10}$/.test(id)) return id;
    if (/^\d{17}$/.test(id)) return id;
    if (/^[0-9a-f]{32}$/i.test(id)) return id;
    return "";
  }

  function steamIdFromSavePath(filePath) {
    const text = String(filePath || "").trim();
    if (!text) return "";
    const parts = text.replace(/\\/g, "/").split("/").filter(Boolean);
    const saveGamesIdx = parts.findIndex(function (part) { return part.toLowerCase() === "savegames"; });
    if (saveGamesIdx >= 0 && saveGamesIdx + 1 < parts.length) {
      const fromFolder = looksLikeUserId(parts[saveGamesIdx + 1]);
      if (fromFolder) return fromFolder;
    }
    for (let i = 0; i < parts.length; i += 1) {
      if (/^7656119\d{10}$/.test(parts[i])) return parts[i];
    }
    return "";
  }

  function fillSteamIdFields(steamId, force) {
    const value = String(steamId || "").trim();
    if (!value) return;
    ["save-steamid", "profile-steamid"].forEach(function (id) {
      const node = document.getElementById(id);
      if (!node) return;
      if (force || !String(node.value || "").trim()) node.value = value;
    });
  }

  function applyDetectedSteamId(steamId) {
    const value = String(steamId || "").trim();
    if (!value) return "";
    fillSteamIdFields(value, true);
    writeLocalSteamId(value);
    return value;
  }

  function currentSteamId() {
    const saveNode = document.getElementById("save-steamid");
    const profileNode = document.getElementById("profile-steamid");
    return String((saveNode && saveNode.value) || (profileNode && profileNode.value) || "").trim();
  }

  async function loadPrefs() {
    if (inMsbtFrame()) {
      const result = await requestParent("loadPrefs");
      cachedPrefs = result && result.data ? result.data : result || {};
      if (cachedPrefs.steamId) writeLocalSteamId(cachedPrefs.steamId);
      return cachedPrefs;
    }
    cachedPrefs = { steamId: localSteamId() };
    return cachedPrefs;
  }

  async function savePrefs(partial) {
    const patch = partial && typeof partial === "object" ? partial : {};
    if (patch.steamId) writeLocalSteamId(patch.steamId);
    if (!inMsbtFrame()) {
      cachedPrefs = { ...(cachedPrefs || {}), ...patch };
      return cachedPrefs;
    }
    const result = await requestParent("savePrefs", patch);
    cachedPrefs = result && result.data ? result.data : { ...(cachedPrefs || {}), ...patch };
    return cachedPrefs;
  }

  function setPathLabel(kind, filePath) {
    const id = kind === "profile" ? "profile-remembered-path" : "save-remembered-path";
    const node = document.getElementById(id);
    if (!node) return;
    const text = String(filePath || "").trim();
    node.textContent = text ? "Remembered: " + text : "No remembered file yet.";
  }

  async function applyNativeFile(kind, payload, autoDecrypt) {
    if (!payload || !payload.ok || !payload.base64) return payload;
    const file = fileFromBase64(payload.name, payload.base64);
    if (!window.saveEditorState) window.saveEditorState = {};
    const detectedSteamId = applyDetectedSteamId(
      payload.steamId || steamIdFromSavePath(payload.path)
    );
    if (detectedSteamId) void savePrefs({ steamId: detectedSteamId });
    const reopenBtn = document.getElementById(kind === "profile" ? "profile-reopen-last-btn" : "save-reopen-last-btn");
    if (reopenBtn) reopenBtn.disabled = !payload.path;
    if (kind === "profile") {
      window.saveEditorState.pendingProfileFile = file;
      window.saveEditorState.originalProfilePath = payload.path;
      setPathLabel("profile", payload.path);
      const nameText = document.getElementById("profile-file-name-text");
      const selected = document.getElementById("profile-file-selected-name");
      if (nameText) nameText.textContent = payload.name || payload.path;
      if (selected) selected.style.display = "block";
      if (autoDecrypt && typeof window.decryptProfileFile === "function") {
        await window.decryptProfileFile();
      }
    } else {
      window.saveEditorState.pendingNativeFile = file;
      window.saveEditorState.originalFilePath = payload.path;
      window.saveEditorState.originalFileName = payload.name || file.name;
      setPathLabel("save", payload.path);
      const nameText = document.getElementById("save-file-name-text");
      const selected = document.getElementById("save-file-selected-name");
      if (nameText) nameText.textContent = payload.name || payload.path;
      if (selected) selected.style.display = "block";
      if (autoDecrypt && typeof window.decryptSaveFile === "function") {
        await window.decryptSaveFile();
      }
    }
    return payload;
  }

  async function openFile(kind, autoDecrypt) {
    const payload = await requestParent("openFile", { kind: kind || "save" });
    if (!payload || payload.canceled || !payload.ok) return payload;
    return applyNativeFile(kind || "save", payload, autoDecrypt !== false);
  }

  async function reopenFile(kind, autoDecrypt) {
    const payload = await requestParent("reopenFile", { kind: kind || "save" });
    return applyNativeFile(kind || "save", payload, autoDecrypt !== false);
  }

  async function blobToBase64(blob) {
    const buffer = await blob.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
  }

  async function writeSavBlob(blob, options) {
    const opts = options && typeof options === "object" ? options : {};
    const base64 = await blobToBase64(blob);
    const result = await requestParent("saveFile", {
      base64: base64,
      suggestedName: opts.suggestedName || "save_encrypted.sav",
      overwritePath: opts.overwritePath || "",
      overwrite: Boolean(opts.overwrite)
    });
    if (result && result.path && window.saveEditorState) {
      window.saveEditorState.originalFilePath = result.path;
      window.saveEditorState.originalFileName = result.name || window.saveEditorState.originalFileName;
      setPathLabel("save", result.path);
    }
    return result;
  }

  function wireSteamIdPersistence() {
    ["save-steamid", "profile-steamid"].forEach(function (id) {
      const node = document.getElementById(id);
      if (!node || node.dataset.msbtPrefsWired === "true") return;
      node.dataset.msbtPrefsWired = "true";
      node.addEventListener("change", function () {
        const steamId = String(node.value || "").trim();
        if (!steamId) return;
        void savePrefs({ steamId: steamId });
      });
      node.addEventListener("blur", function () {
        const steamId = String(node.value || "").trim();
        if (!steamId) return;
        void savePrefs({ steamId: steamId });
      });
    });
  }

  function interceptFileInput(inputId, kind) {
    const input = document.getElementById(inputId);
    if (!input || !inMsbtFrame() || input.dataset.msbtPrefsWired === "true") return;
    input.dataset.msbtPrefsWired = "true";
    input.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      void openFile(kind, true).catch(function (error) {
        const statusId = kind === "profile" ? "profile-decrypt-status" : "save-decrypt-status";
        if (typeof window.showSaveStatus === "function") {
          window.showSaveStatus(statusId, "❌ " + (error && error.message ? error.message : error), false);
        }
      });
    }, true);
  }

  function wireRememberedButtons() {
    const saveReopen = document.getElementById("save-reopen-last-btn");
    if (saveReopen && saveReopen.dataset.msbtPrefsWired !== "true") {
      saveReopen.dataset.msbtPrefsWired = "true";
      saveReopen.addEventListener("click", function () {
        void reopenFile("save", true).catch(function (error) {
          if (typeof window.showSaveStatus === "function") {
            window.showSaveStatus("save-decrypt-status", "❌ " + (error && error.message ? error.message : error), false);
          }
        });
      });
    }
    const profileReopen = document.getElementById("profile-reopen-last-btn");
    if (profileReopen && profileReopen.dataset.msbtPrefsWired !== "true") {
      profileReopen.dataset.msbtPrefsWired = "true";
      profileReopen.addEventListener("click", function () {
        void reopenFile("profile", true).catch(function (error) {
          if (typeof window.showSaveStatus === "function") {
            window.showSaveStatus("profile-decrypt-status", "❌ " + (error && error.message ? error.message : error), false);
          }
        });
      });
    }
  }

  async function restoreOnLoad() {
    let prefs = { steamId: localSteamId() };
    try {
      prefs = await loadPrefs();
    } catch (_err) {
      prefs = { steamId: localSteamId() };
    }
    fillSteamIdFields(prefs.steamId || localSteamId());
    setPathLabel("save", prefs.lastSaveFile);
    setPathLabel("profile", prefs.lastProfileFile);
    const saveReopen = document.getElementById("save-reopen-last-btn");
    if (saveReopen) saveReopen.disabled = !prefs.lastSaveFile;
    const profileReopen = document.getElementById("profile-reopen-last-btn");
    if (profileReopen) profileReopen.disabled = !prefs.lastProfileFile;
    wireSteamIdPersistence();
    interceptFileInput("save-file-input", "save");
    interceptFileInput("profile-file-input", "profile");
    wireRememberedButtons();
  }

  window.MsbtEditorPrefs = {
    inMsbtFrame: inMsbtFrame,
    loadPrefs: loadPrefs,
    savePrefs: savePrefs,
    currentSteamId: currentSteamId,
    steamIdFromSavePath: steamIdFromSavePath,
    applyDetectedSteamId: applyDetectedSteamId,
    openFile: openFile,
    reopenFile: reopenFile,
    writeSavBlob: writeSavBlob,
    restoreOnLoad: restoreOnLoad
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      void restoreOnLoad();
    });
  } else {
    void restoreOnLoad();
  }
})();
