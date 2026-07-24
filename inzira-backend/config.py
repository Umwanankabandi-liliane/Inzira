"""Shared environment helpers for local and production."""

from __future__ import annotations

import os


def normalize_database_url(url: str) -> str:
    """Render/Heroku use postgres://; SQLAlchemy 2 needs postgresql://."""
    u = (url or "").strip()
    if u.startswith("postgres://"):
        return "postgresql://" + u[len("postgres://") :]
    return u


def database_url() -> str:
    raw = os.getenv("DATABASE_URL", "").strip()
    if raw:
        return normalize_database_url(raw)
    return "sqlite:///./inzira_local.db"


def is_production() -> bool:
    return os.getenv("INZIRA_ENV", "").strip().lower() in ("production", "prod")


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if is_production():
        if not raw or raw == "*":
            return []  # block open CORS in production when unset
        return [o.strip() for o in raw.split(",") if o.strip()]
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def server_port(default: int = 8000) -> int:
    raw = os.getenv("PORT", "").strip()
    if raw.isdigit():
        return int(raw)
    return default
