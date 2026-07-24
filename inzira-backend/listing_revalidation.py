"""
Live URL checks for harvested opportunity listings.

During nightly harvest, re-fetch apply URLs for active listings and
remove rows whose pages are gone, denied, or clearly closed.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

import requests

from deadline_scan import parse_deadline_date

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; InziraRegistryBot/1.0; +https://liliane078-inzira.hf.space)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
}

_GONE_STATUSES = {404, 410, 451}
_DENIED_STATUSES = {401, 403}
_SERVER_ERROR_STATUSES = {500, 502, 503, 504}

_CLOSED_BODY_RE = re.compile(
    r"(applications?\s+closed|application\s+closed|no longer accepting|"
    r"position filled|vacancy filled|expired|has ended|was closed|"
    r"access denied|page not found|404 not found|this opportunity is closed|"
    r"listing (?:has )?expired|no longer available)",
    re.I,
)

_ERROR_TITLE_RE = re.compile(
    r"(404|403|access denied|page not found|not found|forbidden|error)",
    re.I,
)


def _domain(url: str) -> str:
    try:
        return (urlparse(url).netloc or "").lower().replace("www.", "")
    except Exception:
        return ""


def _final_path_differs_to_error(original: str, final: str) -> bool:
    """Detect redirects to generic error/home pages on another path."""
    if not original or not final:
        return False
    o = urlparse(original)
    f = urlparse(final)
    if _domain(original) != _domain(final):
        return True
    fpath = (f.path or "/").lower()
    if fpath in ("/", "/home", "/index.html"):
        opath = (o.path or "/").lower()
        if opath not in ("/", "/home", "/index.html") and len(opath.strip("/")) >= 2:
            return True
    if _ERROR_TITLE_RE.search(fpath):
        return True
    return False


def validate_listing_url(url: str, *, timeout: int = 12) -> Dict[str, object]:
    """
    Lightweight live check for a listing apply URL.
    Returns {ok: bool, status_code: int|None, reason: str, final_url: str}
    """
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "status_code": None, "reason": "invalid_url", "final_url": url}

    try:
        res = requests.get(
            url,
            headers=_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return {"ok": False, "status_code": None, "reason": f"fetch_error:{exc.__class__.__name__}", "final_url": url}

    code = res.status_code
    final = (res.url or url).strip()
    if code in _GONE_STATUSES:
        return {"ok": False, "status_code": code, "reason": "http_gone", "final_url": final}
    if code in _DENIED_STATUSES:
        return {"ok": False, "status_code": code, "reason": "http_denied", "final_url": final}
    if code >= 400:
        return {"ok": False, "status_code": code, "reason": f"http_{code}", "final_url": final}

    if _final_path_differs_to_error(url, final):
        return {"ok": False, "status_code": code, "reason": "redirect_to_home_or_error", "final_url": final}

    body = (res.text or "")[:8000]
    low = body.lower()
    if _CLOSED_BODY_RE.search(low):
        return {"ok": False, "status_code": code, "reason": "closed_content", "final_url": final}

    title_m = re.search(r"<title[^>]*>([^<]{1,120})</title>", body, re.I)
    if title_m and _ERROR_TITLE_RE.search(title_m.group(1)):
        return {"ok": False, "status_code": code, "reason": "error_title", "final_url": final}

    return {"ok": True, "status_code": code, "reason": "ok", "final_url": final}


def revalidate_active_listings(
    reg,
    *,
    log: Optional[Callable[[str], None]] = None,
    limit: int = 400,
    only_future_deadline: bool = True,
) -> int:
    """
    HTTP-check active listings; unverify or delete rows whose apply pages are gone/closed.
    Returns count removed/unverified.
    """
    out = log or (lambda _m: None)
    rows = reg.list_opportunities_for_revalidation(limit=limit)
    if not rows:
        return 0

    removed = 0
    checked = 0
    for row in rows:
        opp_id = row["id"]
        apply_url = (row.get("apply_url") or "").strip()
        deadline = (row.get("deadline") or "").strip()
        if only_future_deadline and deadline:
            dl = parse_deadline_date(deadline)
            if dl is not None:
                from datetime import date
                if dl < date.today():
                    reg.delete_opportunity_by_id(opp_id)
                    removed += 1
                    continue

        if not apply_url:
            continue

        checked += 1
        result = validate_listing_url(apply_url)
        if result["ok"]:
            continue

        reason = str(result.get("reason") or "failed")
        title = (row.get("title") or "")[:60]
        out(f"  revalidate drop id={opp_id} ({reason}): {title}")
        reg.delete_opportunity_by_id(opp_id)
        removed += 1

    out(f"Live re-validation: checked {checked}, removed {removed}")
    return removed
