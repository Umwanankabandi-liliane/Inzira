#!/usr/bin/env python3
"""Verify local Inzira backend configuration. Run from inzira-backend/."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

OK = "[OK]"
WARN = "[!!]"
FAIL = "[XX]"


def check(name: str, ok: bool, detail: str = "", *, required: bool = True) -> bool:
    if not ok and not required:
        tag = WARN
    else:
        tag = OK if ok else FAIL
    line = f"{tag} {name}"
    if detail:
        line += f" — {detail}"
    if not ok and not required:
        line += " (optional)"
    print(line)
    return ok if required else True


def main() -> int:
    print("Inzira local setup check\n")

    env_path = ROOT / ".env"
    if not env_path.exists():
        print(f"{FAIL} .env missing — copy .env.example to .env and fill in values")
        return 1

    results = []
    results.append(check(".env exists", True))

    db_url = os.getenv("DATABASE_URL", "").strip()
    results.append(check("DATABASE_URL set", bool(db_url), db_url[:40] + "..." if len(db_url) > 40 else db_url))

    if db_url:
        try:
            from sqlalchemy import text
            from db import db_session
            with db_session() as db:
                db.execute(text("SELECT 1"))
            label = "SQLite database" if db_url.startswith("sqlite") else "PostgreSQL connection"
            results.append(check(label, True))
        except Exception as e:
            results.append(check("Database connection", False, str(e)))

        try:
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            cfg = Config(str(ROOT / "alembic.ini"))
            script = ScriptDirectory.from_config(cfg)
            head = script.get_current_head()
            if not db_url.startswith("sqlite"):
                results.append(check("Alembic migrations defined", bool(head), f"head={head}"))
                print("    Run: alembic -c alembic.ini upgrade head")
            else:
                results.append(check("SQLite dev DB", True, "tables created on server start"))
        except Exception as e:
            results.append(check("Alembic", False, str(e), required=not db_url.startswith("sqlite")))

    sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    project_id = os.getenv("INZIRA_FIREBASE_PROJECT_ID", "").strip()
    firebase_admin_ok = bool(sa_json) or (sa_path and Path(sa_path).exists())
    results.append(check(
        "Firebase Admin (optional)",
        firebase_admin_ok,
        sa_path if sa_path else ("JSON in env" if sa_json else "JWT verify works without it"),
        required=False,
    ))
    results.append(check(
        "Firebase project ID",
        bool(project_id),
        project_id or "set INZIRA_FIREBASE_PROJECT_ID",
    ))
    try:
        from firebase_auth import firebase_project_id
        firebase_project_id()
        results.append(check("Firebase token verification", True))
    except Exception as e:
        results.append(check("Firebase token verification", False, str(e)))

    groq = os.getenv("GROQ_API_KEY", "").strip()
    results.append(check("GROQ_API_KEY set (Assistant)", bool(groq and groq != "your_groq_api_key_here")))

    mifotra = os.getenv("INZIRA_MIFOTRA_STAFF_PASSWORD", "").strip()
    results.append(check("MIFOTRA staff password set", bool(mifotra)))

    index_html = ROOT / "web" / "index.html"
    if index_html.exists():
        text = index_html.read_text(encoding="utf-8")
        web_fb = "YOUR_API_KEY" not in text and "inzira-52474" in text
        results.append(check("Firebase web config in index.html", web_fb))

    reg = ROOT / "registry.db"
    results.append(check("registry.db present", reg.exists(), str(reg) if reg.exists() else "run build_registry if needed"))

    print()
    if all(results):
        print("All checks passed. Start server: python main.py")
        print("Open: http://localhost:8000")
        print("Production deploy: see docs/DEPLOYMENT.md then run python scripts/validate_production.py")
        return 0
    print("Fix failed items above, then re-run: python scripts/check_setup.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
