from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "external_app" / "v22_parts_codes_fixed"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import external_legit_builder  # noqa: E402
import matt_editor_host  # noqa: E402


FIXTURE = {
    "name": "Daedalus Zipgun strict pistol",
    "root_key": "dad_ps",
    "parts": [
        "inv_comp:comp_05_legendary_zipgun",
        "body:part_body",
        "body_acc:part_body_a",
        "barrel:part_barrel_01_zipgun",
        "magazine:part_mag_01",
        "scope:part_scope_ironsight",
        "grip:part_grip_01",
    ],
    "level": 60,
    "seed": 2,
    "seed2": 1534,
    "expected_human": "2, 0, 1, 60| 2, 1534|| {54} {2} {3} {1} {13} {25} {42}|",
    "expected_base85": "@Uga`vnFnkbU{4Y>DRG/(vs7=j5)j/L",
}


def _fail(message: str) -> None:
    raise AssertionError(message)


def _post_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def _expect_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        _fail(f"{label} mismatch\nexpected: {expected!r}\nactual:   {actual!r}")


def _expect_contains(label: str, text: str, needle: str) -> None:
    if needle not in text:
        _fail(f"{label} did not contain {needle!r}")


def run_check() -> None:
    root_key = str(FIXTURE["root_key"])
    parts = list(FIXTURE["parts"])
    level = int(FIXTURE["level"])
    seed = int(FIXTURE["seed"])
    seed2 = int(FIXTURE["seed2"])
    expected_human = str(FIXTURE["expected_human"])
    expected_base85 = str(FIXTURE["expected_base85"])

    validation = external_legit_builder.validate(root_key, parts)
    if not validation.get("ok"):
        _fail("strict builder fixture is invalid: " + "; ".join(validation.get("errors") or []))

    built_human = external_legit_builder.build_human(root_key, parts, level=level, seed=seed, seed2=seed2)
    built_base85 = external_legit_builder.build_base85(root_key, parts, level=level, seed=seed, seed2=seed2)
    _expect_equal("strict builder human", built_human, expected_human)
    _expect_equal("strict builder base85", built_base85, expected_base85)

    url = matt_editor_host.start_editor_host().rstrip("/")
    try:
        index_html = _get_text(url + "/")
        _expect_contains("editor bootstrap", index_html, "MSBT_MATT_EDITOR_MODE")
        _expect_contains("adapter injection", index_html, "/matt_editor_adapter.js")

        adapter_js = _get_text(url + "/matt_editor_adapter.js")
        _expect_contains("adapter version", adapter_js, 'deliver-4-target-selector')

        one = _post_json(url + "/api.php", {"deserialized": expected_human})
        _expect_equal("host deserialized -> base85", one.get("serial_b85"), expected_base85)

        many = _post_json(url + "/api.php", {"deserialized_strings": [expected_human]})
        _expect_equal("host deserialized_strings -> base85", many, [expected_base85])

        decoded = _post_json(url + "/api.php", {"serial_b85": expected_base85})
        _expect_equal("host base85 -> deserialized", decoded.get("deserialized"), expected_human)

        bulk = _post_json(url + "/api.php", {"serials": [expected_base85]})
        result = (bulk.get("results") or {}).get(expected_base85) or {}
        _expect_equal("host serials success", result.get("success"), True)
        _expect_equal("host serials deserialized", result.get("deserialized"), expected_human)
    finally:
        matt_editor_host.stop_editor_host()

    print("Matt editor cross-builder check passed.")
    print(f"Fixture: {FIXTURE['name']}")
    print(f"Human: {expected_human}")
    print(f"Base85: {expected_base85}")


if __name__ == "__main__":
    try:
        run_check()
    except urllib.error.URLError as exc:
        print(f"Matt editor cross-builder check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Matt editor cross-builder check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
