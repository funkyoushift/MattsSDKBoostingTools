/**
 * Lightweight Hoard favorites helper tests (no Electron).
 * Run: node electron_poc/test_hoard_favorites.js
 */
function normalizeHoardFavoriteName(name) {
  return String(name || "").trim().replace(/\s+/g, " ").slice(0, 64);
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}

assert(normalizeHoardFavoriteName("  Boss   Ring  ") === "Boss Ring", "collapse spaces");
assert(normalizeHoardFavoriteName("x".repeat(80)).length === 64, "cap length");
assert(normalizeHoardFavoriteName("   ") === "", "empty after trim");

console.log("hoard favorites helpers passed");
