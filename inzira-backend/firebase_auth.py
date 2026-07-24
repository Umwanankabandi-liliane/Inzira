import json
import os
import time
from functools import lru_cache
from typing import Optional, Tuple

import jwt
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend

import firebase_admin
from firebase_admin import auth, credentials

_KEYS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
_KEY_CACHE: dict[str, object] = {"keys": None, "ts": 0.0}
_KEY_CACHE_SEC = 3600


def _admin_configured() -> bool:
    return bool(
        os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
        or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    )


def firebase_project_id() -> str:
    pid = os.getenv("INZIRA_FIREBASE_PROJECT_ID", "").strip()
    if pid:
        return pid
    if _admin_configured():
        _init_firebase()
        return firebase_admin.get_app().project_id
    # Default for local dev — must match web/index.html Firebase projectId
    return "inzira-52474"


@lru_cache(maxsize=1)
def _init_firebase() -> None:
    if firebase_admin._apps:
        return

    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()

    cred = None
    if sa_json:
        cred = credentials.Certificate(json.loads(sa_json))
    elif sa_path:
        cred = credentials.Certificate(sa_path)
    else:
        raise RuntimeError(
            "Firebase Admin is not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON "
            "(full JSON) or FIREBASE_SERVICE_ACCOUNT_PATH (path to JSON)."
        )

    firebase_admin.initialize_app(cred)


def _fetch_public_keys() -> dict:
    now = time.time()
    cached = _KEY_CACHE.get("keys")
    if cached and now - float(_KEY_CACHE.get("ts") or 0) < _KEY_CACHE_SEC:
        return cached
    res = requests.get(_KEYS_URL, timeout=10)
    res.raise_for_status()
    keys = res.json()
    _KEY_CACHE["keys"] = keys
    _KEY_CACHE["ts"] = now
    return keys


def _public_key_from_google_cert(cert_pem: str):
    data = cert_pem.encode() if isinstance(cert_pem, str) else cert_pem
    cert = x509.load_pem_x509_certificate(data, default_backend())
    return cert.public_key()


def _verify_with_public_keys(id_token: str) -> dict:
    project_id = firebase_project_id()
    header = jwt.get_unverified_header(id_token)
    kid = header.get("kid")
    keys = _fetch_public_keys()
    if not kid or kid not in keys:
        raise ValueError(f"Invalid Firebase token key (kid={kid!r})")
    public_key = _public_key_from_google_cert(keys[kid])
    decoded = jwt.decode(
        id_token,
        public_key,
        algorithms=["RS256"],
        audience=project_id,
        issuer=f"https://securetoken.google.com/{project_id}",
        leeway=60,
    )
    decoded["uid"] = decoded.get("user_id") or decoded.get("sub")
    return decoded


def verify_id_token(id_token: str) -> dict:
    token = (id_token or "").strip()
    if not token:
        raise ValueError("Empty token")
    if _admin_configured():
        _init_firebase()
        return auth.verify_id_token(token)
    return _verify_with_public_keys(token)


def extract_identity(decoded: dict) -> Tuple[str, Optional[str], Optional[str]]:
    uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
    if not uid:
        raise ValueError("Missing Firebase uid")

    email = decoded.get("email")
    phone = decoded.get("phone_number")
    return uid, email, phone


def delete_firebase_user(uid: str) -> None:
    if not _admin_configured():
        raise RuntimeError("Firebase Admin required to delete auth users")
    _init_firebase()
    auth.delete_user(uid)
