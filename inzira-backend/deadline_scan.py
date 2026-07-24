"""Lightweight deadline scanning for saved-site alert jobs."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup

from rwanda_sources import domain_of

_DEADLINE_SCAN_CACHE: dict[str, tuple[float, str]] = {}
_DEADLINE_CACHE_SEC = 300
_DEADLINE_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def fetch_page_text(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split()[:400])
    except Exception:
        return ""


def parse_deadline_date(text: str) -> Optional[date]:
    if not text:
        return None
    raw = text.strip()
    low = raw.lower()
    if any(x in low for x in ("rolling", "ongoing", "open until filled", "no deadline", "tbd")):
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", raw)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        for day, month in ((a, b), (b, a)):
            try:
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(y, month, day)
            except ValueError:
                continue
    m = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
        low,
    )
    if m:
        month = _DEADLINE_MONTHS.get(m.group(1))
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(2)))
            except ValueError:
                pass
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})",
        low,
    )
    if m:
        month = _DEADLINE_MONTHS.get(m.group(2))
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(1)))
            except ValueError:
                pass
    return None


def scan_site_deadline(url: str, entity_extractor: Callable[[str], dict] | None = None) -> str:
    dom = domain_of(url)
    now = datetime.utcnow().timestamp()
    if dom and dom in _DEADLINE_SCAN_CACHE:
        ts, cached = _DEADLINE_SCAN_CACHE[dom]
        if now - ts < _DEADLINE_CACHE_SEC:
            return cached
    text = fetch_page_text(url)
    deadline = ""
    if text:
        if entity_extractor:
            try:
                deadline = entity_extractor(text).get("deadline", "") or ""
            except Exception:
                deadline = ""
        if not deadline:
            m = re.search(
                r"(?:deadline|closing date|apply by|due date)[:\s]+([^.;\n]{4,40})",
                text,
                re.IGNORECASE,
            )
            if m:
                deadline = m.group(1).strip()
    if dom:
        _DEADLINE_SCAN_CACHE[dom] = (now, deadline)
    return deadline


def evaluate_deadline_alert(
    prev: str,
    deadline: str,
    last_alert_at: datetime | None,
    last_alert_reason: str | None,
) -> tuple[str | None, dict | None]:
    """Return (reason, meta) when a push-worthy alert should fire."""
    prev = (prev or "").strip()
    deadline = (deadline or "").strip()
    dl_date = parse_deadline_date(deadline)
    days_left = (dl_date - date.today()).days if dl_date else None

    reason = None
    if deadline and not prev:
        reason = "new"
    elif deadline and prev and deadline.lower() != prev.lower():
        reason = "changed"
    elif dl_date is not None and 0 <= days_left <= 7:
        reason = "soon"

    if not reason:
        return None, None

    if reason == "soon" and last_alert_at and last_alert_reason == "soon":
        if (datetime.utcnow() - last_alert_at).total_seconds() < 24 * 3600:
            return None, None

    if reason in ("new", "changed") and last_alert_at and last_alert_reason == reason:
        if prev == deadline:
            return None, None

    return reason, {"days_left": days_left, "deadline": deadline}
