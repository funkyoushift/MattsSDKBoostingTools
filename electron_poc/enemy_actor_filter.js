(function attachEnemyActorFilter(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.MsbtEnemyActorFilter = api;
})(typeof window !== "undefined" ? window : globalThis, function createEnemyActorFilter() {
  const NON_ENEMY_PATTERN = /(?:^|[_\s|.-])(?:audio|payload|gadget|turret|projectile|grenade|pickup|loot|door|switch|vehicle|mount|climb|grapple|deco|cinematic|vfx|fx|prop|placeable|damageable|interactive|travel|station|mission|quest|player|hologram|friendly|civilian|pet|companion|dummy|test)(?:$|[_\s|.-])/i;
  const NPC_PATTERN = /(?:^|_)char_npc(?:_|$)/i;
  const CHARACTER_PREFIX_PATTERN = /^(?:char|testchar|ai)_/i;
  const HARD_EXCLUDE_PATTERN = /audio|payload|gadget|turret|hologram|friendly|civilian|companion/i;

  function isEnemyActor(actorName, catalog = {}) {
    const name = String(actorName || "").trim();
    if (!name) return false;
    const metadata = catalog.actor_metadata && catalog.actor_metadata[name] || {};
    const display = String(catalog.display_names && catalog.display_names[name] || "");
    const reference = String(metadata.reference_display_name || "");
    const searchable = `${name} ${display} ${reference}`;
    if (HARD_EXCLUDE_PATTERN.test(searchable) || NON_ENEMY_PATTERN.test(searchable)) return false;
    if (metadata.is_boss === true || metadata.is_true_boss === true) return true;

    const characters = catalog.categories && catalog.categories.Characters;
    if (!Array.isArray(characters) || !characters.includes(name)) return false;
    if (!CHARACTER_PREFIX_PATTERN.test(name)) return false;

    if (/^(?:char_ai|ai_ai|testchar)$/i.test(name)) return false;
    if (NPC_PATTERN.test(name)) return false;
    return true;
  }

  function filterEnemyActors(actorNames, catalog = {}) {
    return (Array.isArray(actorNames) ? actorNames : []).filter((name) => isEnemyActor(name, catalog));
  }

  return { isEnemyActor, filterEnemyActors };
});
