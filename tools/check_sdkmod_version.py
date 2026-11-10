from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


def check(root: Path) -> list[str]:
    source = root / "mod_extracted/MattsSDKBoostingTools/__init__.py"
    pyproject = root / "mod_extracted/MattsSDKBoostingTools/pyproject.toml"
    package = root / "electron_poc/package.json"
    latest = root / "docs/releases/latest.json"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in {"__version__", "__version_info__"}:
                values[node.target.id] = ast.literal_eval(node.value)
    if not isinstance(values.get("__version__"), str):
        raise ValueError("SDK __init__.py is missing a literal __version__ string")
    if not isinstance(values.get("__version_info__"), tuple):
        raise ValueError("SDK __init__.py is missing a literal __version_info__ tuple")
    sdk_version = values["__version__"]
    version_info = values["__version_info__"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", sdk_version):
        raise ValueError(f"Unsupported SDK semantic version: {sdk_version!r}")
    sdk_tuple = tuple(int(part) for part in sdk_version.split("."))
    mismatches = []
    if version_info != sdk_tuple:
        mismatches.append(f"__version_info__={version_info!r} does not match __version__={sdk_version}")
    toml_text = pyproject.read_text(encoding="utf-8-sig")
    match = re.search(r"(?m)^version\s*=\s*['\"]([^'\"]+)['\"]", toml_text)
    if not match:
        raise ValueError("SDK pyproject.toml is missing its project version")
    versions = {
        "SDK __version__": sdk_version,
        "SDK pyproject": match.group(1),
        "Electron package": json.loads(package.read_text(encoding="utf-8-sig"))["version"],
    }
    release = json.loads(latest.read_text(encoding="utf-8-sig"))
    for key in ("package_version", "app_version", "sdkmod_version", "resources_version", "electron_version"):
        versions[f"release metadata {key}"] = release.get(key)
    expected = versions["Electron package"]
    mismatches.extend(f"{name}={version!r} does not match Electron package={expected}" for name, version in versions.items() if version != expected)
    return mismatches


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    mismatches = check(root)
    if mismatches:
        for mismatch in mismatches:
            print(f"ERROR {mismatch}", file=sys.stderr)
        return 1
    print("SDK and public release version metadata are in lockstep.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
