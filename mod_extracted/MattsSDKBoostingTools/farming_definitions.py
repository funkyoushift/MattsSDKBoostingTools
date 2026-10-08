"""Experimental farming feature names and scopes; no SDK dependencies."""
FEATURES={
    'god_mode':('God Mode','local player; native damage permission'),
    'infinite_ammo':('Infinite Ammo','local player'),
    'no_reload':('No Reload','local player'),
    'instant_reload':('Instant Reload','owned weapons'),
    'no_recoil':('No Recoil / Sway','owned weapons'),
    'super_accuracy':('Super Accuracy','owned weapons'),
    'rapid_fire':('Rapid Fire','owned weapons; 99 shots/sec requested'),
    'critical_hits':('Critical Hit Boost','local player; trainer value, effect under test'),
    'skill_cooldown':('Instant Skill Cooldown','local player; resource refill'),
    'skill_duration':('Unlimited Skill Duration','local player; resource refill'),
    'grenade_cooldown':('Instant Grenade Cooldown','owned gadget; 0.1 sec on next activation'),
    'vendor_refresh':('Vendor Refresh On Close','host vendors while in use'),
    'glide_duration':('Unlimited Glide Duration','local movement; no vault-power cost while gliding'),
    'legendary_roll':('Weighted Loot High Roll','host process; native experiment, not guaranteed legendary'),
}
