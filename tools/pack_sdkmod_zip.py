"""Zip a staged sdkmod tree with CPython zipfile (oak2 zipimport-safe)."""
from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path


def pack_sdkmod(stage_root: Path, output: Path) -> Path:
    stage_root = stage_root.resolve()
    output = output.resolve()
    if not stage_root.is_dir():
        raise ValueError(f"SDK staging directory does not exist: {stage_root}")
    if output.is_relative_to(stage_root):
        raise ValueError("SDK output must be outside the staging directory")
    files = sorted(path for path in stage_root.rglob("*") if path.is_file())
    if not files:
        raise ValueError("SDK staging directory is empty")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".tmp", delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zf:
            for path in files:
                zf.write(path, path.relative_to(stage_root).as_posix())
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    packed = pack_sdkmod(Path(sys.argv[1]), Path(sys.argv[2]))
    print(packed)
