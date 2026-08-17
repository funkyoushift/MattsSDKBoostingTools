(function attachListSelection(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.MsbtListSelection = api;
})(typeof window !== "undefined" ? window : globalThis, function createListSelection() {
  /**
   * Resolve the click gesture into selection flags. "Select Multiple" mode makes a
   * plain click behave like a Ctrl/Cmd click so modifier keys stay optional.
   */
  function selectionGestureFlags(options = {}) {
    const multiSelect = Boolean(options.multiSelect);
    return {
      toggle: multiSelect || Boolean(options.ctrlKey) || Boolean(options.metaKey),
      shift: Boolean(options.shiftKey)
    };
  }

  function applySelectionGesture(options = {}) {
    const orderedKeys = Array.isArray(options.orderedKeys) ? options.orderedKeys.map(String) : [];
    const key = String(options.key || "");
    const selected = new Set(Array.from(options.selected || []).map(String));
    const toggle = Boolean(options.toggle);
    const shift = Boolean(options.shift);
    const anchor = String(options.anchor || "");
    if (!key || !orderedKeys.includes(key)) return { selected, anchor };

    if (shift && anchor && orderedKeys.includes(anchor)) {
      const from = orderedKeys.indexOf(anchor);
      const to = orderedKeys.indexOf(key);
      const range = orderedKeys.slice(Math.min(from, to), Math.max(from, to) + 1);
      if (!toggle) selected.clear();
      range.forEach((value) => selected.add(value));
      return { selected, anchor };
    }

    if (toggle) {
      if (selected.has(key)) selected.delete(key);
      else selected.add(key);
    } else {
      selected.clear();
      selected.add(key);
    }
    return { selected, anchor: key };
  }

  return { applySelectionGesture, selectionGestureFlags };
});
