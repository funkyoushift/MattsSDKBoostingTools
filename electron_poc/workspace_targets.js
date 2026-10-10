/* Inline selectors mirror existing target state; they do not add backend scopes. */
(() => {
  if (!window.MsbtWorkspace?.enabled) return;
  const pickers = [];
  const panel = id => document.querySelector(`[data-msbt-panel="${id}"]`);
  function add(parent, mode, title, sourceId = "") {
    if (!parent) return;
    const row = document.createElement("div"); row.className = "workspace-inline-target";
    const label = document.createElement("label"); label.textContent = title;
    const select = document.createElement("select"); select.dataset.workspaceTargetMode = mode;
    if (sourceId) select.dataset.workspaceTargetSource = sourceId;
    label.append(select); row.append(label);
    const refresh = document.createElement("button"); refresh.type = "button"; refresh.textContent = "Refresh players";
    refresh.addEventListener("click", () => void bridgeStatus()); row.append(refresh);
    const heading = parent.querySelector(":scope > h2, :scope > summary");
    if (heading) heading.after(row); else parent.prepend(row);
    const item = {select, mode, sourceId}; pickers.push(item);
    select.addEventListener("change", async () => {
      select.disabled = true;
      try {
        if (mode === "public" || mode === "party") {
          if (select.value.startsWith("player:")) {
            const result = await setTarget(select.value.slice(7), {keepBoostScope:mode === "public"});
            if (actionSucceeded(result)) {
              if (mode === "public") setPublicBoostScope("selected"); else setBoostTargetScope("selected");
            }
          } else if (select.value.startsWith("scope:")) {
            if (mode === "public") setPublicBoostScope(select.value.slice(6)); else setBoostTargetScope(select.value.slice(6));
          }
          syncFarmingLabStatus(latestFarmingStatus);
        } else {
          const source = document.getElementById(sourceId);
          source.value = select.value;
          source.dispatchEvent(new Event("change", {bubbles:true}));
        }
      } finally { select.disabled = false; sync(); }
    });
    return row;
  }
  function sync() {
    for (const {select, mode, sourceId} of pickers) {
      const source = sourceId && document.getElementById(sourceId);
      const scoped = mode === "public" || mode === "party";
      const currentScope = mode === "public" ? state.publicBoostScope : state.boostTargetScope;
      const rows = scoped ? [
        ["", "Choose a player"],
        ...(mode === "public" ? [["scope:local", "My Character"]] : []),
        ["scope:all", "All Players"], ["scope:nonhost", "Other Players"],
        ...state.players.map(p => ["player:" + playerValue(p), playerLabel(p)])
      ] : Array.from(source?.options || [], o => [o.value, o.textContent]);
      const signature = JSON.stringify(rows);
      if (select.dataset.options !== signature) {
        select.replaceChildren(...rows.map(([value, text]) => new Option(text, value)));
        select.dataset.options = signature;
      }
      const value = scoped ? currentScope === "selected" ? (state.selectedTarget ? "player:" + state.selectedTarget : "") : "scope:" + currentScope
        : sourceId === "targetSelect" ? (state.pendingTargetValue || state.selectedTarget || "") : source?.value || "";
      // Do not disturb an open native dropdown during status polling.
      if (document.activeElement !== select && select.value !== value) select.value = value;
    }
  }
  ["boost-levels", "boost-currency", "boost-unlocks", "boost-inventory", "boost-max-all"].forEach(id => add(panel(id), "public", "Apply to"));
  // Native game shortcuts take one selected controller, unlike scoped Set/Max actions.
  for (const [id, actions] of [["boost-levels", [0]], ["boost-currency", [1, 2]], ["boost-unlocks", [4]], ["boost-drops", [7]]]) {
    const group = document.createElement("details"); group.className = "gameplay-advanced";
    const summary = document.createElement("summary"); summary.textContent = "Game shortcuts · one named player"; group.append(summary);
    actions.forEach(index => {
      const button = panel(id).querySelector(`[data-action="devperk_${index}"]`);
      if (button) group.append(button);
    });
    panel(id).append(group);
    add(group, "mirror", "Named player (remote targeting requires host)", "targetSelect");
  }
  add(panel("boost-drops"), "public", "Shinies: Deliver to (backpack drops stay local)");
  add(panel("streamer-chaos"), "party", "Party action target");
  ["move-presets", "move-speed", "move-jump", "move-infjump", "move-wall", "move-flight"].forEach(id => add(panel(id), "mirror", "Movement applies to", "movementScope"));
  add(panel("move-teleport"), "mirror", "Selected player for teleport", "targetSelect");
  add(panel("boost-late-join"), "mirror", "Named player (experimental; see limits below)", "targetSelect");
  add(panel("boost-uvh"), "mirror", "Mayhem player (UVH still applies to the lobby)", "targetSelect");
  add(panel("boost-ground-loot"), "mirror", "Named player (when Named Player mode is selected)", "targetSelect");
  add(panel("boost-debug"), "mirror", "Player for Pull Cam to Target", "targetSelect");
  add(panel("travel-reveal"), "public", "Clear Fog applies to");
  add(panel("travel-reveal")?.querySelector("details"), "mirror", "Guest-grid diagnostics player", "targetSelect");
  ["boost-weapon-tests", "combat-skill-tests"].forEach(id => add(panel(id)?.querySelector(".gameplay-advanced"), "mirror", "Named player for game toggle (host only)", "targetSelect"));
  add(document.querySelector(".dev-spawner-controls"), "mirror", "Named spawn player", "targetSelect");
  add(document.querySelector(".item-pool-page"), "mirror", "Spawn near", "boostSpawnAnchor");
  add(document.querySelector(".item-pool-page"), "mirror", "Named spawn player", "targetSelect");
  // The controls above replace navigation detours, not the canonical selectors.
  document.querySelectorAll('[data-workspace-section="players"]').forEach(b => {
    if (b.closest('.workspace-sidebar, .workspace-home-grid')) return;
    b.hidden = true;
  });
  document.querySelectorAll('.gameplay-advanced [data-open-panel="boost-target"]').forEach(b => b.hidden = true);
  const combat = document.getElementById("combatScope").closest("label");
  panel("combat-tuning").querySelector("h2").after(combat);
  function scopeNote(id, text) {
    const p = document.createElement("p"); p.className = "workspace-scope-note"; p.textContent = text;
    panel(id)?.querySelector("h2")?.after(p);
  }
  scopeNote("move-world", "World time is a session setting. These controls do not use a named-player selector.");
  scopeNote("move-interaction", "Local interaction toggles; no recipient selection is used.");
  scopeNote("boost-farm", "Chests and Black Market spawns are host-only. Vendor refresh affects the session.");
  scopeNote("boost-rarity", "Loot weights and drop-rate controls affect the session, not a selected recipient.");
  scopeNote("boost-combat-xp", "The Combat XP toggle does not use the selected-player target.");
  scopeNote("boost-challenges", "Challenge completion applies to live players in the lobby.");
  scopeNote("boost-uvh", "Mayhem rank targets one player and enables lobby access. UVH progression applies to live players in the lobby.");
  document.addEventListener("change", () => queueMicrotask(sync));
  document.addEventListener("focusout", () => queueMicrotask(sync));
  window.addEventListener("msbt-targets-changed", sync);
  const observer = new MutationObserver(sync);
  ["targetSelect", "movementScope", "boostSpawnAnchor"].forEach(id => observer.observe(document.getElementById(id), {childList:true,subtree:true,characterData:true}));
  window.MsbtWorkspace.syncTargets = sync;
  sync();
})();
