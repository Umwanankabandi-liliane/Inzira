"""Background and on-demand deadline alert scanning."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import or_

from db import db_session
from deadline_scan import evaluate_deadline_alert, scan_site_deadline
from models import PushSubscription, SavedSite
from push_service import build_alert_payload, deliver_alert_to_subscriptions


def _alert_message(title: str, deadline: str, reason: str, days_left: int | None) -> tuple[str, str]:
    site = title or "Saved site"
    if reason == "new":
        return (
            f"Inzira — deadline found",
            f"{site}: {deadline}",
        )
    if reason == "changed":
        return (
            f"Inzira — deadline updated",
            f"{site}: now {deadline}",
        )
    suffix = f" ({days_left} days left)" if days_left is not None else ""
    return (
        f"Inzira — deadline soon",
        f"{site}: {deadline}{suffix}",
    )


def process_saved_site_row(
    row: SavedSite,
    now: datetime,
    entity_extractor: Callable[[str], dict] | None = None,
    send_push: bool = True,
) -> dict | None:
    row.last_deadline_check = now
    deadline = scan_site_deadline(row.url, entity_extractor=entity_extractor)
    prev = (row.last_deadline or "").strip()
    row.last_deadline = deadline or None

    reason, meta = evaluate_deadline_alert(
        prev,
        deadline,
        row.last_alert_at,
        row.last_alert_reason,
    )
    if not reason:
        return None

    title = row.title or row.domain
    days_left = meta.get("days_left") if meta else None
    alert = {
        "domain": row.domain,
        "url": row.url,
        "title": title,
        "deadline": deadline,
        "days_left": days_left,
        "reason": reason,
    }

    if send_push:
        push_title, push_body = _alert_message(title, deadline, reason, days_left)
        payload = build_alert_payload(push_title, push_body, row.url)
        with db_session() as db:
            subs = (
                db.query(PushSubscription)
                .filter(
                    PushSubscription.user_id == row.user_id,
                    PushSubscription.active.is_(True),
                )
                .all()
            )
            sent = deliver_alert_to_subscriptions(subs, payload)
            if sent:
                db_row = db.query(SavedSite).filter(SavedSite.id == row.id).one_or_none()
                if db_row:
                    db_row.last_alert_at = now
                    db_row.last_alert_reason = reason
                db.flush()
                alert["pushes_sent"] = sent

    return alert


def scan_user_saved_sites(
    user_id: int,
    limit: int = 6,
    entity_extractor: Callable[[str], dict] | None = None,
    send_push: bool = False,
) -> dict:
    alerts: list[dict] = []
    now = datetime.utcnow()
    scanned = 0
    with db_session() as db:
        rows = (
            db.query(SavedSite)
            .filter(SavedSite.user_id == user_id, SavedSite.notify_enabled.is_(True))
            .order_by(SavedSite.last_deadline_check.is_(None).desc(), SavedSite.last_deadline_check.asc())
            .limit(limit)
            .all()
        )
        scanned = len(rows)
        for row in rows:
            alert = process_saved_site_row(row, now, entity_extractor, send_push=send_push)
            if alert:
                alerts.append(alert)
        db.flush()
    return {"ok": True, "scanned": scanned, "alerts": alerts}


def run_background_alert_scan(
    batch_size: int | None = None,
    entity_extractor: Callable[[str], dict] | None = None,
) -> dict:
    """Scan due saved sites and push alerts to registered devices."""
    batch_size = batch_size or int(os.getenv("ALERT_SCAN_BATCH_SIZE", "20"))
    min_gap = int(os.getenv("ALERT_SCAN_INTERVAL_MINUTES", "30"))
    cutoff = datetime.utcnow() - timedelta(minutes=max(min_gap - 5, 10))
    now = datetime.utcnow()
    scanned = 0
    alerts = 0
    pushes = 0

    with db_session() as db:
        rows = (
            db.query(SavedSite)
            .filter(
                SavedSite.notify_enabled.is_(True),
                or_(
                    SavedSite.last_deadline_check.is_(None),
                    SavedSite.last_deadline_check < cutoff,
                ),
            )
            .order_by(SavedSite.last_deadline_check.is_(None).desc(), SavedSite.last_deadline_check.asc())
            .limit(batch_size)
            .all()
        )
        for row in rows:
            scanned += 1
            alert = process_saved_site_row(row, now, entity_extractor, send_push=True)
            if alert:
                alerts += 1
                pushes += int(alert.get("pushes_sent") or 0)
        db.flush()

    summary = {"scanned": scanned, "alerts": alerts, "pushes_sent": pushes}
    if scanned:
        print(f"Alert scan: {summary}")
    return summary
