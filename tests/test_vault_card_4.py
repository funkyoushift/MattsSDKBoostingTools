from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "MattsSDKBoostingTools"

package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(ROOT / "mod_extracted" / PACKAGE_NAME)]
sys.modules[PACKAGE_NAME] = package

writes: list[tuple[str, object, int]] = []
economy = types.ModuleType(f"{PACKAGE_NAME}.player_economy")
economy._CURRENCY_KIND_ALIASES = {
    f"vaultcard{number}": f"VaultCard{number:02d}_Tokens"
    for number in range(1, 5)
}
economy._MAX_WALLET_AMOUNT = 2_147_483_647
economy._give_currency_on_pc = (
    lambda _pc, token, amount: writes.append(("currency", token, amount)) or True
)
economy._set_experience_level_via_bp = (
    lambda _ps, slot, level: writes.append(("experience", slot, level)) or True
)
sys.modules[economy.__name__] = economy

module_path = ROOT / "mod_extracted" / PACKAGE_NAME / "vault_card_boost.py"
spec = importlib.util.spec_from_file_location(f"{PACKAGE_NAME}.vault_card_boost", module_path)
assert spec and spec.loader
vault_card_boost = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = vault_card_boost
spec.loader.exec_module(vault_card_boost)

pc = types.SimpleNamespace(PlayerState=object())
ok, summary = vault_card_boost._economy_max_vault_cards(pc, log=lambda _message: None)

assert ok, summary
assert ("currency", "VaultCard04_Tokens", 2_147_483_647) in writes
assert ("experience", 5, 9_999_999) in writes
assert len(writes) == 8, writes

print("VAULT CARD 4 TEST PASSED")
