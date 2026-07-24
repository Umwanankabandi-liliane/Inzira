#!/usr/bin/env python3
"""Download models + registry.db bundle before first production start."""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.getenv("INZIRA_DATA_DIR", str(ROOT)))
MODELS = DATA_ROOT / "models" / "bert_classifier"
REGISTRY = DATA_ROOT / "registry.db"
BUNDLED_REGISTRY = ROOT / "registry.db"
BERT_CONFIG = MODELS / "config.json"
HF_DATASET = os.getenv("INZIRA_ASSETS_HF_DATASET", "Liliane078/inzira-assets")
HF_FILENAME = "inzira_deploy_assets.zip"


def assets_ready() -> bool:
    return BERT_CONFIG.is_file()


def resolve_bundle_url(url: str) -> str:
    url = url.strip()
    file_id = None
    m = re.search(r"drive\.google\.com/file/d/([^/]+)", url)
    if m:
        file_id = m.group(1)
    else:
        m = re.search(r"[?&]id=([^&]+)", url)
        if m:
            file_id = m.group(1)
    if file_id:
        return (
            "https://drive.usercontent.google.com/download"
            f"?id={file_id}&export=download&confirm=t"
        )
    return url


def download_from_url(url: str, dest: str) -> None:
    resolved = resolve_bundle_url(url)
    with requests.get(
        resolved,
        headers={"User-Agent": "Mozilla/5.0"},
        stream=True,
        timeout=(30, 600),
    ) as resp:
        resp.raise_for_status()
        content_type = (resp.headers.get("content-type") or "").lower()
        if "text/html" in content_type:
            raise RuntimeError("Bundle URL returned HTML — check sharing is public")
        with open(dest, "wb") as out:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    out.write(chunk)


def download_from_hf(dest: str) -> None:
    from huggingface_hub import hf_hub_download

    token = os.getenv("HF_TOKEN", "").strip() or None
    print(f"[assets] Downloading from HF dataset {HF_DATASET} ...")
    path = hf_hub_download(
        repo_id=HF_DATASET,
        filename=HF_FILENAME,
        repo_type="dataset",
        token=token,
    )
    shutil.copy2(path, dest)


def safe_extract(zf: zipfile.ZipFile, dest: Path, skip_names: set[str] | None = None) -> None:
    skip = {n.lower() for n in (skip_names or set())}
    bad = zf.testzip()
    if bad:
        raise RuntimeError(f"Corrupt zip entry: {bad}")
    dest.mkdir(parents=True, exist_ok=True)
    for member in zf.infolist():
        name = member.filename.replace("\\", "/").lstrip("./")
        if not name or name.endswith("/"):
            continue
        base = Path(name).name.lower()
        if base in skip:
            print(f"[assets] skip zip entry (keep bundled): {name}")
            continue
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)


def debug_tree(root: Path, limit: int = 30) -> str:
    lines = []
    if root.exists():
        for p in sorted(root.rglob("*"))[:limit]:
            lines.append(str(p.relative_to(root)))
    return "\n  ".join(lines) or "(empty)"


def main() -> int:
    if assets_ready():
        print(f"[assets] ML models already present at {MODELS} — skip download")
        if BUNDLED_REGISTRY.is_file():
            DATA_ROOT.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUNDLED_REGISTRY, REGISTRY)
            print(f"[assets] Applied bundled registry.db from image ({BUNDLED_REGISTRY.stat().st_size} bytes)")
        return 0

    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        try:
            download_from_hf(tmp_path)
        except Exception as hf_err:
            url = os.getenv("INZIRA_ASSETS_BUNDLE_URL", "").strip()
            if not url:
                raise RuntimeError(f"HF dataset download failed: {hf_err}") from hf_err
            print(f"[assets] HF dataset failed ({hf_err}); trying Google Drive...")
            print(f"[assets] Downloading bundle from Drive...")
            download_from_url(url, tmp_path)

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if size_mb < 100:
            raise RuntimeError(f"Bundle too small ({size_mb:.1f} MB)")
        print(f"[assets] Downloaded {size_mb:.1f} MB")

        with zipfile.ZipFile(tmp_path, "r") as zf:
            print(f"[assets] Zip entries: {len(zf.namelist())}")
            # Never overwrite the shipped 300-row registry with the old asset-bundle DB.
            safe_extract(zf, DATA_ROOT, skip_names={"registry.db"})

        if not assets_ready():
            raise RuntimeError(
                f"Missing {BERT_CONFIG} after extract. Found:\n  {debug_tree(DATA_ROOT)}"
            )
        print(f"[assets] Extracted OK → {BERT_CONFIG}")
        if BUNDLED_REGISTRY.is_file():
            shutil.copy2(BUNDLED_REGISTRY, REGISTRY)
            print(f"[assets] Applied bundled registry.db from image ({BUNDLED_REGISTRY.stat().st_size} bytes)")
        elif not REGISTRY.exists():
            print("[assets] WARNING: registry.db missing after extract")
        return 0
    except Exception as e:
        print(f"[assets] Download failed: {e}", file=sys.stderr)
        return 1
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
