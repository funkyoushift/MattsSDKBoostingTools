"""Zip a staged sdkmod tree with CPython zipfile (oak2 zipimport-safe)."""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def pack_sdkmod(stage_root: Path, output: Path) -> Path:
    stage_root = stage_root.resolve()
    output = output.resolve()
    if output.exists():
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zf:
        for path in sorted(stage_root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(stage_root).as_posix())
    return output


if __name__ == "__main__":
    packed = pack_sdkmod(Path(sys.argv[1]), Path(sys.argv[2]))
    print(packed)
