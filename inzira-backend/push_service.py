"""Web Push (VAPID) and Firebase Cloud Messaging delivery."""

from __future__ import annotations

import json
import os
from typing import Iterable

from models import PushSubscription

_vapid_warned = False


def vapid_public_key() -> str:
    return os.getenv("INZIRA_VAPID_PUBLIC_KEY", "").strip()


def vapid_private_key() -> str:
    raw = os.getenv("INZIRA_VAPID_PRIVATE_KEY", "").strip()
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    return raw.replace("\\n", "\n")


def vapid_configured() -> bool:
    return bool(vapid_public_key() and vapid_private_key())


def _vapid_claims() -> dict:
    email = os.getenv("INZIRA_VAPID_CLAIMS_EMAIL", "mailto:alerts@inzira.rw").strip()
    return {"sub": email}


def build_alert_payload(title: str, body: str, url: str = "/#/followed") -> dict:
    return {
        "title": title,
        "body": body,
        "url": url,
        "icon": "/assets/icons/icon-192.svg",
    }


def send_web_push(sub: PushSubscription, payload: dict) -> bool:
    global _vapid_warned
    if not vapid_configured():
        if not _vapid_warned:
            print("Web push skipped: set INZIRA_VAPID_PUBLIC_KEY and INZIRA_VAPID_PRIVATE_KEY in .env")
            _vapid_warned = True
        return False
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        if not _vapid_warned:
            print("Web push skipped: install pywebpush")
            _vapid_warned = True
        return False

    subscription_info = {
        "endpoint": sub.endpoint,
        "keys": {
            "p256dh": sub.p256dh or "",
            "auth": sub.auth_secret or "",
        },
    }
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key(),
            vapid_claims=_vapid_claims(),
            ttl=86400,
        )
        return True
    except WebPushException as e:
        status = getattr(e.response, "status_code", None) if e.response is not None else None
        if status in (404, 410):
            sub.active = False
        print(f"Web push failed ({status}): {e}")
        return False
    except Exception as e:
        print(f"Web push error: {e}")
        return False


def send_fcm_push(sub: PushSubscription, payload: dict) -> bool:
    try:
        from firebase_auth import _admin_configured, _init_firebase
        from firebase_admin import messaging
    except Exception as e:
        print(f"FCM import error: {e}")
        return False

    if not _admin_configured():
        print("FCM push skipped: Firebase service account not configured")
        return False

    try:
        _init_firebase()
        message = messaging.Message(
            notification=messaging.Notification(
                title=payload.get("title", "Inzira"),
                body=payload.get("body", ""),
            ),
            data={
                "url": payload.get("url", "/"),
                "title": payload.get("title", "Inzira"),
                "body": payload.get("body", ""),
            },
            token=sub.endpoint,
        )
        messaging.send(message)
        return True
    except Exception as e:
        err = str(e).lower()
        if "not-found" in err or "registration-token-not-registered" in err:
            sub.active = False
        print(f"FCM push error: {e}")
        return False


def deliver_alert_to_subscriptions(subs: Iterable[PushSubscription], payload: dict) -> int:
    sent = 0
    for sub in subs:
        if not sub.active:
            continue
        ok = False
        if sub.channel == "web":
            ok = send_web_push(sub, payload)
        elif sub.channel == "fcm":
            ok = send_fcm_push(sub, payload)
        if ok:
            sent += 1
    return sent
