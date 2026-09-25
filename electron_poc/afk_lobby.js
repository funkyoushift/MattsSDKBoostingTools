/* AFK lobby controls; boost execution stays in the SDK game tick. */
(() => {
  const byId = (id) => document.getElementById(id);
  const panel = byId("afkLobbyPanel");
  if (!panel) return;
  const options = [...panel.querySelectorAll("[data-afk-boost]")];
  const storageKey = "msbt.afk-lobby.v1";
  let running = false;
  let busy = false;
  let lastStatus = null;
  let loaded = false;

  function selection() {
    return Object.fromEntries([
      ...options.map((node) => [node.dataset.afkBoost, node.checked]),
      ["auto_accept", byId("afkAutoAccept").checked],
      ["auto_kick", byId("afkAutoKick").checked],
      ["codes", byId("afkCodes").value]
    ]);
  }
  function save() {
    try { localStorage.setItem(storageKey, JSON.stringify(selection())); } catch (_) { /* session still usable */ }
  }
  function apply(config) {
    options.forEach((node) => { node.checked = config[node.dataset.afkBoost] === true; });
    byId("afkAutoAccept").checked = config.auto_accept !== false;
    byId("afkAutoKick").checked = config.auto_kick === true;
    if (typeof config.codes === "string") byId("afkCodes").value = config.codes;
    else if (Array.isArray(config.serials)) byId("afkCodes").value = config.serials.join("\n");
  }
  try { const saved = JSON.parse(localStorage.getItem(storageKey) || "null"); if (saved) apply(saved); } catch (_) { /* defaults */ }
  panel.addEventListener("change", save);
  byId("afkCodes").addEventListener("input", save);

  function render(data) {
    const afk = data && data.afk_lobby;
    lastStatus = afk || null;
    running = Boolean(afk && afk.enabled);
    if (running && !loaded) apply(afk.config || {});
    loaded = Boolean(afk);
    byId("afkStart").disabled = busy || running || !afk;
    byId("afkStop").disabled = busy || !running;
    panel.querySelectorAll("input,textarea,select,#afkAddBookmarks,#afkLoadBookmarks").forEach((node) => { node.disabled = running || busy; });
    byId("afkStatus").textContent = afk ? afk.message : "AFK lobby is not connected. Install the bundled game files and restart Borderlands 4.";
    byId("afkShiftStatus").textContent = afk && afk.shift_connected
      ? `SHiFT menu connected · Auto-accepter ${afk.shift_running ? "running" : "stopped"}`
      : "SHiFT menu not connected. Open the SHiFT menu after installing the bundled game files.";
    byId("afkQueue").textContent = afk && afk.queued && afk.queued.length ? `Waiting: ${afk.queued.join(", ")}` : "No guests waiting.";
    byId("afkLog").textContent = afk && afk.history && afk.history.length
      ? afk.history.map((entry) => `${entry.name}: ${entry.message}\n${(entry.results || []).map((r) => `  ${r.step}: ${r.ok ? "OK" : "FAILED"} — ${r.message}`).join("\n")}`).join("\n\n")
      : "Each join gets one full run. Rejoining gets another run.";
  }
  window.msbtAfkRender = render;

  async function run(action, payload = {}) {
    if (busy) return;
    busy = true;
    render({ afk_lobby: lastStatus });
    try {
      save();
      const response = await bridgeAction(action, payload, 30000);
      const result = response && response.data !== undefined ? response.data : response;
      if (!result || result.ok === false) throw new Error(result && result.message || "AFK command failed.");
      if (result.afk_lobby) render({ afk_lobby: { ...lastStatus, ...result.afk_lobby } });
      await bridgeStatus({ quiet: true });
    } catch (error) {
      byId("afkStatus").textContent = error.message;
    } finally {
      busy = false;
      byId("afkStart").disabled = running || !lastStatus;
      byId("afkStop").disabled = !running;
      panel.querySelectorAll("input,textarea,select,#afkAddBookmarks,#afkLoadBookmarks").forEach((node) => { node.disabled = running; });
    }
  }
  byId("afkStart").addEventListener("click", () => run("afk_lobby_start", selection()));
  byId("afkStop").addEventListener("click", () => run("afk_lobby_stop"));
  byId("afkCloseShift").addEventListener("click", () => run("shift_overlay_control", { mode: "close" }));
  async function bookmarks() {
    const result = await window.msbt.loadSerialBookmarks();
    const rows = result && result.data && result.data.bookmarks || [];
    const select = byId("afkBookmarks");
    select.replaceChildren();
    rows.forEach((row) => {
      const option = document.createElement("option");
      option.value = row.serial;
      option.textContent = `${row.group || "Default"} · ${row.name || "Unnamed item"}`;
      select.appendChild(option);
    });
    byId("afkBookmarkNote").textContent = rows.length ? "Select bookmarks, then Add selected to loot." : "No saved bookmarks yet. You can paste item codes below.";
  }
  byId("afkLoadBookmarks").addEventListener("click", () => bookmarks().catch((error) => { byId("afkBookmarkNote").textContent = error.message; }));
  function appendLoot(codes) {
    if (running || busy) return { ok: false, message: "Stop AFK Lobby before changing its loot list." };
    if (!codes.length) return { ok: false, message: "Select an item first." };
    byId("afkCodes").value = [byId("afkCodes").value.trim(), ...codes].filter(Boolean).join("\n");
    panel.querySelector('[data-afk-boost="loot"]').checked = true;
    save();
    return { ok: true, message: `Added ${codes.length} item code(s) to AFK loot. Review them in Boosting → AFK Lobby.` };
  }
  function addCatalogLoot(entries) {
    const rows = bl4ValidSerialEntries(entries);
    if (rows.length !== entries.length) {
      setBl4Status("One or more selected items have invalid codes. Nothing added to AFK.", "warning");
      return;
    }
    const result = appendLoot(rows.map((row) => row.serial));
    setBl4Status(result.message, result.ok ? "ok" : "warning");
  }
  byId("bl4AddToAfkBtn").addEventListener("click", () => addCatalogLoot(bl4SelectedEntries()));
  byId("bl4AddThisToAfkBtn").addEventListener("click", () => {
    const row = activeBl4Entry();
    addCatalogLoot(row ? [row] : []);
  });
  byId("afkAddBookmarks").addEventListener("click", () => {
    const codes = [...byId("afkBookmarks").selectedOptions].map((option) => option.value);
    const result = appendLoot(codes);
    byId("afkBookmarkNote").textContent = result.message;
  });
  bookmarks().catch(() => {});
  render(null);
})();
