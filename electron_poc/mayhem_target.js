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
  add(panel("boost-uvh"), "mirror", "Mayhem player (UVH still applies to the lobby)", "targetSelect");
  document.addEventListener("change", () => queueMicrotask(sync));
  document.addEventListener("focusout", () => queueMicrotask(sync));
  const observer = new MutationObserver(sync);
  observer.observe(document.getElementById("targetSelect"), {childList:true,subtree:true,characterData:true});
  sync();
})();
