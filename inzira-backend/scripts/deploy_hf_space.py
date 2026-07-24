#!/usr/bin/env python3
"""Upload inzira-backend to Hugging Face Space and set secrets from .env."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

SPACE = os.getenv("HF_SPACE_ID", "Liliane078/inzira")
TOKEN = os.getenv("HF_TOKEN", "").strip()
SUBTREE_BRANCH = "hf-deploy-split"
COMMIT_MSG = (
    "Fix My Matches: enforce field of interest as hard filter, "
    "fix ICT/district word-boundary bug, add honest empty state"
)

IGNORE = [
    ".venv/**",
    "**/__pycache__/**",
    ".pytest_cache/**",
    "models/**",
    "deploy/*.zip",
    ".env",
    "inzira_local.db",
    "harvest_log*.txt",
    ".git/**",
    "notebooks/**",
    "tests/**",
    "pytest-cache-files-*/**",
]

SECRETS = [
    ("INZIRA_ENV", "production"),
    ("INZIRA_FIREBASE_PROJECT_ID", "inzira-52474"),
    ("GROQ_MODEL", "llama-3.1-8b-instant"),
    ("INZIRA_MIFOTRA_EMAIL_DOMAINS", "mifotra.gov.rw"),
    ("INZIRA_VAPID_CLAIMS_EMAIL", "mailto:alerts@inzira.rw"),
    ("DATABASE_URL", "sqlite:////tmp/inzira/inzira_prod.db"),
    ("INZIRA_DATA_DIR", "/tmp/inzira"),
    ("INZIRA_ASSETS_HF_DATASET", "Liliane078/inzira-assets"),
    ("HF_TOKEN", None),
    ("GROQ_API_KEY", None),
    ("INZIRA_MIFOTRA_STAFF_PASSWORD", None),
    ("INZIRA_VAPID_PUBLIC_KEY", None),
    ("INZIRA_VAPID_PRIVATE_KEY", None),
    ("INZIRA_ASSETS_BUNDLE_URL", None),
    ("CORS_ORIGINS", "https://liliane078-inzira.hf.space"),
    # Optional — enables firebase_admin + FCM. Prefer JSON secret on Space.
    ("FIREBASE_SERVICE_ACCOUNT_JSON", None),
]


def _registry_ok() -> bool:
    reg = ROOT / "registry.db"
    if not reg.is_file():
        print(f"[FAIL] Missing {reg}")
        return False
    mb = reg.stat().st_size / (1024 * 1024)
    print(f"[OK] registry.db present ({mb:.1f} MB)")
    return True


def deploy_via_api() -> int:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("[FAIL] pip install huggingface_hub")
        return 1

    api = HfApi(token=TOKEN)
    print(f"[upload] HF API -> Space {SPACE} (includes registry.db, no models/)...")
    api.upload_folder(
        folder_path=str(ROOT),
        repo_id=SPACE,
        repo_type="space",
        ignore_patterns=IGNORE,
        commit_message=COMMIT_MSG,
    )
    print("[OK] Code uploaded via HF API.")
    return 0


def deploy_via_git_subtree() -> int:
    """Push inzira-backend/ as Space root (uses git HTTPS credential manager)."""
    hf_url = f"https://huggingface.co/spaces/{SPACE}"
    print(f"[upload] Git subtree: inzira-backend/ -> Space root ({SPACE})...")

    subprocess.run(
        ["git", "remote", "set-url", "hf", hf_url],
        cwd=REPO_ROOT,
        check=True,
    )
    split = subprocess.run(
        ["git", "subtree", "split", "--prefix=inzira-backend", "-b", SUBTREE_BRANCH],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if split.returncode != 0:
        print("[FAIL] git subtree split:", split.stderr or split.stdout)
        return 1

    push = subprocess.run(
        ["git", "push", "hf", f"{SUBTREE_BRANCH}:main", "--force-with-lease"],
        cwd=REPO_ROOT,
    )
    if push.returncode != 0:
        print("[FAIL] git push hf (subtree). Check HTTPS credentials.")
        return 1

    print("[OK] Subtree pushed to Space main.")
    return 0


def set_secrets() -> int:
    if not TOKEN:
        print("[WARN] HF_TOKEN not set — skipping secret sync (Space may already have them).")
        return 0

    try:
        from huggingface_hub import HfApi
    except ImportError:
        return 0

    api = HfApi(token=TOKEN)
    print("[secrets] Syncing Space secrets...")
    for key, default in SECRETS:
        val = (os.getenv(key) or default or "").strip()
        if not val:
            print(f"  [WARN] skip {key} — missing in .env")
            continue
        api.add_space_secret(repo_id=SPACE, key=key, value=val)
        print(f"  [OK] {key}")
    return 0


def main() -> int:
    if not _registry_ok():
        return 1

    if TOKEN:
        rc = deploy_via_api()
    else:
        print("[info] HF_TOKEN not set — using git subtree push (Windows credential manager).")
        rc = deploy_via_git_subtree()

    if rc != 0:
        return rc

    set_secrets()

    print("")
    print("Done!")
    print("  Space:  https://huggingface.co/spaces/Liliane078/inzira")
    print("  Live:   https://liliane078-inzira.hf.space")
    print("  Health: https://liliane078-inzira.hf.space/health")
    print("")
    print("Watch build logs on the Space page (rebuild ~5–15 min).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
