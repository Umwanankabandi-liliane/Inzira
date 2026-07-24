"""
MIFOTRA staff portal — separate from youth Firebase accounts.

Youth: register in the app with personal email (Firebase).
Staff: @mifotra.gov.rw email + institution password (backend only, never replaces youth session).
"""

import os
import secrets
import time
from typing import List, Optional, Tuple

from config import is_production

SESSION_TTL_SECONDS = 8 * 60 * 60  # 8 hours
_sessions: dict[str, float] = {}


def allowed_domains() -> List[str]:
    raw = os.getenv("INZIRA_MIFOTRA_EMAIL_DOMAINS", "mifotra.gov.rw").strip()
    if not raw:
        return []
    return [d.strip().lower().lstrip("@") for d in raw.split(",") if d.strip()]


def _staff_password() -> str:
    return os.getenv("INZIRA_MIFOTRA_STAFF_PASSWORD", "").strip()


def staff_auth_required() -> bool:
    return bool(allowed_domains()) and bool(_staff_password())


def is_staff_email(email: Optional[str]) -> bool:
    domains = allowed_domains()
    if not domains:
        return True
    if not email or "@" not in email:
        return False
    domain = email.strip().lower().split("@")[-1]
    return domain in domains


def verify_staff_login(email: str, password: str) -> bool:
    """Institution login — independent of youth Firebase accounts."""
    if not is_staff_email(email):
        return False
    expected = _staff_password()
    if not expected:
        return not is_production()  # dev only: domain check without password
    return secrets.compare_digest((password or "").strip(), expected)


def create_session() -> Tuple[str, int]:
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time() + SESSION_TTL_SECONDS
    return token, SESSION_TTL_SECONDS


def validate_session(token: Optional[str]) -> bool:
    if not staff_auth_required():
        return True
    if not token or not token.strip():
        return False
    expiry = _sessions.get(token.strip())
    if not expiry:
        return False
    if time.time() > expiry:
        _sessions.pop(token.strip(), None)
        return False
    return True


def revoke_session(token: Optional[str]) -> None:
    if token:
        _sessions.pop(token.strip(), None)
