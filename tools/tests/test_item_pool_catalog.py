"""Item Pool Spawning catalog completeness for cooked pearl pools."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_POOLS = ROOT / "docs" / "data" / "item_pools.json"
RES_POOLS = ROOT / "external_app" / "v22_parts_codes_fixed" / "resources" / "item_pools.json"
MOD_POOLS = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "item_pools.json"
SPAWNING = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "item_pool_spawning.py"
JS = ROOT / "electron_poc" / "renderer.js"
HTML = ROOT / "electron_poc" / "renderer.html"
MOBILE = ROOT / "mobile_controller" / "app" / "src" / "main" / "assets" / "app.js"

COOKED_PEARL_POOLS = (
    "itempool_ar_06_pearl",
    "itempool_ps_06_pearl",
    "itempool_sm_06_pearl",
    "itempool_sg_06_pearl",
    "itempool_sr_06_pearl",
    "itempool_vla_sm_06_pearl_Locust_shiny",
)


def _load_pools(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), f"{path} must be a JSON list"
    return data


def _pool_ids(rows: list[dict]) -> set[str]:
    return {str(row.get("itempool") or "").strip() for row in rows}


def test_picker_catalogs_include_cooked_pearl_pools():
    for path in (DOCS_POOLS, RES_POOLS, MOD_POOLS):
        ids = _pool_ids(_load_pools(path))
        missing = [pool for pool in COOKED_PEARL_POOLS if pool not in ids]
        assert not missing, f"{path.name} missing pearl pools: {missing}"


def test_item_pool_catalog_copies_match():
    docs = _load_pools(DOCS_POOLS)
    assert docs == _load_pools(RES_POOLS)
    assert docs == _load_pools(MOD_POOLS)


def test_electron_item_pool_picker_lists_every_filtered_pool():
    js = JS.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    assert "function itemPoolIsPearl" in js
    assert 'category === "Pearl"' in js
    assert "state.filteredItemPools.forEach" in js
    assert "state.filteredItemPools.slice(0, 400)" not in js
    assert 'placeholder="pearl, shield, sniper, class mod..."' in html
    assert 'id="tab-item-pool"' in html
    assert 'id="itempoolCategory"' in html


def test_sdk_and_mobile_item_pool_filters_keep_pearls_visible():
    spawning = SPAWNING.read_text(encoding="utf-8")
    mobile = MOBILE.read_text(encoding="utf-8")
    assert "def item_pool_is_pearl" in spawning
    assert "'Pearl'" in spawning
    assert "limit: int = 0" in spawning
    start = mobile.index("function renderPools")
    end = mobile.index("async function loadPoolCatalog")
    pool_render = mobile[start:end]
    assert "function renderPools" in pool_render
    assert ".slice(0,300)" not in pool_render
    assert "filtered.forEach" in pool_render
