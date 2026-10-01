/* AFK lobby controls; boost execution stays in the SDK game tick. */
(() => {
  const byId = (id) => document.getElementById(id);
  const panel = byId("afkLobbyPanel");
  if (!panel) return;
  const options = [...panel.querySelectorAll("[data-afk-boost]")];
  const amountLimits = {level: 70, spec: 701, cash: 2147483647, eridium: 2147483647, keys: 2147483647};
  const amountLabels = {level: 'Target character level', spec: 'Target specialization level', cash: 'Cash added per join', eridium: 'Eridium added per join', keys: 'Keys added per card (1–5) per join'};
  const amountInputs = {};
  for (const [key, maximum] of Object.entries(amountLimits)) {
    const checkbox = options.find(node => node.dataset.afkBoost === key);
    const label = checkbox.parentElement;
    label.lastChild.textContent = ' ' + amountLabels[key];
    const group = document.createElement('div');
    group.className = 'afk-amount';
    label.replaceWith(group);
    group.append(label);
    const controls = document.createElement('div');
    controls.className = 'afk-amount-controls';
    const slider = document.createElement('input');
    const number = document.createElement('input');
    slider.type = 'range'; number.type = 'number';
    for (const input of [slider, number]) {
      input.min = '1'; input.max = String(maximum); input.step = '1'; input.value = String(maximum);
      input.setAttribute('aria-label', amountLabels[key]);
    }
    slider.addEventListener('input', () => { number.value = slider.value; });
    number.addEventListener('input', () => { slider.value = number.value; });
    controls.append(slider, number);
    group.append(controls);
    amountInputs[key] = {slider, number};
  }
  const storageKey = "msbt.afk-lobby.v1";
  let running = false;
  let busy = false;
  let lastStatus = null;
  let loaded = false;
  let edits = 0;
  let savedAt = 0;

  function selection() {
    return Object.fromEntries([
      ...options.map((node) => [node.dataset.afkBoost, node.checked]),
      ...Object.entries(amountInputs).map(([key, {number}]) => [key + '_amount', Number(number.value)]),
      ["auto_accept", byId("afkAutoAccept").checked],
      ["auto_kick", byId("afkAutoKick").checked],
      ["cleanup_rewards", byId("afkCleanupRewards").checked],
      ["loot_mode", byId("afkLootMode").value],
      ["random_count", Number(byId("afkRandomCount").value)],
      ["serial_override_level", byId("afkItemLevelOverride").checked],
      ["serial_level", Number(byId("afkItemLevel").value)],
      ["guaranteed_codes", byId("afkGuaranteedCodes").value],
      ["codes", byId("afkCodes").value]
    ]);
  }
  function save() {
    edits++;
    const config = selection();
    config.saved_at = savedAt = Math.max(Date.now(), savedAt + 1);
    let fallbackSaved = false;
    try { localStorage.setItem(storageKey, JSON.stringify(config)); fallbackSaved = true; } catch (_) { /* IndexedDB handles larger lists. */ }
    window.msbtAfkConfigStore.save(config).catch(error => {
      if (!fallbackSaved) byId('afkStatus').textContent = `Could not save AFK lists: ${error.message}. Keep this window open and copy your lists before closing.`;
    });
  }
  function apply(config) {
    for (const [key, {slider, number}] of Object.entries(amountInputs)) {
      slider.value = number.value = config[key + '_amount'] ?? amountLimits[key];
    }
    options.forEach((node) => { node.checked = config[node.dataset.afkBoost] === true; });
    byId("afkAutoAccept").checked = config.auto_accept !== false;
    byId("afkAutoKick").checked = config.auto_kick === true;
    byId("afkCleanupRewards").checked = config.cleanup_rewards === true;
    byId("afkLootMode").value = config.loot_mode === "random70" ? "random70" : "all";
    byId("afkRandomCount").value = config.random_count || 70;
    byId("afkItemLevelOverride").checked = config.serial_override_level === true;
    byId("afkItemLevel").value = config.serial_level || 70;
    if (typeof config.codes === "string") byId("afkCodes").value = config.codes;
    else if (Array.isArray(config.serials)) byId("afkCodes").value = config.serials.join("\n");
    byId("afkGuaranteedCodes").value = typeof config.guaranteed_codes === "string"
      ? config.guaranteed_codes : (config.guaranteed_serials || []).join("\n");
  }
  try { const saved = JSON.parse(localStorage.getItem(storageKey) || "null"); if (saved) { savedAt = saved.saved_at || 0; apply(saved); } } catch (_) { /* defaults */ }
  window.msbtAfkConfigStore.load().then(saved => {
    if (saved && (saved.saved_at || 0) >= savedAt && edits === 0 && !running && !busy) { savedAt = saved.saved_at || 0; apply(saved); }
  }).catch(() => { /* Existing localStorage settings remain available. */ });
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
    byId("afkTestHost").disabled = busy || running || !afk?.host_test_supported;
    byId("afkStop").disabled = busy || !running;
    panel.querySelectorAll("input,textarea,select,#afkAddBookmarks,#afkAddGuaranteedBookmarks,#afkLoadBookmarks,#afkAddFolder,#afkAddGuaranteedFolder").forEach((node) => { node.disabled = running || busy; });
    byId("afkStatus").textContent = afk ? afk.message : "AFK lobby is not connected. Install the bundled game files and restart Borderlands 4.";
    byId("afkShiftStatus").textContent = afk && afk.shift_connected
      ? `SHiFT menu connected · Auto-accepter ${afk.shift_running ? "running" : "stopped"}`
      : "SHiFT menu not connected. Open the SHiFT menu after installing the bundled game files.";
    byId("afkQueue").textContent = afk && afk.queued && afk.queued.length ? `Waiting: ${afk.queued.join(", ")}` : "No guests waiting.";
    byId("afkJoinCounts").textContent = afk?.session_joins != null
      ? (window.msbtI18n ? window.msbtI18n.t("counts", {session: afk.session_joins, lifetime: afk.lifetime_joins ?? window.msbtI18n.t("unavailable")}) : `Guest joins: ${afk.session_joins} this session · ${afk.lifetime_joins ?? "unavailable"} lifetime`) + (afk.counter_error ? " · Lifetime count could not be saved: " + afk.counter_error : "")
      : "Join counters require the updated SDK mod.";
    byId("afkLog").textContent = afk && afk.history && afk.history.length
      ? afk.history.map((entry) => `${entry.name}: ${entry.message}\n${entry.report_path ? `Saved report: ${entry.report_path}\n` : ""}${entry.report_error ? `${entry.report_error}\n` : ""}${(entry.results || []).map((r) => `  ${r.step}: ${r.cleanup_skipped ? "SKIPPED" : r.ok ? "OK" : "NEEDS REVIEW"} — ${r.message}`).join("\n")}`).join("\n\n")
      : "Each join gets one full run. Rejoining gets another run.";
  }
  window.msbtAfkRender = render;

  async function run(action, payload = {}) {
    if (busy) return;
    busy = true;
    render({ afk_lobby: lastStatus });
    try {
      if (action === 'afk_lobby_start') {
        for (const [key, maximum] of Object.entries(amountLimits)) {
          const value = payload[key + '_amount'];
          if (!Number.isInteger(value) || value < 1 || value > maximum) throw new Error(`${amountLabels[key]} must be a whole number from 1 to ${maximum.toLocaleString()}.`);
          if (payload[key] && value !== maximum && !lastStatus?.boost_amounts_supported) throw new Error('Install the updated SDK mod and restart Borderlands 4 before using custom AFK boost amounts.');
        }
      }
      if (payload.test_host && !lastStatus?.host_test_supported) {
        throw new Error('Install the updated SDK before testing AFK on yourself.');
      }
      if (action === 'afk_lobby_start' && payload.cleanup_rewards && !lastStatus?.cleanup_rewards_supported) {
        throw new Error('Install the updated SDK before using reward cleanup.');
      }
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
      if(action === "afk_lobby_start" && payload.loot && payload.loot_mode === "random70"
          && payload.random_count !== 70 && !lastStatus?.random_count_supported) {
        throw new Error("Install the updated SDK mod before changing random delivery size.");
      }
      if (action === 'afk_lobby_start' && payload.loot && payload.serial_override_level && !lastStatus?.item_level_override_supported) {
        throw new Error('Install the updated SDK mod and restart Borderlands 4 before overriding AFK item levels.');
      }
      save();
      const send = (data) => window.msbtAfkConfigSend(action, data,
        (name, body) => bridgeAction(name, body, 30000), lastStatus?.config_upload_supported);
      let response = await send(payload);
      let result = response && response.data !== undefined ? response.data : response;
      if (result?.password_required && result.password_kind === "bulk_loot") {
        const password = await requestBackpackPassword(result.password_kind);
        if (password === null) throw new Error("AFK start cancelled.");
        response = await send({ ...payload, bulk_loot_password: password });
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
      byId("afkTestHost").disabled = running || !lastStatus?.host_test_supported;
      byId("afkStop").disabled = !running;
      panel.querySelectorAll("input,textarea,select,#afkAddBookmarks,#afkAddGuaranteedBookmarks,#afkLoadBookmarks,#afkAddFolder,#afkAddGuaranteedFolder").forEach((node) => { node.disabled = running; });
    }
  }
  byId("afkStart").addEventListener("click", () => run("afk_lobby_start", selection()));
  byId("afkTestHost").addEventListener("click", () => run("afk_lobby_start", {...selection(), test_host: true}));
  byId("afkStop").addEventListener("click", () => run("afk_lobby_stop"));
  byId("afkCloseShift").addEventListener("click", () => run("shift_overlay_control", { mode: "close" }));
  let bookmarkRows = [];
  function folderRows() {
    const folder = byId('afkBookmarkFolder').value;
    return bookmarkRows.filter(row => !folder || bookmarkInFolder(row.group, folder));
  }
  function renderBookmarkItems() {
    const rows = folderRows();
    const select = byId('afkBookmarks');
    select.replaceChildren();
    rows.forEach(row => {
      const option = document.createElement('option');
      option.value = row.serial;
      option.textContent = `${row.group || 'Default'} · ${row.name || 'Unnamed item'}`;
      select.appendChild(option);
    });
    byId('afkBookmarkNote').textContent = `${rows.length} bookmark(s) in this view. Select individual items or add the whole folder, including subfolders.`;
  }
  async function bookmarks() {
    const result = await window.msbt.loadSerialBookmarks();
    if (!result?.ok) throw Error(result?.message || 'Could not load bookmarks.');
    bookmarkRows = result.data?.bookmarks || [];
    const folders = new Set(result.data?.folders || []);
    bookmarkRows.forEach(row => folders.add(row.group || 'Default'));
    [...folders].forEach(folder => {
      const parts = folder.split('/').map(part => part.trim());
      while (parts.length > 1) { parts.pop(); folders.add(parts.join(' / ')); }
    });
    const select = byId('afkBookmarkFolder'), previous = select.value;
    select.replaceChildren(new Option('All folders', ''));
    [...folders].sort((a,b) => a.localeCompare(b)).forEach(folder => select.add(new Option(folder, folder)));
    select.value = folders.has(previous) ? previous : '';
    renderBookmarkItems();
  }
  byId('afkBookmarkFolder').addEventListener('change', renderBookmarkItems);
  window.addEventListener('msbt-bookmarks-changed', () => bookmarks().catch(error => { byId('afkBookmarkNote').textContent = error.message; }));
  for (const [id, guaranteed] of [['afkAddFolder', false], ['afkAddGuaranteedFolder', true]]) {
    byId(id).addEventListener('click', () => {
      if (!byId('afkBookmarkFolder').value) { byId('afkBookmarkNote').textContent = 'Choose a folder first.'; return; }
      byId('afkBookmarkNote').textContent = appendLoot(folderRows().map(row => row.serial), guaranteed).message;
    });
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
  window.msbtAfkAppendLoot = appendLoot;
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
  window.addEventListener("msbt-language-change", () => render({afk_lobby:lastStatus}));
  render(null);
})();
