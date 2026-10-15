"""Package the console mod, replay library and bundled save worker."""

import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mod_extracted/MattsSDKBoostingTools"
ENTRY = ROOT / "standalone_mission_selector"
HELPERS = ROOT / "external_app/v22_parts_codes_fixed"
OUT = ROOT / "output/standalone-mission-selector"
PACKAGE = "BL4MissionSelector"
VERSION = json.loads((ROOT / "electron_poc/package.json").read_text(encoding="utf-8"))["version"]


def functions(source, names):
    """Extract unchanged function bodies and their local-function dependencies."""
    tree = ast.parse(source)
    nodes = {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    needed = set(names)
    pending = list(names)
    while pending:
        name = pending.pop()
        for node in ast.walk(nodes[name]):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in nodes
                and node.id not in needed
            ):
                needed.add(node.id)
                pending.append(node.id)
    lines = source.splitlines(keepends=True)
    return "\n\n".join(
        "".join(lines[node.lineno - 1 : node.end_lineno])
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in needed
    ), sorted(needed)


def isolate_settings(text):
    """Give the bundled core its own settings directory."""
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    for node in sorted(
        ast.walk(tree), key=lambda n: getattr(n, "lineno", 0), reverse=True
    ):
        if not isinstance(node, ast.ImportFrom) or node.module != "mods_base":
            continue
        names = [n for n in node.names if n.name == "SETTINGS_DIR"]
        if not names:
            continue
        others = [n for n in node.names if n.name != "SETTINGS_DIR"]
        indent = " " * node.col_offset
        render = lambda n: n.name + (" as " + n.asname if n.asname else "")
        replacement = (
            indent
            + "from ..runtime_paths import "
            + ", ".join(render(n) for n in names)
            + "\n"
        )
        if others:
            replacement += (
                indent
                + "from mods_base import "
                + ", ".join(render(n) for n in others)
                + "\n"
            )
        lines[node.lineno - 1 : node.end_lineno] = [replacement]
    return "".join(lines)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = {}

    def put(name, value):
        entries[PACKAGE + "/" + name] = (
            value.encode("utf-8") if isinstance(value, str) else value
        )

    for p in ENTRY.glob("*.py"):
        put(p.name, p.read_bytes())
    for p in SOURCE.iterdir():
        if (
            p.is_file()
            and p.suffix in (".py", ".json", ".yaml", ".txt")
            and p.name
            not in (
                "__init__.py",
                "backend_actions.py",
                "travel.py",
                "runtime_cleanup.py",
            )
        ):
            value = (
                p.read_text(encoding="utf-8") if p.suffix == ".py" else p.read_bytes()
            )
            if p.suffix == ".py":
                value = isolate_settings(value)
            if p.name == "camera_tick.py":
                value = value.replace(
                    'HOOK_ID = "msbt_shared_camera_tick_v1"',
                    'HOOK_ID = "bl4_mission_selector_camera_tick_v1"',
                )
                value = re.sub(
                    r"_LEGACY_HOOK_IDS = \(.*?\n\)",
                    "_LEGACY_HOOK_IDS = ()",
                    value,
                    flags=re.S,
                )
            put("core/" + p.name, value)
    put(
        "core/__init__.py",
        f'"""Private replay library; no MSBT UI, bridge or startup.\n"""\n__version__="{VERSION}"\n',
    )
    travel_source = (SOURCE / "travel.py").read_text(encoding="utf-8")
    travel, names = functions(travel_source, ["_exec_console"])
    put(
        "core/travel.py",
        'from __future__ import annotations\nfrom typing import Any\nfrom mods_base import ENGINE,get_pc\nfrom unrealsdk import find_class,logging\n_PREFIX="[Mission Selector]"\n'
        + travel
        + "\n",
    )
    backend_source = (SOURCE / "backend_actions.py").read_text(encoding="utf-8")
    backend, backend_names = functions(backend_source, ["load_character_late_join"])
    # The original helper supports guest targeting; this package is solo host.
    # Fixed host-only shims preserve its normal pause/late-join UI sequence.
    facade = """from __future__ import annotations
import json
from typing import Any
from importlib.resources import files
from .travel import _exec_console
def set_target_player(index):
    if index!=0:raise ValueError('Standalone replay requires the solo host')
def get_selected_player_index():return 0
def get_selected_player_name():return ''
def _host_player_index_value():return 0
def _selected_player_label(index,name):return 'host'
def travel_to_station(station):
    known={s['station'] for s in json.loads(files(__package__).joinpath('travelstations.json').read_text(encoding='utf-8'))['stations']}
    if station not in known:raise ValueError('Unknown authored replay station')
    _exec_console('gbx.servertraveltostation '+station)
    return dict(ok=True,message='Requested native replay station')
"""
    # Keep only the late-join helper tree. Definitions for the target shims are
    # excluded even if transitively referenced by the original entry function.
    tree = ast.parse(backend)
    lines = backend.splitlines(keepends=True)
    keep = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and (
            n.name.startswith("_late_join_")
            or n.name in ("open_late_join_ui", "load_character_late_join")
        )
    ]
    put(
        "core/backend_actions.py",
        facade
        + "\n"
        + "\n\n".join("".join(lines[n.lineno - 1 : n.end_lineno]) for n in keep)
        + "\n",
    )
    put(
        "core/runtime_cleanup.py",
        '"""No full-app travel/background feature workers in this package."""\ndef clear_travel_caches():\n    pass\n',
    )
    put("save_tools/__init__.py", "")
    helpers = (
        "mission_save_boundary.py",
        "mission_save_replay.py",
        "mission_selection_state.py",
        "mission_save_bookmarks.py",
        "mission_save_fog.py",
    )
    for name in helpers:
        text = (HELPERS / name).read_text(encoding="utf-8")
        text = re.sub(r"(?m)^from (mission_[a-z_]+) import ", r"from .\1 import ", text)
        text = re.sub(
            r"(?m)^(\s+)from (mission_[a-z_]+) import ", r"\1from .\2 import ", text
        )
        text = text.replace("import yaml", "from ._vendor import yaml").replace(
            "from yaml.tokens import", "from ._vendor.yaml.tokens import"
        )
        text = text.replace(
            "Path(__file__).with_name('mission_save_observed.yaml').read_text(encoding='utf-8')",
            "__import__('importlib.resources',fromlist=['files']).files(__package__).joinpath('mission_save_observed.yaml').read_text(encoding='utf-8')",
        )
        put("save_tools/" + name, text)
    put(
        "save_tools/mission_save_observed.yaml",
        (HELPERS / "mission_save_observed.yaml").read_bytes(),
    )
    put("save_tools/_vendor/__init__.py", "")
    import yaml

    yaml_root = Path(yaml.__file__).parent
    # Always use the vendored pure-Python implementation. A foreign global
    # yaml/_yaml extension must not become an implicit game-side dependency.
    for p in yaml_root.glob("*.py"):
        if p.name != "cyaml.py":
            put("save_tools/_vendor/yaml/" + p.name, p.read_bytes())
    distribution = importlib.metadata.distribution("PyYAML")
    license_file = next(p for p in distribution.files if str(p).endswith("/LICENSE"))
    put(
        "licenses/PyYAML-LICENSE.txt",
        distribution.locate_file(license_file).read_bytes(),
    )
    node = Path(shutil.which("node") or "")
    if not node.is_file():
        raise RuntimeError("Build machine needs Node to bundle the standalone worker")
    node_version = subprocess.check_output(
        [str(node), "-p", "process.version"], text=True
    ).strip()
    license_cache = OUT / ("node-" + node_version + "-LICENSE.txt")
    if not license_cache.exists():
        with urllib.request.urlopen(
            "https://raw.githubusercontent.com/nodejs/node/"
            + node_version
            + "/LICENSE",
            timeout=30,
        ) as response:
            license_cache.write_bytes(response.read())
    if (
        b"Node.js" not in license_cache.read_bytes()
        or b"MIT" not in license_cache.read_bytes()
    ):
        raise RuntimeError("Missing Node redistribution license")
    put("licenses/Node-LICENSE.txt", license_cache.read_bytes())
    put("worker/node.exe", node.read_bytes())
    put(
        "worker/replay_service.js",
        (ROOT / "electron_poc/save_replay_service.js").read_bytes(),
    )
    codec = (HELPERS / "matt_editor_blcrypt.js").read_text(encoding="utf-8")
    assert codec.endswith("main();\n")
    put("worker/codec.js", codec[: -len("main();\n")] + "module.exports={run};\n")
    put("worker/worker.cjs", (ENTRY / "worker.cjs").read_bytes())
    for p in [
        ROOT / "LICENSE",
        ROOT / "docs/THIRD_PARTY_NOTICES.txt",
        HELPERS / "LICENSE_GLACIERPIECE_MIT.txt",
    ]:
        put("licenses/" + p.name, p.read_bytes())
    manifest = {
        "node_version": node_version,
        "files": {
            n.split("/")[-1]: hashlib.sha256(v).hexdigest()
            for n, v in entries.items()
            if n.startswith(PACKAGE + "/worker/")
        },
    }
    put("worker_manifest.json", json.dumps(manifest, indent=2) + "\n")
    put(
        "pyproject.toml",
        f'[project]\nname="BL4MissionSelector"\nversion="{VERSION}"\n[tool.sdkmod]\nname="BL4 Mission Selector"\nversion="{VERSION}"\ncoop_support="Unknown"\n',
    )
    put("README.md", (ENTRY / "README.md").read_bytes())
    for name, value in entries.items():
        if name.endswith(".py"):
            compile(value, name, "exec")
    artifact = OUT / (PACKAGE + ".sdkmod")
    with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, value in sorted(entries.items()):
            z.writestr(name, value)
    with zipfile.ZipFile(artifact) as z:
        assert z.testzip() is None
    receipt = {
        "artifact": str(artifact),
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "bytes": artifact.stat().st_size,
        "files": len(entries),
        "node": node_version,
        "pyyaml": distribution.version,
        "travel_functions": names,
        "late_join_functions": [n.name for n in keep],
        "based_on_sdk_sha256": hashlib.sha256(
            (ROOT / "MattsSDKBoostingTools.sdkmod").read_bytes()
        ).hexdigest(),
    }
    (OUT / "build-receipt.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    print(json.dumps(receipt))
    return artifact


if __name__ == "__main__":
    build()
