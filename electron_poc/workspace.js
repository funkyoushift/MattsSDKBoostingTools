/* Responsive workspace shell. Moves existing controls; never dispatches game actions. */
(function () {
  "use strict";
  const MODE_KEY = "msbt.workspace.mode.v1";
  let enabled = new URLSearchParams(location.search).get("workspace") !== "classic";
  try { enabled = enabled && localStorage.getItem(MODE_KEY) !== "classic"; } catch (_) {}
  function setMode(mode) {
    try { localStorage.setItem(MODE_KEY, mode); } catch (_) {}
    location.reload();
  }
  const modeButton = document.createElement("button");
  modeButton.type = "button";
  modeButton.className = "header-btn workspace-mode-button";
  modeButton.textContent = enabled ? "Classic layout" : "New layout";
  modeButton.title = "Switch layout and reload the panel. Your saved classic layouts are retained.";
  modeButton.addEventListener("click", () => setMode(enabled ? "classic" : "workspace"));
  document.querySelector(".header-main-actions").append(modeButton);
  window.MsbtWorkspace = { enabled };
  if (!enabled) return;

  document.body.classList.add("msbt-workspace");
  const groups = [
    ["Character & Boosting", [["boosting", "Boosting"], ["boosting", "AFK Lobby", "afk"], ["boosting", "Levels & XP", "levels"], ["boosting", "Currency", "currency"], ["boosting", "Unlocks & Capacity", "capacity"], ["boosting", "Challenges & UVH", "challenges"]]],
    ["Items & Inventory", [["inventory", "Inventory"], ["bl4-codes", "Item Catalog"], ["serial-tools", "Saved Items", "saved"], ["boosting", "Give Items", "rewards"], ["boosting", "Ground Loot & Vendors", "loot"], ["boosting", "Rarity Weights", "rarity"], ["item-pool", "Random Loot Pools"]]],
    ["Spawning & Waves", [["dev-spawner", "Spawn Enemies & Objects"], ["hoard-builder", "Hoard Builder"], ["combat-vehicle", "Vehicles", "vehicles"]]],
    ["Movement & World", [["player-movement", "Movement"], ["player-movement", "Teleport & World", "world"], ["map-travel", "Map Travel"], ["boosting", "Camera", "camera"]]],
    ["Party & Combat", [["combat-vehicle", "Party & Chaos", "chaos"], ["combat-vehicle", "Combat Tuning", "combat"], ["boosting", "Combat Cheats", "combat"]]],
    ["Editors & Advanced", [["matt-editor", "Matt Editor"], ["serial-tools", "Serial Converter", "convert"], ["serial-tools", "Item Validation", "validate"], ["boosting", "Experimental Character Tools", "experimental"]]],
    ["Shortcuts & Settings", [["quick-menu", "In-game F7 Menu"], ["mobile-gateway", "Mobile Pairing"], ["updates", "Updates"], ["activity", "Activity & Connection"], ["report", "Help & Report an Issue"]]]
  ];
  const sections = {
    boosting: [
      ["overview", "Quick Actions", ["boost-essentials"]],
      ["afk", "AFK Lobby", ["afk-lobby"]],
      ["levels", "Levels & XP", ["boost-levels", "boost-combat-xp"]],
      ["currency", "Currency", ["boost-currency"]],
      ["capacity", "Unlocks & Capacity", ["boost-unlocks", "boost-inventory"]],
      ["challenges", "Challenges & UVH", ["boost-uvh", "boost-challenges"]],
      ["rewards", "Give Items", ["boost-serial"]],
      ["loot", "Loot & Vendors", ["boost-ground-loot", "boost-farm"]],
      ["rarity", "Rarity", ["boost-rarity"]],
      ["camera", "Camera", ["boost-debug"]],
      ["combat", "Combat", ["boost-cheats"]],
      ["experimental", "Experimental", ["boost-late-join"]],
      ["all", "All Controls", null]
    ],
    "serial-tools": [["saved", "Saved Items", ["serial-bookmarks"]], ["convert", "Serial Converter", ["serial-tools-main"]], ["validate", "Validate Items", ["serial-validator"]], ["all", "All Controls", null]],
    "player-movement": [["movement", "Movement", ["move-presets", "move-speed", "move-jump", "move-infjump", "move-wall", "move-glide"]], ["world", "World & Teleport", ["move-world", "move-teleport"]], ["all", "All Controls", null]],
    "combat-vehicle": [["chaos", "Party & Chaos", ["streamer-chaos"]], ["combat", "Combat Tuning", ["combat-tuning"]], ["vehicles", "Vehicles", ["vehicle-tuning"]], ["all", "All Controls", null]]
  };
  const selected = {};
  const shared = new Set(["boost-target", "boost-result", "move-result", "dev-target"]);
  const roots = new Map();
  const titles = { boosting: "Boosting", "dev-spawner": "Spawn enemies & objects", "serial-tools": "Items & serials", "player-movement": "Movement & world", "combat-vehicle": "Party & gameplay", "quick-menu": "In-game F7 menu", "map-travel": "Map travel" };
  const descriptions = { boosting: "Choose who receives the action, then choose a task.", "serial-tools": "Find saved items, convert serials, and validate gear.", "player-movement": "Adjust movement or travel between players.", "combat-vehicle": "Player targeting stays with the actions that use it.", "quick-menu": "Organize your in-game shortcuts.", "map-travel": "Maps, travel stations, and saved locations." };
  const shell = document.createElement("div");
  shell.className = "workspace-shell";
  const side = document.createElement("aside");
  side.className = "workspace-sidebar";
  side.id = "workspaceNavigation";
  side.setAttribute("aria-label", "Workspaces");
  const brand = document.createElement("div");
  brand.className = "workspace-brand";
  brand.textContent = "MSBT";
  side.append(brand);
  const close = document.createElement("button");
  close.className = "workspace-close";
  close.textContent = "Close navigation";
  close.addEventListener("click", () => toggleMenu(false));
  side.append(close);
  const nav = document.createElement("nav");
  nav.setAttribute("aria-label", "Main workspaces");
  groups.forEach(([name, routes]) => {
    const group = document.createElement("details");
    const heading = document.createElement("summary");
    heading.textContent = name;
    group.append(heading);
    routes.forEach(([tab, label, section]) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = label;
      b.dataset.workspaceTab = tab;
      b.dataset.workspaceSection = section || "";
      b.addEventListener("click", () => open(tab, section || defaultSection(tab)));
      group.append(b);
    });
    nav.append(group);
  });
  side.append(nav);
  const hint = document.createElement("p");
  hint.className = "workspace-sidebar-hint";
  hint.textContent = "Text size and spacing are in View. Search all tools with Ctrl+K.";
  side.append(hint);
  const main = document.querySelector(".tab-shell");
  main.before(shell);
  shell.append(side, main);
  const backdrop = document.createElement("button");
  backdrop.className = "workspace-backdrop";
  backdrop.setAttribute("aria-label", "Close navigation");
  backdrop.addEventListener("click", () => toggleMenu(false));
  shell.append(backdrop);
  const menu = document.createElement("button");
  menu.type = "button";
  menu.className = "workspace-menu-button";
  menu.textContent = "Navigation";
  menu.setAttribute("aria-controls", side.id);
  menu.setAttribute("aria-expanded", "false");
  menu.addEventListener("click", () => toggleMenu(!document.body.classList.contains("workspace-menu-open")));
  document.querySelector(".app-header").prepend(menu);
  function toggleMenu(show) {
    document.body.classList.toggle("workspace-menu-open", show);
    menu.setAttribute("aria-expanded", String(show));
    if (show) close.focus(); else menu.focus();
  }
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && document.body.classList.contains("workspace-menu-open")) toggleMenu(false);
  });

  // Split the large mixed cheat panel without replacing any controls or handlers.
  function newPanel(id, title) {
    const p = document.createElement("section");
    p.className = "panel";
    p.dataset.msbtPanel = id;
    p.dataset.msbtTitle = title;
    const h = document.createElement("h2"); h.textContent = title; p.append(h);
    document.getElementById("tab-boosting").append(p);
    return p;
  }
  const levels = newPanel("boost-levels", "Levels & XP");
  const currency = newPanel("boost-currency", "Currency");
  const unlocks = newPanel("boost-unlocks", "Unlocks");
  levels.append(document.getElementById("xpTrack").closest(".boost-knob-group"));
  currency.append(document.getElementById("currencyKind").closest(".boost-knob-group"));
  const cheatButtons = document.querySelector('[data-msbt-panel="boost-cheats"] > .button-grid');
  const moved = { devperk_0: levels, devperk_1: currency, devperk_2: currency, max_currency: currency, max_eridium: currency, max_player_level: levels, max_spec_level: levels, max_sdu: unlocks };
  Array.from(cheatButtons.children).forEach(b => {
    const dest = moved[b.dataset.action];
    if (dest) {
      if (dest.querySelector(`[data-action="${b.dataset.action}"]`)) b.classList.add("workspace-redundant");
      dest.append(b);
    }
  });
  const cosmetic = document.querySelector('[data-action="devperk_4"]');
  if (cosmetic) unlocks.append(cosmetic);

  document.querySelectorAll(".tab-panel[data-msbt-layout-tab]").forEach(tab => {
    const id = tab.dataset.msbtLayoutTab;
    tab.dataset.workspaceLayoutTab = id;
    tab.removeAttribute("data-msbt-layout-tab");
    const panels = Array.from(tab.querySelectorAll("[data-msbt-panel]"));
    const header = document.createElement("header"); header.className = "workspace-heading";
    const h = document.createElement("h2"); h.textContent = titles[id] || id;
    const p = document.createElement("p"); p.textContent = descriptions[id] || "";
    header.append(h, p); tab.prepend(header);
    if (sections[id]) {
      const bar = document.createElement("nav"); bar.className = "workspace-sections"; bar.setAttribute("aria-label", h.textContent + " sections");
      sections[id].forEach(([key, label]) => {
        const button = document.createElement("button"); button.textContent = label; button.type = "button";
        button.dataset.workspaceLocalSection = key;
        button.addEventListener("click", () => open(id, key)); bar.append(button);
      });
      header.after(bar);
    }
    const root = document.createElement("div"); root.className = "workspace-panels";
    root.setAttribute("data-msbt-layout-root", "");
    panels.forEach(panel => { root.append(panel); if (shared.has(panel.dataset.msbtPanel)) panel.classList.add("workspace-shared"); });
    tab.append(root); roots.set(id, root);
    tab.querySelectorAll(":scope > .grid, :scope > .quick-menu-editor-shell").forEach(n => { if (!n.textContent.trim() && !n.querySelector("input,button,select")) n.remove(); });
  });
  // Labels can change independently of action ids.
  document.querySelectorAll('[data-action="max_spec_level"]').forEach(b => b.textContent = "Max Specialization Level");
  document.querySelectorAll('[data-action="max_player_level"]').forEach(b => b.textContent = "Max Character Level");
  document.querySelector('[data-msbt-panel="boost-target"] h2').textContent = "Players & action scope";
  document.querySelector('[data-msbt-panel="serial-bookmarks"] h2').textContent = "Saved Items";
  document.querySelector('#tab-dev-spawner .dev-spawner-title-row h2').textContent = titles["dev-spawner"];
  document.querySelector('.tab-bar [data-tab="bl4-codes"]').textContent = "Item Catalog";
  document.querySelector('.tab-bar [data-tab="dev-spawner"]').textContent = "Spawn Enemies & Objects";
  const field = document.getElementById("appFinderInput");
  field.placeholder = "Find a feature… (Ctrl+K)";
  // Catalog/status responses can contain thousands of lines. Keep the status
  // visible and make the full diagnostic response available on demand.
  const challengeOutput = document.getElementById("challengeOutput");
  const challengeLog = document.createElement("details");
  challengeLog.className = "workspace-output-fold";
  const challengeLogTitle = document.createElement("summary");
  challengeLogTitle.textContent = "Challenge details & log";
  challengeOutput.before(challengeLog);
  challengeLog.append(challengeLogTitle, challengeOutput);
  // Keep long category lists optional without hiding the search field.
  const categories = document.getElementById("devActorCategoryButtons").closest(".dev-browser-section");
  const categoryFold = document.createElement("details"); categoryFold.className = "workspace-category-fold";
  const categoryTitle = document.createElement("summary"); categoryTitle.textContent = "Browse categories";
  categories.before(categoryFold); categoryFold.append(categoryTitle, categories);
  // Scope stays on screen as a compact, expandable section, not a second settings page.
  ["boost-target", "dev-target"].forEach(id => {
    const panel = document.querySelector(`[data-msbt-panel="${id}"]`);
    const heading = panel.querySelector("h2");
    const fold = document.createElement("details"); fold.className = "workspace-scope";
    const summary = document.createElement("summary"); summary.textContent = id === "boost-target" ? "Choose players & spawn location" : "Choose party target";
    fold.append(summary);
    Array.from(panel.children).forEach(n => { if (n !== heading && !["targetSummary", "devTargetSummary"].includes(n.id)) fold.append(n); });
    panel.append(fold);
  });
  function defaultSection(tab) { return sections[tab] ? sections[tab][0][0] : ""; }
  function applySection(tab, value) {
    if (!sections[tab]) return;
    const definition = sections[tab].find(s => s[0] === value) || sections[tab][0];
    selected[tab] = definition[0];
    roots.get(tab).querySelectorAll("[data-msbt-panel]").forEach(p => {
      p.classList.toggle("workspace-section-hidden", Boolean(definition[2]) && !shared.has(p.dataset.msbtPanel) && !definition[2].includes(p.dataset.msbtPanel));
      if (!shared.has(p.dataset.msbtPanel)) p.style.order = definition[2] ? String(Math.max(0, definition[2].indexOf(p.dataset.msbtPanel))) : "";
    });
    document.querySelectorAll(`#tab-${tab} [data-workspace-local-section]`).forEach(b => {
      const active = b.dataset.workspaceLocalSection === selected[tab];
      b.classList.toggle("active", active); b.setAttribute("aria-pressed", String(active));
    });
  }
  function sync(tab) {
    applySection(tab, selected[tab] || defaultSection(tab));
    let found = false;
    nav.querySelectorAll("button").forEach(b => {
      const active = b.dataset.workspaceTab === tab && (b.dataset.workspaceSection || defaultSection(tab)) === (selected[tab] || defaultSection(tab));
      b.classList.toggle("active", active);
      if (active) { b.setAttribute("aria-current", "page"); b.parentElement.open = true; found = true; } else b.removeAttribute("aria-current");
    });
    if (!found) { const fallback = nav.querySelector(`[data-workspace-tab="${tab}"]`); if (fallback) fallback.parentElement.open = true; }
  }
  function open(tab, section) {
    selected[tab] = section || defaultSection(tab);
    if (typeof window.switchTab === "function") window.switchTab(tab);
    sync(tab); main.scrollTop = 0;
    if (document.body.classList.contains("workspace-menu-open")) toggleMenu(false);
  }
  function revealPanel(panel) {
    if (!panel) return false;
    const tab = panel.closest(".tab-panel");
    if (!tab) return false;
    const id = tab.id.replace(/^tab-/, "");
    const definition = (sections[id] || []).find(s => s[2] && s[2].includes(panel.dataset.msbtPanel));
    if (definition) { selected[id] = definition[0]; sync(id); }
    panel.classList.remove("workspace-section-hidden");
    panel.querySelectorAll(":scope > details.workspace-scope").forEach(fold => { fold.open = true; });
    for (let n = panel.parentElement; n && n !== tab; n = n.parentElement) if (n.tagName === "DETAILS") n.open = true;
    return true;
  }
  window.MsbtWorkspace = { enabled, onTabShown: sync, open, revealPanel, sections };
  Object.keys(sections).forEach(id => applySection(id, defaultSection(id)));
  sync("boosting");
})();
