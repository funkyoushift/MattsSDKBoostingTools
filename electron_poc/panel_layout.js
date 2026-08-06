/**
 * MSBT Electron dockable panels (GridStack).
 * Free drag onto empty cells, resize, compact/fill gaps, and stack into tabs.
 * Also: View prefs (text scale, main-tab order/visibility).
 */
(function (global) {
  "use strict";

  const STORAGE_PREFIX = "msbt.panelLayout.v2.";
  const TEXT_SCALE_KEY = "msbt.uiTextScale";
  const NAV_TABS_KEY = "msbt.navTabs.v1";
  const TEXT_SCALE_MIN = 0.85;
  const TEXT_SCALE_MAX = 1.4;
  const TEXT_SCALE_STEP = 0.05;
  const COLS = 12;
  const STACK_ZONE = 0.45; // center fraction that triggers stack-on-drop
  const Z_BASE = 10;
  const CELL_HEIGHT = 72;
  /** Tabs whose single main panel should stretch to fill remaining viewport height. */
  const FILL_TABS = new Set(["matt-editor"]);

  /** @type {WeakMap<Element, any>} */
  const grids = new WeakMap();
  let hideRestoreHintShown = false;
  let zCounter = Z_BASE;

  function storageKey(tabId) {
    return STORAGE_PREFIX + String(tabId || "");
  }

  function loadState(tabId) {
    try {
      const raw = localStorage.getItem(storageKey(tabId));
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch (_err) {
      return null;
    }
  }

  function saveState(tabId, state) {
    try {
      localStorage.setItem(storageKey(tabId), JSON.stringify(state));
    } catch (_err) {
      /* ignore */
    }
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function cssEscape(value) {
    if (global.CSS && typeof global.CSS.escape === "function") return global.CSS.escape(value);
    return String(value).replace(/"/g, '\\"');
  }

  function panelTitle(panel) {
    return (
      panel.getAttribute("data-msbt-title")
      || (panel.querySelector("h2") ? panel.querySelector("h2").textContent.trim() : "")
      || panel.getAttribute("data-msbt-panel")
      || "Panel"
    );
  }

  function defaultSize(panel) {
    const span = Number(panel.getAttribute("data-msbt-span") || 6) || 6;
    const id = panel.getAttribute("data-msbt-panel") || "";
    const w = Math.min(COLS, Math.max(3, span));
    let h = 5;
    let minH = 2;
    if (id === "matt-editor-main") {
      // Tall enough for first paint; syncFillTab expands to viewport.
      h = 18;
      minH = 10;
    } else if (id === "dev-browser") {
      h = 12;
      minH = 6;
    } else if (id === "inv-main") {
      h = 11;
      minH = 6;
    } else if (id === "bl4-main") {
      h = 11;
      minH = 6;
    } else if (id === "serial-bookmarks" || id === "travel-main") {
      h = 9;
      minH = 5;
    } else if (id === "qm-slots") {
      h = 10;
      minH = 5;
    } else if (id === "boost-result" || id === "dev-result" || id === "move-result") {
      h = 3;
      minH = 2;
    } else if (id === "activity-log" || id === "activity-bridge" || id === "report-preview") {
      h = 8;
      minH = 4;
    } else if (w >= 12) {
      h = panel.hasAttribute("data-msbt-resize") ? 8 : 4;
      minH = 3;
    } else if (w <= 4) {
      h = 5;
      minH = 3;
    }
    return { w, h, minH };
  }

  function ensureChrome(panel) {
    if (panel.querySelector(":scope > .msbt-panel-chrome")) return;
    const title = panelTitle(panel);
    panel.setAttribute("data-msbt-title", title);

    const kids = Array.from(panel.childNodes);
    const body = document.createElement("div");
    body.className = "msbt-panel-body";
    kids.forEach((node) => body.appendChild(node));
    panel.appendChild(body);

    const chrome = document.createElement("div");
    chrome.className = "msbt-panel-chrome";
    chrome.innerHTML = [
      '<span class="msbt-panel-handle" title="Drag to move" role="button" tabindex="0" aria-label="Drag to move">⠿</span>',
      `<span class="msbt-panel-title msbt-panel-handle" title="Drag to move">${escapeHtml(title)}</span>`,
      '<div class="msbt-panel-actions">',
      '<button type="button" class="msbt-panel-collapse" title="Collapse / expand" aria-label="Collapse or expand">▾</button>',
      '<button type="button" class="msbt-panel-hide" title="Hide panel — restore from Panels menu" aria-label="Hide panel">✕</button>',
      "</div>"
    ].join("");
    panel.insertBefore(chrome, body);
    body.querySelectorAll("h2").forEach((h2) => h2.classList.add("msbt-panel-h2-hidden"));
  }

  function wrapAsGridItem(panel, opts) {
    const item = document.createElement("div");
    item.className = "grid-stack-item";
    item.setAttribute("data-msbt-item", "1");
    const defaults = defaultSize(panel);
    const w = opts && opts.w ? opts.w : defaults.w;
    const h = opts && opts.h ? opts.h : defaults.h;
    const minH = opts && opts.minH != null ? opts.minH : defaults.minH;
    item.setAttribute("gs-w", String(w));
    item.setAttribute("gs-h", String(h));
    item.setAttribute("gs-min-w", "3");
    item.setAttribute("gs-min-h", String(Math.max(2, minH || 2)));
    if (opts && opts.x != null) item.setAttribute("gs-x", String(opts.x));
    if (opts && opts.y != null) item.setAttribute("gs-y", String(opts.y));
    if (opts && opts.z != null) {
      item.style.zIndex = String(opts.z);
      zCounter = Math.max(zCounter, Number(opts.z) || Z_BASE);
    }
    const content = document.createElement("div");
    content.className = "grid-stack-item-content msbt-gs-content";
    panel.classList.add("msbt-dock-panel");
    content.appendChild(panel);
    item.appendChild(content);
    return item;
  }

  function refreshItemDrag(grid, item) {
    if (!grid || !item || typeof grid.prepareDragDrop !== "function") return;
    try {
      grid.prepareDragDrop(item, true);
    } catch (_err) {
      /* ignore */
    }
  }

  function removeGridItemClean(grid, item) {
    if (!item) return;
    if (grid) {
      try {
        grid.removeWidget(item, false);
      } catch (_err) {
        /* ignore */
      }
    }
    if (item.parentElement) item.remove();
  }

  function showLayoutToast(message) {
    let toast = document.getElementById("msbtLayoutToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "msbtLayoutToast";
      toast.className = "msbt-layout-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("visible");
    clearTimeout(showLayoutToast._timer);
    showLayoutToast._timer = setTimeout(() => {
      toast.classList.remove("visible");
    }, 4200);
  }

  function bringItemToFront(item) {
    if (!item || !item.classList.contains("grid-stack-item")) return;
    zCounter += 1;
    item.style.zIndex = String(zCounter);
  }

  function availableFillRows(root, grid) {
    const cellH = (grid && typeof grid.getCellHeight === "function")
      ? (Number(grid.getCellHeight(true)) || CELL_HEIGHT)
      : CELL_HEIGHT;
    const host = root.parentElement;
    let avail = 0;
    if (host && host.clientHeight > 40) {
      const toolbar = host.querySelector(":scope > [data-msbt-layout-toolbar-host]");
      const toolbarH = toolbar ? toolbar.getBoundingClientRect().height + 10 : 0;
      avail = Math.max(0, host.clientHeight - toolbarH);
    }
    const rect = root.getBoundingClientRect();
    const maxByViewport = Math.max(0, window.innerHeight - rect.top - 10);
    if (avail < 80) avail = maxByViewport;
    else if (maxByViewport > 0) avail = Math.min(avail, maxByViewport);
    // Leave a small slack so GridStack chrome/margins do not force a page scrollbar.
    return Math.max(10, Math.floor((avail - 12) / cellH));
  }

  function syncFillTab(tab) {
    if (!tab) return;
    const tabId = tab.getAttribute("data-msbt-layout-tab");
    if (!FILL_TABS.has(tabId)) return;
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    if (!root || !grid) return;
    const items = Array.from(root.querySelectorAll(":scope > .grid-stack-item"))
      .filter((item) => item.gridstackNode && !item.classList.contains("grid-stack-placeholder"));
    if (items.length !== 1) return;
    const item = items[0];
    const rows = availableFillRows(root, grid);
    const node = item.gridstackNode;
    if (Number(node.h) === rows && Number(node.y) === 0) return;
    try {
      grid.update(item, { h: rows, y: 0 });
    } catch (_err) {
      /* ignore */
    }
  }

  function scheduleFillSync(tab) {
    if (!tab || !FILL_TABS.has(tab.getAttribute("data-msbt-layout-tab"))) return;
    requestAnimationFrame(() => {
      syncFillTab(tab);
      requestAnimationFrame(() => syncFillTab(tab));
    });
  }

  function flattenIntoRoot(tab) {
    let root = tab.querySelector(":scope > [data-msbt-layout-root]");
    if (root) return root;
    root = document.createElement("div");
    root.className = "msbt-layout-root grid-stack";
    root.setAttribute("data-msbt-layout-root", "");

    const panels = Array.from(tab.querySelectorAll("[data-msbt-panel]"));
    panels.sort((a, b) => {
      const pos = a.compareDocumentPosition(b);
      if (pos & Node.DOCUMENT_POSITION_FOLLOWING) return -1;
      if (pos & Node.DOCUMENT_POSITION_PRECEDING) return 1;
      return 0;
    });

    const toolbarHost = document.createElement("div");
    toolbarHost.className = "msbt-layout-toolbar-host";
    toolbarHost.setAttribute("data-msbt-layout-toolbar-host", "");

    // Keep non-panel chrome (e.g. update notice, section headings) above the dock root.
    const anchor = Array.from(tab.children).find((child) => {
      return child.matches && (
        child.matches("[data-msbt-panel]")
        || child.classList.contains("grid")
        || child.classList.contains("bl4-layout")
        || child.classList.contains("quick-menu-editor-shell")
      );
    }) || null;
    if (anchor) {
      tab.insertBefore(toolbarHost, anchor);
      tab.insertBefore(root, toolbarHost.nextSibling);
    } else {
      tab.appendChild(toolbarHost);
      tab.appendChild(root);
    }

    panels.forEach((panel) => {
      try {
        root.appendChild(wrapAsGridItem(panel));
      } catch (err) {
        console.warn("[MSBT] skip panel wrap", panel.getAttribute("data-msbt-panel"), err && err.message);
      }
    });

    tab.querySelectorAll(":scope > .grid").forEach((grid) => {
      if (!grid.children.length) grid.remove();
    });
    tab.querySelectorAll(":scope > .bl4-layout, :scope > .quick-menu-editor-shell").forEach((shell) => {
      if (!shell.children.length) shell.remove();
    });

    // Keep Quick Menu page tabs above the dock (not below after panels move).
    const pageTabs = tab.querySelector("#quickMenuPageTabs");
    if (pageTabs && pageTabs.parentElement === tab) {
      tab.insertBefore(pageTabs, root);
    }

    return root;
  }

  function ensureToolbar(tab) {
    let host = tab.querySelector("[data-msbt-layout-toolbar-host]");
    if (!host) {
      host = document.createElement("div");
      host.className = "msbt-layout-toolbar-host";
      host.setAttribute("data-msbt-layout-toolbar-host", "");
      const root = tab.querySelector("[data-msbt-layout-root]");
      tab.insertBefore(host, root || tab.firstChild);
    }
    if (host.querySelector(".msbt-layout-toolbar")) return host.querySelector(".msbt-layout-toolbar");
    const bar = document.createElement("div");
    bar.className = "msbt-layout-toolbar";
    bar.innerHTML = [
      '<span class="msbt-layout-hint">Drag freely (panels may overlap) · drop on a panel <strong>center</strong> to stack as tabs · drag a <strong>tab name</strong> to detach · resize edges · <strong>Compact</strong> packs and clears overlaps.</span>',
      '<div class="msbt-layout-toolbar-actions">',
      '<details class="msbt-panels-menu">',
      "<summary>Panels</summary>",
      '<div class="msbt-panels-menu-body" data-msbt-panels-menu></div>',
      "</details>",
      '<button type="button" class="secondary msbt-layout-walkthrough" title="Short tips for this tab">Walkthrough</button>',
      '<button type="button" class="secondary msbt-layout-compact" title="Pack panels, fill gaps, and clear overlaps">Compact</button>',
      '<button type="button" class="secondary msbt-layout-reset" title="Restore default layout">Reset layout</button>',
      "</div>"
    ].join("");
    host.appendChild(bar);
    const tabId = tab.getAttribute("data-msbt-layout-tab");
    bar.querySelector(".msbt-layout-reset").addEventListener("click", () => resetTab(tabId));
    bar.querySelector(".msbt-layout-compact").addEventListener("click", () => {
      const grid = grids.get(tab.querySelector("[data-msbt-layout-root]"));
      if (grid) {
        grid.compact();
        persist(tab);
      }
    });
    const walkBtn = bar.querySelector(".msbt-layout-walkthrough");
    if (walkBtn) {
      if (tabId === "quick-menu") {
        walkBtn.textContent = "Walkthrough";
        walkBtn.title = "Full Quick Menu setup (in-game dock + this tab)";
      }
      walkBtn.addEventListener("click", () => {
        if (typeof global.msbtStartTabTutorial === "function") {
          global.msbtStartTabTutorial(tabId);
        }
      });
    }
    return bar;
  }

  function allPanelsInTab(tab) {
    return Array.from(tab.querySelectorAll("[data-msbt-panel]"));
  }

  function refreshPanelsMenu(tab) {
    const menu = tab.querySelector("[data-msbt-panels-menu]");
    if (!menu) return;
    menu.innerHTML = "";
    const hint = document.createElement("div");
    hint.className = "msbt-panels-menu-hint";
    hint.textContent = "Checked = visible. Uncheck to hide; re-check to restore.";
    menu.appendChild(hint);
    allPanelsInTab(tab).forEach((panel) => {
      const id = panel.getAttribute("data-msbt-panel");
      const title = panelTitle(panel);
      const label = document.createElement("label");
      label.className = "msbt-panels-menu-item";
      const input = document.createElement("input");
      input.type = "checkbox";
      const hidden = panel.classList.contains("msbt-panel-hidden")
        || Boolean(panel.closest(".msbt-panel-stash"));
      input.checked = !hidden;
      input.addEventListener("change", () => {
        if (input.checked) showPanel(tab, id);
        else hidePanel(tab, id);
      });
      label.appendChild(input);
      label.appendChild(document.createTextNode(` ${title}`));
      menu.appendChild(label);
    });
  }

  function getStash(tab) {
    let stash = tab.querySelector("[data-msbt-panel-stash]");
    if (!stash) {
      stash = document.createElement("div");
      stash.className = "msbt-panel-stash";
      stash.setAttribute("data-msbt-panel-stash", "");
      stash.hidden = true;
      tab.appendChild(stash);
    }
    return stash;
  }

  function findGridItemForPanel(panel) {
    return panel.closest(".grid-stack-item");
  }

  function hidePanel(tab, panelId) {
    const panel = tab.querySelector(`[data-msbt-panel="${cssEscape(panelId)}"]`);
    if (!panel) return;
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    const item = findGridItemForPanel(panel);
    const stack = panel.closest(".msbt-stack");
    if (stack) {
      removePanelFromStack(tab, panel, { keepInDom: false });
    } else if (item) {
      removeGridItemClean(grid, item);
    }
    panel.classList.add("msbt-panel-hidden");
    getStash(tab).appendChild(panel);
    if (grid) grid.compact();
    persist(tab);
    if (!hideRestoreHintShown) {
      hideRestoreHintShown = true;
      showLayoutToast("Panel hidden — restore from the Panels menu (or View → Panels).");
    }
  }

  function showPanel(tab, panelId) {
    const stash = getStash(tab);
    const panel = stash.querySelector(`[data-msbt-panel="${cssEscape(panelId)}"]`)
      || tab.querySelector(`[data-msbt-panel="${cssEscape(panelId)}"]`);
    if (!panel) return;
    panel.classList.remove("msbt-panel-hidden");
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    if (!grid) return;
    if (panel.closest(".grid-stack-item")) {
      persist(tab);
      return;
    }
    ensureChrome(panel);
    const item = wrapAsGridItem(panel);
    grid.addWidget(item);
    wirePanelActions(tab, panel);
    refreshItemDrag(grid, item);
    grid.compact();
    persist(tab);
  }

  function wirePanelActions(tab, panel) {
    const collapseBtn = panel.querySelector(".msbt-panel-collapse");
    const hideBtn = panel.querySelector(".msbt-panel-hide");
    if (collapseBtn && !collapseBtn.dataset.msbtBound) {
      collapseBtn.dataset.msbtBound = "1";
      collapseBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const item = findGridItemForPanel(panel);
        const grid = grids.get(tab.querySelector("[data-msbt-layout-root]"));
        const collapsed = panel.classList.toggle("msbt-panel-collapsed");
        collapseBtn.textContent = collapsed ? "▸" : "▾";
        if (item && grid) {
          if (collapsed) {
            item.dataset.msbtPrevH = String(item.gridstackNode && item.gridstackNode.h || item.getAttribute("gs-h") || 4);
            grid.update(item, { h: 1 });
          } else {
            const prev = Number(item.dataset.msbtPrevH || 5);
            grid.update(item, { h: Math.max(2, prev) });
          }
        }
        persist(tab);
      });
    }
    if (hideBtn && !hideBtn.dataset.msbtBound) {
      hideBtn.dataset.msbtBound = "1";
      hideBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        hidePanel(tab, panel.getAttribute("data-msbt-panel"));
      });
    }
  }

  function isStackContent(content) {
    return Boolean(content && content.querySelector(":scope > .msbt-stack"));
  }

  function makeStackShell(initialPanel) {
    const stack = document.createElement("div");
    stack.className = "msbt-stack";
    stack.setAttribute("data-msbt-stack", "1");
    const tabs = document.createElement("div");
    tabs.className = "msbt-stack-tabs";
    tabs.innerHTML = '<div class="msbt-stack-tablist" data-msbt-stack-tablist></div><button type="button" class="msbt-stack-pop" title="Pop active tab into its own panel">⧉</button>';
    const bodies = document.createElement("div");
    bodies.className = "msbt-stack-bodies";
    stack.appendChild(tabs);
    stack.appendChild(bodies);
    if (initialPanel) {
      bodies.appendChild(initialPanel);
      initialPanel.classList.add("msbt-stack-active");
    }
    return stack;
  }

  function wireStackPop(tab, stack) {
    const popBtn = stack.querySelector(".msbt-stack-pop");
    if (popBtn && !popBtn.dataset.msbtBound) {
      popBtn.dataset.msbtBound = "1";
      popBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        popActiveStackTab(tab, stack);
      });
    }
  }

  function rebuildStackTabs(tab, stack) {
    const list = stack.querySelector("[data-msbt-stack-tablist]");
    if (!list) return;
    list.innerHTML = "";
    const panels = Array.from(stack.querySelectorAll(":scope > .msbt-stack-bodies > [data-msbt-panel]"));
    panels.forEach((panel) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "msbt-stack-tab";
      if (panel.classList.contains("msbt-stack-active")) btn.classList.add("active");
      btn.textContent = panelTitle(panel);
      btn.dataset.panelId = panel.getAttribute("data-msbt-panel");
      btn.title = "Click to switch · drag to detach";
      btn.addEventListener("click", (ev) => {
        if (btn.dataset.msbtDidDrag === "1") {
          ev.preventDefault();
          ev.stopPropagation();
          delete btn.dataset.msbtDidDrag;
          return;
        }
        activateStackTab(tab, stack, panel.getAttribute("data-msbt-panel"));
      });
      if (tab) wireStackTabDetach(tab, stack, btn, panel);
      list.appendChild(btn);
    });
  }

  function activateStackTab(tab, stack, panelId) {
    const panels = Array.from(stack.querySelectorAll(":scope > .msbt-stack-bodies > [data-msbt-panel]"));
    panels.forEach((p) => {
      p.classList.toggle("msbt-stack-active", p.getAttribute("data-msbt-panel") === panelId);
    });
    const layoutTab = tab || stack.closest("[data-msbt-layout-tab]");
    rebuildStackTabs(layoutTab, stack);
  }

  /**
   * Drag a stacked tab label to detach that panel into its own window.
   * Uses a movement threshold so clicks still switch tabs.
   */
  function wireStackTabDetach(tab, stack, btn, panel) {
    btn.addEventListener("pointerdown", (ev) => {
      if (ev.button !== 0) return;
      const startX = ev.clientX;
      const startY = ev.clientY;
      let detached = false;

      const onMove = (moveEv) => {
        if (detached) return;
        const dx = moveEv.clientX - startX;
        const dy = moveEv.clientY - startY;
        if (Math.abs(dx) + Math.abs(dy) < 8) return;
        detached = true;
        btn.dataset.msbtDidDrag = "1";
        cleanup();
        detachStackedPanel(tab, stack, panel, {
          clientX: moveEv.clientX,
          clientY: moveEv.clientY
        });
      };

      const onUp = () => cleanup();

      function cleanup() {
        document.removeEventListener("pointermove", onMove, true);
        document.removeEventListener("pointerup", onUp, true);
        document.removeEventListener("pointercancel", onUp, true);
      }

      document.addEventListener("pointermove", onMove, true);
      document.addEventListener("pointerup", onUp, true);
      document.addEventListener("pointercancel", onUp, true);
    });
  }

  function detachStackedPanel(tab, stack, panel, pointer) {
    if (!panel || !stack || !panel.closest(".msbt-stack")) return null;
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    if (!grid) return null;
    const stackItem = stack.closest(".grid-stack-item");
    const node = stackItem && stackItem.gridstackNode;
    removePanelFromStack(tab, panel, { keepInDom: true, skipCompact: true });
    ensureChrome(panel);
    const defaults = defaultSize(panel);
    let x = node ? Math.min(COLS - 3, (node.x || 0) + 1) : undefined;
    let y = node ? (node.y || 0) : undefined;
    if (pointer && root) {
      const rect = root.getBoundingClientRect();
      const cellW = rect.width / COLS;
      const cellH = 72;
      if (cellW > 0) {
        x = Math.max(0, Math.min(COLS - defaults.w, Math.floor((pointer.clientX - rect.left) / cellW)));
        y = Math.max(0, Math.floor((pointer.clientY - rect.top) / cellH));
      }
    }
    const item = wrapAsGridItem(panel, {
      w: node ? Math.min(COLS, Math.max(3, node.w)) : defaults.w,
      h: node ? Math.max(3, node.h) : defaults.h,
      x,
      y
    });
    bringItemToFront(item);
    grid.addWidget(item);
    wirePanelActions(tab, panel);
    refreshItemDrag(grid, item);
    // Kick GridStack drag from the new panel handle so the user can keep dragging.
    try {
      const handle = item.querySelector(".msbt-panel-handle");
      if (handle && pointer) {
        handle.dispatchEvent(new MouseEvent("mousedown", {
          bubbles: true,
          cancelable: true,
          view: window,
          clientX: pointer.clientX,
          clientY: pointer.clientY,
          button: 0,
          buttons: 1
        }));
      }
    } catch (_err) {
      /* ignore */
    }
    persist(tab);
    return item;
  }

  function stackPanelOnto(tab, sourcePanel, targetPanel) {
    if (!sourcePanel || !targetPanel || sourcePanel === targetPanel) return false;
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    if (!grid) return false;

    const sourceItem = findGridItemForPanel(sourcePanel);
    const targetItem = findGridItemForPanel(targetPanel);
    if (!targetItem || sourceItem === targetItem) return false;

    const sourceStack = sourcePanel.closest(".msbt-stack");
    const panelsToMove = sourceStack
      ? Array.from(sourceStack.querySelectorAll(".msbt-stack-bodies > [data-msbt-panel]"))
      : [sourcePanel];
    if (!panelsToMove.length) return false;
    if (panelsToMove.includes(targetPanel)) return false;

    let targetStack = targetPanel.closest(".msbt-stack");
    const targetContent = targetItem.querySelector(":scope > .grid-stack-item-content");
    if (!targetStack) {
      targetStack = makeStackShell(targetPanel);
      targetContent.innerHTML = "";
      targetContent.appendChild(targetStack);
      targetContent.classList.add("msbt-gs-content");
    }

    // Move panels out of the source item BEFORE removing the widget shell.
    const bodies = targetStack.querySelector(".msbt-stack-bodies");
    panelsToMove.forEach((panel) => {
      panel.classList.remove("msbt-panel-hidden", "msbt-stack-active");
      bodies.appendChild(panel);
    });

    if (sourceItem) {
      removeGridItemClean(grid, sourceItem);
    }

    const focusId = sourcePanel.getAttribute("data-msbt-panel");
    activateStackTab(tab, targetStack, focusId);
    wireStackPop(tab, targetStack);
    refreshItemDrag(grid, targetItem);

    // Do not auto-compact after stack — keeps the stack where the user dropped it.
    persist(tab);
    return true;
  }

  function removePanelFromStack(tab, panel, opts) {
    opts = opts || {};
    const stack = panel.closest(".msbt-stack");
    if (!stack) return;
    const item = stack.closest(".grid-stack-item");
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    const bodies = stack.querySelector(".msbt-stack-bodies");
    panel.classList.remove("msbt-stack-active");
    panel.remove();
    const left = bodies ? Array.from(bodies.querySelectorAll(":scope > [data-msbt-panel]")) : [];
    if (left.length <= 1 && item && grid) {
      const content = item.querySelector(":scope > .grid-stack-item-content");
      if (left.length === 1) {
        const only = left[0];
        only.classList.remove("msbt-stack-active");
        content.innerHTML = "";
        content.appendChild(only);
        refreshItemDrag(grid, item);
      } else {
        removeGridItemClean(grid, item);
      }
    } else {
      if (left.length) activateStackTab(tab, stack, left[0].getAttribute("data-msbt-panel"));
      else rebuildStackTabs(tab, stack);
      refreshItemDrag(grid, item);
    }
    if (!opts.keepInDom) getStash(tab).appendChild(panel);
    if (!opts.skipCompact && grid) grid.compact();
  }

  function popActiveStackTab(tab, stack) {
    const active = stack.querySelector(".msbt-stack-bodies > [data-msbt-panel].msbt-stack-active")
      || stack.querySelector(".msbt-stack-bodies > [data-msbt-panel]");
    if (!active) return;
    detachStackedPanel(tab, stack, active, null);
  }

  /** Shared pointer — must be document-scoped: drag helper uses appendTo:"body". */
  let lastPointer = { x: 0, y: 0 };
  document.addEventListener("pointermove", (ev) => {
    lastPointer = { x: ev.clientX, y: ev.clientY };
  }, true);

  function eventPointer(ev) {
    if (ev && typeof ev.clientX === "number" && typeof ev.clientY === "number") {
      return { x: ev.clientX, y: ev.clientY };
    }
    return lastPointer;
  }

  /**
   * Hit-test panels under the cursor (screen space).
   * Returns inCenter when inside the middle STACK_ZONE fraction (stack drop zone);
   * otherwise over a panel edge (reposition / snap, not stack).
   */
  function panelUnderPoint(root, clientX, clientY, excludeItem) {
    const items = Array.from(root.querySelectorAll(":scope > .grid-stack-item"))
      .filter((item) => item.gridstackNode && !item.classList.contains("grid-stack-placeholder"))
      .sort((a, b) => {
        const za = Number(a.style.zIndex) || 0;
        const zb = Number(b.style.zIndex) || 0;
        return zb - za;
      });
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];
      if (item === excludeItem) continue;
      const rect = item.getBoundingClientRect();
      if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) continue;
      const zx = rect.width * STACK_ZONE;
      const zy = rect.height * STACK_ZONE;
      const inCenter =
        clientX >= rect.left + (rect.width - zx) / 2
        && clientX <= rect.right - (rect.width - zx) / 2
        && clientY >= rect.top + (rect.height - zy) / 2
        && clientY <= rect.bottom - (rect.height - zy) / 2;
      const panel = item.querySelector("[data-msbt-panel].msbt-stack-active")
        || item.querySelector("[data-msbt-panel]");
      if (!panel) continue;
      return { item, panel, inCenter };
    }
    return null;
  }

  /** Strong cell-overlap fallback when the pointer is not precisely in the center zone. */
  function stackTargetByOverlap(root, dragEl) {
    const node = dragEl && dragEl.gridstackNode;
    if (!node) return null;
    let best = null;
    let bestRatio = 0;
    Array.from(root.querySelectorAll(":scope > .grid-stack-item")).forEach((item) => {
      if (item === dragEl || item.classList.contains("grid-stack-placeholder")) return;
      if (!item.gridstackNode) return;
      const other = item.gridstackNode;
      const overlapW = Math.max(0, Math.min(node.x + node.w, other.x + other.w) - Math.max(node.x, other.x));
      const overlapH = Math.max(0, Math.min(node.y + node.h, other.y + other.h) - Math.max(node.y, other.y));
      const overlapArea = overlapW * overlapH;
      if (!overlapArea) return;
      const minArea = Math.min(node.w * node.h, other.w * other.h) || 1;
      const ratio = overlapArea / minArea;
      if (ratio < 0.45 || ratio <= bestRatio) return;
      const panel = item.querySelector("[data-msbt-panel].msbt-stack-active")
        || item.querySelector("[data-msbt-panel]");
      if (!panel) return;
      bestRatio = ratio;
      best = { item, panel, inCenter: true };
    });
    return best;
  }

  /**
   * GridStack always resolves collisions by shoving other widgets.
   * No-op _fixCollisions so drag/resize can layer/overlap (Chrome-like tabbing).
   * Compact still works: it re-adds with autoPosition via collide/empty-slot search.
   */
  function enableOverlapDrag(grid) {
    if (!grid || !grid.engine || grid.engine._msbtOverlapDrag) return;
    grid.engine._msbtOverlapDrag = true;
    grid.engine._fixCollisions = function () {
      return false;
    };
  }

  function collectState(tab) {
    const root = tab.querySelector("[data-msbt-layout-root]");
    const items = [];
    const hidden = [];
    getStash(tab).querySelectorAll("[data-msbt-panel]").forEach((p) => {
      hidden.push(p.getAttribute("data-msbt-panel"));
    });
    if (!root) return { version: 2, items, hidden };
    root.querySelectorAll(":scope > .grid-stack-item").forEach((item) => {
      if (!item.gridstackNode) return;
      const node = item.gridstackNode || {};
      const z = Number(item.style.zIndex) || undefined;
      const stack = item.querySelector(":scope > .grid-stack-item-content > .msbt-stack");
      if (stack) {
        const tabs = Array.from(stack.querySelectorAll(".msbt-stack-bodies > [data-msbt-panel]"))
          .map((p) => p.getAttribute("data-msbt-panel"));
        const activeEl = stack.querySelector(".msbt-stack-bodies > [data-msbt-panel].msbt-stack-active");
        items.push({
          type: "stack",
          tabs,
          active: activeEl ? activeEl.getAttribute("data-msbt-panel") : tabs[0],
          x: node.x,
          y: node.y,
          w: node.w,
          h: node.h,
          z
        });
      } else {
        const panel = item.querySelector("[data-msbt-panel]");
        if (!panel) return;
        items.push({
          type: "panel",
          id: panel.getAttribute("data-msbt-panel"),
          collapsed: panel.classList.contains("msbt-panel-collapsed"),
          x: node.x,
          y: node.y,
          w: node.w,
          h: node.h,
          z
        });
      }
    });
    return { version: 2, items, hidden };
  }

  function persist(tab) {
    const tabId = tab.getAttribute("data-msbt-layout-tab");
    if (!tabId) return;
    saveState(tabId, collectState(tab));
    refreshPanelsMenu(tab);
  }

  function captureDefaults(tab) {
    if (tab.dataset.msbtDefaultLayoutV2) return;
    tab.dataset.msbtDefaultLayoutV2 = JSON.stringify(collectState(tab));
  }

  function applySavedLayout(tab, saved) {
    if (!saved || !Array.isArray(saved.items) || !saved.items.length) return false;
    const root = tab.querySelector("[data-msbt-layout-root]");
    const grid = grids.get(root);
    if (!grid) return false;

    const panelMap = {};
    allPanelsInTab(tab).forEach((p) => {
      panelMap[p.getAttribute("data-msbt-panel")] = p;
    });
    getStash(tab).querySelectorAll("[data-msbt-panel]").forEach((p) => {
      panelMap[p.getAttribute("data-msbt-panel")] = p;
    });

    Array.from(root.querySelectorAll(":scope > .grid-stack-item")).forEach((item) => {
      removeGridItemClean(grid, item);
    });
    Object.keys(panelMap).forEach((id) => {
      const p = panelMap[id];
      p.classList.remove("msbt-stack-active", "msbt-panel-hidden");
      getStash(tab).appendChild(p);
    });

    (saved.hidden || []).forEach((id) => {
      const p = panelMap[id];
      if (p) {
        p.classList.add("msbt-panel-hidden");
        getStash(tab).appendChild(p);
      }
    });

    saved.items.forEach((spec) => {
      if (spec.type === "stack" && Array.isArray(spec.tabs) && spec.tabs.length) {
        const panels = spec.tabs.map((id) => panelMap[id]).filter(Boolean);
        if (!panels.length) return;
        panels.forEach((p) => {
          p.classList.remove("msbt-panel-hidden");
          ensureChrome(p);
          wirePanelActions(tab, p);
        });
        const stack = makeStackShell(panels[0]);
        const bodies = stack.querySelector(".msbt-stack-bodies");
        panels.slice(1).forEach((p) => bodies.appendChild(p));
        const activeId = spec.active && panelMap[spec.active] ? spec.active : panels[0].getAttribute("data-msbt-panel");
        activateStackTab(tab, stack, activeId);
        wireStackPop(tab, stack);

        const item = document.createElement("div");
        item.className = "grid-stack-item";
        item.setAttribute("data-msbt-item", "1");
        item.setAttribute("gs-min-w", "3");
        item.setAttribute("gs-min-h", "4");
        if (spec.z != null) {
          item.style.zIndex = String(spec.z);
          zCounter = Math.max(zCounter, Number(spec.z) || Z_BASE);
        }
        const content = document.createElement("div");
        content.className = "grid-stack-item-content msbt-gs-content";
        content.appendChild(stack);
        item.appendChild(content);
        grid.addWidget(item, { x: spec.x, y: spec.y, w: spec.w || 6, h: Math.max(4, spec.h || 6) });
        refreshItemDrag(grid, item);
      } else if (spec.type === "panel" && spec.id && panelMap[spec.id]) {
        if ((saved.hidden || []).includes(spec.id)) return;
        const panel = panelMap[spec.id];
        panel.classList.remove("msbt-panel-hidden");
        ensureChrome(panel);
        wirePanelActions(tab, panel);
        if (spec.collapsed) {
          panel.classList.add("msbt-panel-collapsed");
          const btn = panel.querySelector(".msbt-panel-collapse");
          if (btn) btn.textContent = "▸";
        }
        const defaults = defaultSize(panel);
        const restoredH = spec.collapsed ? 1 : Math.max(defaults.minH || 2, Number(spec.h) || defaults.h);
        const item = wrapAsGridItem(panel, {
          x: spec.x,
          y: spec.y,
          w: Math.max(3, Number(spec.w) || defaults.w),
          h: restoredH,
          minH: defaults.minH,
          z: spec.z
        });
        if (spec.collapsed && spec.h) item.dataset.msbtPrevH = String(Math.max(defaults.minH || 2, spec.h));
        grid.addWidget(item);
        refreshItemDrag(grid, item);
      }
    });

    Object.keys(panelMap).forEach((id) => {
      const p = panelMap[id];
      if (p.closest(".grid-stack-item")) return;
      if ((saved.hidden || []).includes(id) || p.classList.contains("msbt-panel-hidden")) return;
      ensureChrome(p);
      wirePanelActions(tab, p);
      const item = wrapAsGridItem(p);
      grid.addWidget(item);
      refreshItemDrag(grid, item);
    });

    return true;
  }

  function initGrid(tab, root) {
    if (typeof global.GridStack === "undefined") {
      console.warn("[MSBT] GridStack not loaded; panel docking disabled.");
      return null;
    }
    if (grids.get(root)) return grids.get(root);

    const grid = global.GridStack.init({
      column: COLS,
      cellHeight: CELL_HEIGHT,
      margin: 8,
      float: true,
      animate: true,
      // Handle-only drag (not whole panel) so list scrolling / buttons still work.
      // Title + grip + stack tab strip are all valid handles.
      draggable: {
        handle: ".msbt-panel-handle, .msbt-stack-tabs",
        appendTo: "body",
        scroll: true,
        cancel: "input,textarea,button,select,a,label,.dev-row-list,.list-select,.msbt-stack-tab,.msbt-stack-pop,.msbt-panel-actions"
      },
      resizable: { handles: "e,se,s" },
      alwaysShowResizeHandle: true,
      minRow: 1,
      disableOneColumnMode: true
    }, root);

    enableOverlapDrag(grid);
    grids.set(root, grid);

    let pendingStack = null;

    function clearStackHighlight() {
      root.querySelectorAll(".msbt-stack-target").forEach((n) => n.classList.remove("msbt-stack-target"));
      pendingStack = null;
    }

    function resolveStackTarget(el, pt) {
      const under = panelUnderPoint(root, pt.x, pt.y, el);
      if (under && under.inCenter) return under;
      return stackTargetByOverlap(root, el);
    }

    root.addEventListener("pointerdown", (ev) => {
      const item = ev.target && ev.target.closest && ev.target.closest(":scope > .grid-stack-item, .grid-stack-item");
      if (!item || !root.contains(item) || !item.gridstackNode) return;
      if (ev.target.closest(".msbt-panel-actions, .msbt-stack-pop, .ui-resizable-handle")) return;
      bringItemToFront(item);
    }, true);

    grid.on("dragstart", (_ev, el) => {
      clearStackHighlight();
      if (el) bringItemToFront(el);
    });

    grid.on("drag", (ev, el) => {
      const pt = eventPointer(ev);
      lastPointer = pt;
      clearStackHighlight();
      const hit = resolveStackTarget(el, pt);
      if (hit && hit.panel) {
        hit.item.classList.add("msbt-stack-target");
        pendingStack = hit;
      }
    });

    grid.on("dragstop", (ev, el) => {
      const pt = eventPointer(ev);
      lastPointer = pt;
      const hit = resolveStackTarget(el, pt) || pendingStack;
      clearStackHighlight();

      if (hit && hit.panel) {
        const sourcePanel = el.querySelector("[data-msbt-panel].msbt-stack-active")
          || el.querySelector("[data-msbt-panel]");
        if (sourcePanel && hit.panel !== sourcePanel) {
          const stacked = stackPanelOnto(tab, sourcePanel, hit.panel);
          if (stacked) return;
        }
      }
      persist(tab);
    });

    grid.on("resizestop", () => persist(tab));
    grid.on("change", () => {
      /* dragstop/resizestop persist; avoid thrash */
    });

    return grid;
  }

  function initTab(tab) {
    if (!tab || !tab.getAttribute("data-msbt-layout-tab")) return;
    try {
      if (tab.dataset.msbtLayoutReady === "2") {
        refreshPanelsMenu(tab);
        const root = tab.querySelector("[data-msbt-layout-root]");
        const grid = grids.get(root);
        if (grid) {
          try {
            if (typeof grid.onParentResize === "function") grid.onParentResize();
            else if (typeof grid.cellHeight === "function") grid.cellHeight(grid.getCellHeight(true));
          } catch (_err) {
            /* ignore */
          }
        }
        scheduleFillSync(tab);
        return;
      }
      if (typeof global.GridStack === "undefined") {
        console.warn("[MSBT] GridStack missing; skipping dock layout for", tab.id);
        return;
      }
      const root = flattenIntoRoot(tab);
      root.classList.add("grid-stack");
      allPanelsInTab(tab).forEach((panel) => {
        ensureChrome(panel);
        wirePanelActions(tab, panel);
      });
      ensureToolbar(tab);
      let grid;
      try {
        grid = initGrid(tab, root);
      } catch (gridErr) {
        console.error("[MSBT] GridStack.init failed", gridErr && gridErr.name, gridErr && gridErr.message, gridErr && gridErr.stack);
        throw gridErr;
      }
      if (!grid) return;

      root.querySelectorAll(":scope > .grid-stack-item").forEach((item) => refreshItemDrag(grid, item));

      const tabId = tab.getAttribute("data-msbt-layout-tab");
      const isFillTab = FILL_TABS.has(tabId);
      if (!isFillTab) captureDefaults(tab);

      const saved = loadState(tabId);
      if (saved && saved.version === 2) {
        try {
          applySavedLayout(tab, saved);
        } catch (layoutErr) {
          console.warn("[MSBT] clearing bad saved layout for", tabId, layoutErr && layoutErr.message);
          try { localStorage.removeItem(storageKey(tabId)); } catch (_e) { /* ignore */ }
          grid.compact();
        }
      } else {
        grid.compact();
      }

      refreshPanelsMenu(tab);
      tab.dataset.msbtLayoutReady = "2";
      scheduleFillSync(tab);
      if (isFillTab && !tab.dataset.msbtDefaultLayoutV2) {
        requestAnimationFrame(() => {
          syncFillTab(tab);
          captureDefaults(tab);
        });
      }
    } catch (err) {
      console.error(
        "[MSBT] panel layout init failed for",
        tab && tab.id,
        err && err.name,
        err && err.message,
        err && err.stack
      );
    }
  }

  function resetTab(tabId) {
    const tab = document.querySelector(`[data-msbt-layout-tab="${cssEscape(tabId)}"]`);
    if (!tab) return;
    try {
      localStorage.removeItem(storageKey(tabId));
      localStorage.removeItem("msbt.panelLayout." + tabId);
    } catch (_err) {
      /* ignore */
    }
    try {
      let defaults = null;
      try {
        defaults = tab.dataset.msbtDefaultLayoutV2 ? JSON.parse(tab.dataset.msbtDefaultLayoutV2) : null;
      } catch (_err) {
        defaults = null;
      }
      if (defaults) applySavedLayout(tab, defaults);
      else {
        const root = tab.querySelector("[data-msbt-layout-root]");
        const grid = grids.get(root);
        if (grid) grid.compact();
      }
      scheduleFillSync(tab);
      persist(tab);
    } catch (err) {
      console.error("[MSBT] panel layout reset failed", err);
    }
  }

  function initAll() {
    // Only init the visible tab up front. Hidden tabs break GridStack sizing and
    // used to abort app startup before Dev Spawner lists loaded.
    const active = document.querySelector(".tab-panel.active[data-msbt-layout-tab]");
    if (active) initTab(active);
  }

  function onTabShown(tabId) {
    const tab = document.getElementById(`tab-${tabId}`);
    if (tab && tab.hasAttribute("data-msbt-layout-tab")) {
      initTab(tab);
      const root = tab.querySelector("[data-msbt-layout-root]");
      const grid = grids.get(root);
      if (grid) {
        try {
          if (typeof grid.onParentResize === "function") grid.onParentResize();
        } catch (_err) {
          /* ignore */
        }
      }
      scheduleFillSync(tab);
    }
  }

  let fillResizeTimer = null;
  function onWindowResizeForFill() {
    clearTimeout(fillResizeTimer);
    fillResizeTimer = setTimeout(() => {
      const tab = document.querySelector(".tab-panel.active[data-msbt-layout-tab]");
      if (!tab) return;
      const root = tab.querySelector("[data-msbt-layout-root]");
      const grid = grids.get(root);
      if (grid) {
        try {
          if (typeof grid.onParentResize === "function") grid.onParentResize();
        } catch (_err) {
          /* ignore */
        }
      }
      syncFillTab(tab);
    }, 80);
  }
  global.addEventListener("resize", onWindowResizeForFill);

  /* ---------- Text scale + main nav View menu ---------- */

  function clampTextScale(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return 1;
    return Math.min(TEXT_SCALE_MAX, Math.max(TEXT_SCALE_MIN, Math.round(n / TEXT_SCALE_STEP) * TEXT_SCALE_STEP));
  }

  function loadTextScale() {
    try {
      const raw = localStorage.getItem(TEXT_SCALE_KEY);
      if (raw == null) return 1;
      return clampTextScale(raw);
    } catch (_err) {
      return 1;
    }
  }

  function applyTextScale(scale) {
    const next = clampTextScale(scale);
    document.documentElement.style.setProperty("--msbt-text-scale", String(next));
    try {
      localStorage.setItem(TEXT_SCALE_KEY, String(next));
    } catch (_err) {
      /* ignore */
    }
    const label = document.querySelector("[data-msbt-text-scale-value]");
    if (label) label.textContent = `${Math.round(next * 100)}%`;
    return next;
  }

  function bumpTextScale(delta) {
    return applyTextScale(loadTextScale() + delta);
  }

  function defaultNavTabIds() {
    return Array.from(document.querySelectorAll(".tab-bar [data-tab]")).map((btn) => btn.dataset.tab);
  }

  function loadNavTabsState() {
    const defaults = defaultNavTabIds();
    try {
      const raw = localStorage.getItem(NAV_TABS_KEY);
      if (!raw) return { order: defaults.slice(), hidden: [] };
      const parsed = JSON.parse(raw);
      const order = Array.isArray(parsed.order) ? parsed.order.filter((id) => defaults.includes(id)) : [];
      defaults.forEach((id) => {
        if (!order.includes(id)) order.push(id);
      });
      const hidden = Array.isArray(parsed.hidden)
        ? parsed.hidden.filter((id) => defaults.includes(id) && id !== "boosting")
        : [];
      return { order, hidden };
    } catch (_err) {
      return { order: defaults.slice(), hidden: [] };
    }
  }

  function saveNavTabsState(state) {
    try {
      localStorage.setItem(NAV_TABS_KEY, JSON.stringify(state));
    } catch (_err) {
      /* ignore */
    }
  }

  function applyNavTabsState(state) {
    const bar = document.querySelector(".tab-bar");
    if (!bar) return;
    const buttons = Array.from(bar.querySelectorAll("[data-tab]"));
    const byId = {};
    buttons.forEach((btn) => {
      byId[btn.dataset.tab] = btn;
    });
    (state.order || []).forEach((id) => {
      const btn = byId[id];
      if (btn) bar.appendChild(btn);
    });
    buttons.forEach((btn) => {
      const id = btn.dataset.tab;
      const hide = (state.hidden || []).includes(id);
      btn.classList.toggle("msbt-nav-tab-hidden", hide);
      btn.hidden = hide;
    });

    const activeBtn = bar.querySelector("[data-tab].active");
    if (activeBtn && activeBtn.hidden) {
      const first = bar.querySelector("[data-tab]:not([hidden])");
      if (first && typeof global.switchTab === "function") {
        global.switchTab(first.dataset.tab);
      } else if (first) {
        first.click();
      }
    }
  }

  function moveNavTab(tabId, direction) {
    const state = loadNavTabsState();
    const idx = state.order.indexOf(tabId);
    if (idx < 0) return;
    const next = idx + direction;
    if (next < 0 || next >= state.order.length) return;
    const tmp = state.order[idx];
    state.order[idx] = state.order[next];
    state.order[next] = tmp;
    saveNavTabsState(state);
    applyNavTabsState(state);
    refreshViewMenu();
  }

  function setNavTabHidden(tabId, hidden) {
    const state = loadNavTabsState();
    const set = new Set(state.hidden || []);
    if (hidden) set.add(tabId);
    else set.delete(tabId);
    // Keep at least one visible tab.
    const visible = state.order.filter((id) => !set.has(id));
    if (!visible.length) return;
    state.hidden = Array.from(set);
    saveNavTabsState(state);
    applyNavTabsState(state);
    refreshViewMenu();
  }

  function navTabLabel(tabId) {
    const btn = document.querySelector(`.tab-bar [data-tab="${cssEscape(tabId)}"]`);
    return btn ? btn.textContent.trim() : tabId;
  }

  function refreshViewMenu() {
    const body = document.querySelector("[data-msbt-view-menu-body]");
    if (!body) return;
    const state = loadNavTabsState();
    const scale = loadTextScale();

    body.innerHTML = "";

    const helpBlock = document.createElement("div");
    helpBlock.className = "msbt-view-menu-section";
    helpBlock.innerHTML = '<div class="msbt-view-menu-heading">Walkthroughs</div>';
    const helpActions = document.createElement("div");
    helpActions.className = "msbt-view-text-scale";
    const helpButtons = [
      { label: "App overview", title: "Replay the main app tour", run: () => global.msbtStartMainTutorial && global.msbtStartMainTutorial({ force: true }) },
      { label: "Layout walkthrough", title: "Full panel layout editor tour", run: () => global.msbtStartLayoutTutorial && global.msbtStartLayoutTutorial({ force: true }) },
      { label: "Quick Menu setup", title: "Full Quick Menu setup (in-game dock + ★ Quick Menu tab)", run: () => global.msbtStartQuickMenuSetupTutorial && global.msbtStartQuickMenuSetupTutorial({ force: true }) }
    ];
    helpButtons.forEach((entry) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "secondary";
      btn.textContent = entry.label;
      btn.title = entry.title;
      btn.addEventListener("click", () => {
        const menu = document.querySelector("[data-msbt-view-menu]");
        if (menu) menu.open = false;
        entry.run();
      });
      helpActions.appendChild(btn);
    });
    helpBlock.appendChild(helpActions);
    body.appendChild(helpBlock);

    const textBlock = document.createElement("div");
    textBlock.className = "msbt-view-menu-section";
    textBlock.innerHTML = [
      '<div class="msbt-view-menu-heading">Text size</div>',
      '<div class="msbt-view-text-scale">',
      '<button type="button" class="secondary" data-msbt-text-scale-dec title="Decrease text size">A−</button>',
      '<span data-msbt-text-scale-value></span>',
      '<button type="button" class="secondary" data-msbt-text-scale-inc title="Increase text size">A+</button>',
      '<input type="range" min="85" max="140" step="5" data-msbt-text-scale-slider aria-label="Text size percent">',
      "</div>"
    ].join("");
    body.appendChild(textBlock);

    const valueEl = textBlock.querySelector("[data-msbt-text-scale-value]");
    const slider = textBlock.querySelector("[data-msbt-text-scale-slider]");
    if (valueEl) valueEl.textContent = `${Math.round(scale * 100)}%`;
    if (slider) slider.value = String(Math.round(scale * 100));
    textBlock.querySelector("[data-msbt-text-scale-dec]").addEventListener("click", () => {
      const next = bumpTextScale(-TEXT_SCALE_STEP);
      if (slider) slider.value = String(Math.round(next * 100));
    });
    textBlock.querySelector("[data-msbt-text-scale-inc]").addEventListener("click", () => {
      const next = bumpTextScale(TEXT_SCALE_STEP);
      if (slider) slider.value = String(Math.round(next * 100));
    });
    slider.addEventListener("input", () => {
      applyTextScale(Number(slider.value) / 100);
    });

    const tabsBlock = document.createElement("div");
    tabsBlock.className = "msbt-view-menu-section";
    tabsBlock.innerHTML = '<div class="msbt-view-menu-heading">Main tabs</div>';
    const list = document.createElement("div");
    list.className = "msbt-view-tabs-list";
    state.order.forEach((id, index) => {
      const row = document.createElement("div");
      row.className = "msbt-view-tab-row";
      row.draggable = true;
      row.dataset.tabId = id;

      const check = document.createElement("input");
      check.type = "checkbox";
      check.checked = !(state.hidden || []).includes(id);
      check.title = "Show / hide tab";
      check.addEventListener("change", () => setNavTabHidden(id, !check.checked));

      const name = document.createElement("span");
      name.className = "msbt-view-tab-name";
      name.textContent = navTabLabel(id);

      const up = document.createElement("button");
      up.type = "button";
      up.className = "secondary";
      up.textContent = "↑";
      up.title = "Move tab left";
      up.disabled = index === 0;
      up.addEventListener("click", () => moveNavTab(id, -1));

      const down = document.createElement("button");
      down.type = "button";
      down.className = "secondary";
      down.textContent = "↓";
      down.title = "Move tab right";
      down.disabled = index === state.order.length - 1;
      down.addEventListener("click", () => moveNavTab(id, 1));

      row.appendChild(check);
      row.appendChild(name);
      row.appendChild(up);
      row.appendChild(down);
      list.appendChild(row);

      row.addEventListener("dragstart", (ev) => {
        row.classList.add("dragging");
        try {
          ev.dataTransfer.setData("text/plain", id);
          ev.dataTransfer.effectAllowed = "move";
        } catch (_err) {
          /* ignore */
        }
      });
      row.addEventListener("dragend", () => row.classList.remove("dragging"));
      row.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        row.classList.add("drag-over");
      });
      row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
      row.addEventListener("drop", (ev) => {
        ev.preventDefault();
        row.classList.remove("drag-over");
        let fromId = id;
        try {
          fromId = ev.dataTransfer.getData("text/plain") || id;
        } catch (_err) {
          /* ignore */
        }
        if (fromId === id) return;
        const st = loadNavTabsState();
        const from = st.order.indexOf(fromId);
        const to = st.order.indexOf(id);
        if (from < 0 || to < 0) return;
        st.order.splice(from, 1);
        st.order.splice(to, 0, fromId);
        saveNavTabsState(st);
        applyNavTabsState(st);
        refreshViewMenu();
      });
    });
    tabsBlock.appendChild(list);
    body.appendChild(tabsBlock);

    const panelsBlock = document.createElement("div");
    panelsBlock.className = "msbt-view-menu-section";
    panelsBlock.innerHTML = '<div class="msbt-view-menu-heading">Panels (active tab)</div>';
    const panelsHost = document.createElement("div");
    panelsHost.className = "msbt-view-panels-host";
    panelsHost.setAttribute("data-msbt-view-panels-host", "");
    panelsBlock.appendChild(panelsHost);
    body.appendChild(panelsBlock);
    refreshViewPanelsSection();
  }

  function refreshViewPanelsSection() {
    const host = document.querySelector("[data-msbt-view-panels-host]");
    if (!host) return;
    host.innerHTML = "";
    const tab = document.querySelector(".tab-panel.active[data-msbt-layout-tab]");
    if (!tab) {
      host.textContent = "This tab has no dockable panels.";
      return;
    }
    allPanelsInTab(tab).forEach((panel) => {
      const id = panel.getAttribute("data-msbt-panel");
      const label = document.createElement("label");
      label.className = "msbt-panels-menu-item";
      const input = document.createElement("input");
      input.type = "checkbox";
      const hidden = panel.classList.contains("msbt-panel-hidden")
        || Boolean(panel.closest(".msbt-panel-stash"));
      input.checked = !hidden;
      input.addEventListener("change", () => {
        if (input.checked) showPanel(tab, id);
        else hidePanel(tab, id);
        refreshViewPanelsSection();
      });
      label.appendChild(input);
      label.appendChild(document.createTextNode(` ${panelTitle(panel)}`));
      host.appendChild(label);
    });
  }

  function ensureViewMenu() {
    let menu = document.querySelector("[data-msbt-view-menu]");
    if (menu) return menu;
    const headerActions = document.querySelector(".header-main-actions");
    if (!headerActions) return null;
    menu = document.createElement("details");
    menu.className = "msbt-view-menu";
    menu.setAttribute("data-msbt-view-menu", "");
    menu.innerHTML = [
      "<summary>View</summary>",
      '<div class="msbt-view-menu-body" data-msbt-view-menu-body></div>'
    ].join("");
    const opacity = headerActions.querySelector(".opacity-control");
    if (opacity) headerActions.insertBefore(menu, opacity.nextSibling);
    else headerActions.insertBefore(menu, headerActions.firstChild);
    menu.addEventListener("toggle", () => {
      if (menu.open) refreshViewMenu();
    });
    return menu;
  }

  function enableNavTabDragReorder() {
    const bar = document.querySelector(".tab-bar");
    if (!bar || bar.dataset.msbtNavDrag === "1") return;
    bar.dataset.msbtNavDrag = "1";
    let dragId = null;

    bar.addEventListener("dragstart", (ev) => {
      const btn = ev.target && ev.target.closest && ev.target.closest("[data-tab]");
      if (!btn || btn.hidden) return;
      dragId = btn.dataset.tab;
      btn.classList.add("msbt-nav-dragging");
      try {
        ev.dataTransfer.setData("text/plain", dragId);
        ev.dataTransfer.effectAllowed = "move";
      } catch (_err) {
        /* ignore */
      }
    });
    bar.addEventListener("dragend", (ev) => {
      const btn = ev.target && ev.target.closest && ev.target.closest("[data-tab]");
      if (btn) btn.classList.remove("msbt-nav-dragging");
      dragId = null;
      bar.querySelectorAll(".msbt-nav-drag-over").forEach((n) => n.classList.remove("msbt-nav-drag-over"));
    });
    bar.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      const btn = ev.target && ev.target.closest && ev.target.closest("[data-tab]");
      bar.querySelectorAll(".msbt-nav-drag-over").forEach((n) => n.classList.remove("msbt-nav-drag-over"));
      if (btn) btn.classList.add("msbt-nav-drag-over");
    });
    bar.addEventListener("drop", (ev) => {
      ev.preventDefault();
      const target = ev.target && ev.target.closest && ev.target.closest("[data-tab]");
      bar.querySelectorAll(".msbt-nav-drag-over").forEach((n) => n.classList.remove("msbt-nav-drag-over"));
      let fromId = dragId;
      try {
        fromId = ev.dataTransfer.getData("text/plain") || dragId;
      } catch (_err) {
        /* ignore */
      }
      if (!fromId || !target || fromId === target.dataset.tab) return;
      const state = loadNavTabsState();
      const from = state.order.indexOf(fromId);
      const to = state.order.indexOf(target.dataset.tab);
      if (from < 0 || to < 0) return;
      state.order.splice(from, 1);
      state.order.splice(to, 0, fromId);
      saveNavTabsState(state);
      applyNavTabsState(state);
      refreshViewMenu();
    });

    bar.querySelectorAll("[data-tab]").forEach((btn) => {
      btn.setAttribute("draggable", "true");
    });
  }

  function initViewChrome() {
    applyTextScale(loadTextScale());
    ensureViewMenu();
    const state = loadNavTabsState();
    applyNavTabsState(state);
    enableNavTabDragReorder();
    refreshViewMenu();
  }

  // Keep a stable global hook so switchTab can force-show a hidden tab if needed.
  const originalOnTabShown = onTabShown;
  function onTabShownWrapped(tabId) {
    originalOnTabShown(tabId);
    refreshViewPanelsSection();
  }

  global.MsbtPanelLayout = {
    initAll,
    initTab,
    resetTab,
    onTabShown: onTabShownWrapped,
    persist,
    initViewChrome,
    applyTextScale,
    bumpTextScale,
    showPanel,
    hidePanel
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      try { initViewChrome(); } catch (err) { console.warn("[MSBT] view chrome init failed", err); }
    });
  } else {
    try { initViewChrome(); } catch (err) { console.warn("[MSBT] view chrome init failed", err); }
  }
})(window);
