#!/usr/bin/env python3
"""Create a Linux-friendly deploy zip (models + registry.db)."""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deploy" / "inzira_deploy_assets.zip"


def add_dir(zf: zipfile.ZipFile, folder: Path, arc_prefix: str) -> int:
    count = 0
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            arc = f"{arc_prefix}/{path.relative_to(folder).as_posix()}"
            zf.write(path, arc)
            count += 1
    return count


def main() -> int:
    models = ROOT / "models"
    registry = ROOT / "registry.db"
    if not models.is_dir() or not registry.is_file():
        print("[FAIL] Need models/ and registry.db in inzira-backend/")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    files = 0
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        files += add_dir(zf, models, "models")
        zf.write(registry, "registry.db")
        files += 1

    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"[OK] {OUT} — {files} files, {size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
