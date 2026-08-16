(function exposePollCoordinator(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.MsbtPollCoordinator = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function createPollCoordinatorApi() {
  const DEFAULT_DELAYS = Object.freeze({
    active: 1250,
    idle: 4000,
    hidden: 8000
  });

  function pollDelay({ hidden = false, active = false } = {}, delays = DEFAULT_DELAYS) {
    if (hidden) return Number(delays.hidden) || DEFAULT_DELAYS.hidden;
    if (active) return Number(delays.active) || DEFAULT_DELAYS.active;
    return Number(delays.idle) || DEFAULT_DELAYS.idle;
  }

  function stableFingerprint(value) {
    const seen = new WeakSet();
    const normalize = (item) => {
      if (item === null || typeof item !== "object") return item;
      if (seen.has(item)) return "[Circular]";
      seen.add(item);
      if (Array.isArray(item)) return item.map(normalize);
      const out = {};
      Object.keys(item).sort().forEach((key) => {
        const field = item[key];
        if (field !== undefined && typeof field !== "function") out[key] = normalize(field);
      });
      return out;
    };
    return JSON.stringify(normalize(value));
  }

  function serialDeliveryFingerprint(progress) {
    const value = progress && typeof progress === "object" ? progress : {};
    return stableFingerprint({
      active: Boolean(value.active),
      complete: Boolean(value.complete),
      current: value.current ?? value.delivered ?? null,
      total: value.total ?? null,
      failed: value.failed ?? null,
      message: value.message || value.status || ""
    });
  }

  return {
    DEFAULT_DELAYS,
    pollDelay,
    serialDeliveryFingerprint,
    stableFingerprint
  };
});
