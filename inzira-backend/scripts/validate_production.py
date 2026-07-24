#!/usr/bin/env python3
"""Validate production environment before deploy. Exit 1 if blockers found."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def req(name: str, ok: bool, hint: str = "") -> bool:
    tag = OK if ok else FAIL
    line = f"{tag} {name}"
    if hint:
        line += f" — {hint}"
    print(line)
    return ok


def opt(name: str, ok: bool, hint: str = "") -> None:
    tag = OK if ok else WARN
    line = f"{tag} {name} (optional)"
    if hint:
        line += f" — {hint}"
    print(line)


def main() -> int:
    print("Inzira production readiness\n")

    results = []
    prod = os.getenv("INZIRA_ENV", "").lower() in ("production", "prod")
    results.append(req("INZIRA_ENV=production", prod, "set on hosting platform"))

    db = os.getenv("DATABASE_URL", "").strip()
    results.append(req("DATABASE_URL (PostgreSQL)", bool(db) and not db.startswith("sqlite")))

    groq = os.getenv("GROQ_API_KEY", "").strip()
    results.append(req("GROQ_API_KEY", bool(groq and "your_groq" not in groq)))

    pid = os.getenv("INZIRA_FIREBASE_PROJECT_ID", "").strip()
    results.append(req("INZIRA_FIREBASE_PROJECT_ID", bool(pid)))

    mifotra = os.getenv("INZIRA_MIFOTRA_STAFF_PASSWORD", "").strip()
    results.append(req("INZIRA_MIFOTRA_STAFF_PASSWORD", bool(mifotra)))

    cors = os.getenv("CORS_ORIGINS", "").strip()
    results.append(req("CORS_ORIGINS (not *)", bool(cors) and cors != "*"))

    vapid = bool(os.getenv("INZIRA_VAPID_PUBLIC_KEY", "").strip())
    results.append(req("VAPID keys (push)", vapid))

    models = (ROOT / "models" / "bert_classifier").is_dir()
    bundle = os.getenv("INZIRA_ASSETS_BUNDLE_URL", "").strip()
    results.append(req(
        "ML models on disk or bundle URL",
        models or bool(bundle),
        "run package_deploy_assets.ps1 then upload zip" if not models else "",
    ))

    registry = (ROOT / "registry.db").exists()
    results.append(req("registry.db", registry, "included in assets bundle"))

    sa = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip() or os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", ""
    ).strip()
    opt("Firebase Admin service account", bool(sa), "needed for account deletion")

    print()
    if all(results):
        print("Ready for production deploy.")
        return 0
    print("Fix [FAIL] items above, then re-run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
