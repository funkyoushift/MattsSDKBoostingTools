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
      ["loot_mode", byId("afkLootMode").value],
      ["guaranteed_codes", byId("afkGuaranteedCodes").value],
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
    byId("afkLootMode").value = config.loot_mode === "random70" ? "random70" : "all";
    if (typeof config.codes === "string") byId("afkCodes").value = config.codes;
    else if (Array.isArray(config.serials)) byId("afkCodes").value = config.serials.join("\n");
    byId("afkGuaranteedCodes").value = typeof config.guaranteed_codes === "string"
      ? config.guaranteed_codes : (config.guaranteed_serials || []).join("\n");
  }
  try { const saved = JSON.parse(localStorage.getItem(storageKey) || "null"); if (saved) apply(saved); } catch (_) { /* defaults */ }
  panel.addEventListener("change", save);
  byId("afkCodes").addEventListener("input", save);
  byId("afkGuaranteedCodes").addEventListener("input", save);

  function render(data) {
    const afk = data && data.afk_lobby;
    lastStatus = afk || null;
    running = Boolean(afk && afk.enabled);
    if (running && !loaded) apply(afk.config || {});
    loaded = Boolean(afk);
    byId("afkStart").disabled = busy || running || !afk;
    byId("afkStop").disabled = busy || !running;
    panel.querySelectorAll("input,textarea,select,#afkAddBookmarks,#afkAddGuaranteedBookmarks,#afkLoadBookmarks").forEach((node) => { node.disabled = running || busy; });
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
      if (action === "afk_lobby_start" && payload.loot && payload.guaranteed_codes?.trim()
          && !lastStatus?.guaranteed_loot_supported) {
        throw new Error("Install the updated SDK mod and restart Borderlands 4 before using guaranteed items.");
      }
      if (action === "afk_lobby_start" && payload.loot && payload.loot_mode === "random70"
          && !lastStatus?.loot_modes?.includes("random70")) {
        throw new Error("Install the updated SDK mod and restart Borderlands 4 before using random 70 loot.");
      }
      if (action === "afk_lobby_start" && payload.loot && payload.loot_mode === "all"
          && !lastStatus?.bulk_loot_password_required) {
        throw new Error("Install the updated SDK mod and restart Borderlands 4 before using password-protected loot delivery.");
      }
      save();
      let response = await bridgeAction(action, payload, 30000);
      let result = response && response.data !== undefined ? response.data : response;
      if (result?.password_required && result.password_kind === "bulk_loot") {
        const password = await requestBackpackPassword("bulk_loot");
        if (password === null) throw new Error("AFK start cancelled.");
        response = await bridgeAction(action, { ...payload, bulk_loot_password: password }, 30000);
        result = response && response.data !== undefined ? response.data : response;
      }
      if (!result || result.ok === false) throw new Error(result && result.message || "AFK command failed.");
      if (result.afk_lobby) render({ afk_lobby: { ...lastStatus, ...result.afk_lobby } });
      await bridgeStatus({ quiet: true });
    } catch (error) {
      byId("afkStatus").textContent = error.message;
    } finally {
      busy = false;
      byId("afkStart").disabled = running || !lastStatus;
      byId("afkStop").disabled = !running;
      panel.querySelectorAll("input,textarea,select,#afkAddBookmarks,#afkAddGuaranteedBookmarks,#afkLoadBookmarks").forEach((node) => { node.disabled = running; });
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
  function appendLoot(codes, guaranteed = false) {
    if (running || busy) return { ok: false, message: "Stop AFK Lobby before changing its loot list." };
    if (!codes.length) return { ok: false, message: "Select an item first." };
    const target = byId(guaranteed ? "afkGuaranteedCodes" : "afkCodes");
    target.value = [target.value.trim(), ...codes].filter(Boolean).join("\n");
    panel.querySelector('[data-afk-boost="loot"]').checked = true;
    save();
    return { ok: true, message: `Added ${codes.length} item code(s) to AFK ${guaranteed ? "guaranteed items" : "loot pool"}. Review them in Boosting → AFK Lobby.` };
  }
  function addCatalogLoot(entries, guaranteed = false) {
    const rows = bl4ValidSerialEntries(entries);
    if (rows.length !== entries.length) {
      setBl4Status("One or more selected items have invalid codes. Nothing added to AFK.", "warning");
      return;
    }
    const result = appendLoot(rows.map((row) => row.serial), guaranteed);
    setBl4Status(result.message, result.ok ? "ok" : "warning");
  }
  byId("bl4AddToAfkBtn").addEventListener("click", () => addCatalogLoot(bl4SelectedEntries()));
  byId("bl4AddGuaranteedAfkBtn").addEventListener("click", () => addCatalogLoot(bl4SelectedEntries(), true));
  byId("bl4AddThisToAfkBtn").addEventListener("click", () => {
    const row = activeBl4Entry();
    addCatalogLoot(row ? [row] : []);
  });
  byId("afkAddBookmarks").addEventListener("click", () => {
    const codes = [...byId("afkBookmarks").selectedOptions].map((option) => option.value);
    const result = appendLoot(codes);
    byId("afkBookmarkNote").textContent = result.message;
  });
  byId("afkAddGuaranteedBookmarks").addEventListener("click", () => {
    const codes = [...byId("afkBookmarks").selectedOptions].map((option) => option.value);
    byId("afkBookmarkNote").textContent = appendLoot(codes, true).message;
  });
  bookmarks().catch(() => {});
  render(null);
})();
