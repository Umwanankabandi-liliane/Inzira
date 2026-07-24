#!/usr/bin/env python3
"""Upload deploy zip to Hugging Face Dataset (reliable for HF Spaces)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "deploy" / "inzira_deploy_assets.zip"
DATASET = os.getenv("INZIRA_ASSETS_HF_DATASET", "Liliane078/inzira-assets")


def main() -> int:
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        print("[FAIL] Set HF_TOKEN")
        return 1
    if not ZIP_PATH.is_file():
        print("[FAIL] Run: python scripts/package_deploy_assets.py")
        return 1

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(DATASET, repo_type="dataset", exist_ok=True)
    print(f"[upload] {ZIP_PATH.name} -> {DATASET} ...")
    api.upload_file(
        path_or_fileobj=str(ZIP_PATH),
        path_in_repo="inzira_deploy_assets.zip",
        repo_id=DATASET,
        repo_type="dataset",
        commit_message="Inzira ML models + registry bundle",
    )
    print(f"[OK] https://huggingface.co/datasets/{DATASET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
