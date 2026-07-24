"""Shared ML model singleton — import once per process before parallel harvest workers."""
from __future__ import annotations

import threading

_lock = threading.Lock()
_loaded = False


def ensure_models_loaded() -> None:
    """Load BERT / RoBERTa / spaCy / RF exactly once (thread-safe)."""
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        import main  # noqa: F401 — triggers model load at import time
        _loaded = True
