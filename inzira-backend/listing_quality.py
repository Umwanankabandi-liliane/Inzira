"""
Publishability checks for opportunity listings shown to Rwanda youth.
Filters expired, foreign-only, junk scrapes, and non-Rwanda noise.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

_EXPIRED_YEARS = ("2018", "2019", "2020", "2021", "2022", "2023", "2024")
_CURRENT_MARKERS = ("2026", "2027", "2028", "open", "ongoing", "rolling", "now open")
_STALE_YEAR_ONLY = re.compile(r"\b2025\b")
_STALE_YEAR_SPAN = re.compile(r"\b2025\s*[-/]\s*202[6-9]\b")
_STALE_BRAND_YEAR = re.compile(r"(?i)\bnew\s+america\b.*\b2025\b|\b2025\b.*\bnew\s+america\b")
_OLD_MONTH_YEAR = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)"
    r"\s*(20(1[89]|2[0-4]))\b",
    re.I,
)

_FOREIGN_COUNTRIES = (
    "nigeria", "senegal", "uganda", "kenya", "ghana", "tanzania",
    "ethiopia", "cameroon", "zambia", "zimbabwe", "malawi",
    "central african republic", "democratic republic of congo", "south sudan",
)

_FOREIGN_ONLY = (
    "for nigerians",
    "nigeria only",
    "in nigeria",
    "open for nigerians",
    "– nigeria",
    "- nigeria",
    "kenya only",
    "for ugandans",
    "south africa only",
    "ghana only",
    "for tanzanians",
    "for ethiopians",
    "jobs in africa",
    "uganda, kenya, nigeria",
    "browse job opportunities in uganda",
)

_JUNK_BLOB = (
    "application form for examination",
    "examination center",
    "national examination",
    "email-protection",
    "cdn-cgi",
    "application link",
    "click here to apply",
    "catch fish and them the net",
)

def is_rwanda_relevant_listing(item: Dict[str, Any]) -> bool:
    from rwanda_relevance import is_rwanda_relevant_listing as _check
    return _check(item)


def _is_stale_2025_listing(item: Dict[str, Any]) -> bool:
    """True when listing is dated 2025-only (title/deadline), not a 2026+ cycle."""
    title = (item.get("title") or "").lower()
    deadline = (item.get("deadline") or "").lower()
    if not _STALE_YEAR_ONLY.search(f"{title} {deadline}"):
        if not _STALE_YEAR_ONLY.search((item.get("snippet") or "")[:240].lower()):
            return False
        if re.search(r"\b202[6-9]\b", title):
            return False
        return True
    if re.search(r"\b202[6-9]\b", title):
        return False
    if _STALE_YEAR_SPAN.search(title) or _STALE_YEAR_SPAN.search(deadline):
        return False
    return True


def is_current_listing(item: Dict[str, Any]) -> bool:
    blob = " ".join([
        item.get("title") or "",
        item.get("snippet") or "",
        item.get("deadline") or "",
    ]).lower()

    if any(y in blob for y in _EXPIRED_YEARS):
        if not any(m in blob for m in _CURRENT_MARKERS):
            return False

    if _is_stale_2025_listing(item):
        return False

    title_deadline = f"{item.get('title') or ''} {item.get('deadline') or ''}"
    if _STALE_BRAND_YEAR.search(title_deadline):
        return False

    if _OLD_MONTH_YEAR.search(blob):
        if not any(m in blob for m in _CURRENT_MARKERS):
            return False

    # Glued blog dates in titles: Post18 October 2023...
    if re.search(r"\bpost\d{1,2}\s*(january|february|march|april|may|june|july|august|september|october|november|december)\s*20(1[89]|2[0-4])\b", blob, re.I):
        if not any(m in blob for m in _CURRENT_MARKERS):
            return False

    if any(m in blob for m in _FOREIGN_ONLY):
        if "rwanda" not in blob and "kigali" not in blob:
            return False

    for country in _FOREIGN_COUNTRIES:
        if country in blob and "rwanda" not in blob and "kigali" not in blob:
            # Allow pan-Africa only when Rwanda is in scope
            if country in (item.get("title") or "").lower():
                return False

    if any(m in blob for m in _JUNK_BLOB):
        return False

    apply_url = (item.get("apply_url") or item.get("url") or "").lower()
    if not apply_url or apply_url.startswith("mailto:"):
        return False

    return True


def is_publishable_listing(item: Dict[str, Any]) -> bool:
    try:
        from listing_curation import should_auto_purge, is_ur_admission, normalize_ur_admission_fields
        item = normalize_ur_admission_fields(item)
        if is_ur_admission(item):
            return True
        purge_reason = should_auto_purge(item)
        if purge_reason:
            return False
    except Exception:
        pass

    try:
        from opportunity_extractor import (
            is_junk_listing_title,
            is_nav_portal_title,
            is_procurement_listing,
            is_deep_opportunity_url,
            polish_listing_title,
            title_snippet_coherent,
            clean_organization,
        )
        title = polish_listing_title(item.get("title") or "")
        snippet_raw = re.sub(r"^\[listing\]\s*", "", (item.get("snippet") or ""), flags=re.I)
        if is_procurement_listing(title, snippet_raw):
            return False
        if is_junk_listing_title(title) or is_nav_portal_title(title):
            return False
        apply_url = (item.get("apply_url") or item.get("url") or item.get("apply_link") or "").strip()
        if apply_url and not is_deep_opportunity_url(apply_url):
            return False
        snippet = snippet_raw
        if not title_snippet_coherent(title, snippet):
            return False
        org = item.get("organization") or ""
        domain = item.get("source_domain") or item.get("domain") or ""
        cleaned = clean_organization(org, domain, title)
        if org and cleaned != org and len(org) > 42:
            return False
    except Exception:
        pass

    if not is_current_listing(item):
        return False
    if not is_rwanda_relevant_listing(item):
        return False

    try:
        from inzira_features import deadline_guardian
        st = deadline_guardian(item.get("deadline") or "")
        if st.get("status") == "expired" or (st.get("days_left") is not None and st["days_left"] <= 0):
            return False
    except Exception:
        pass

    return True


def filter_publishable(items: List[dict]) -> List[dict]:
    return [i for i in items if is_publishable_listing(i)]


# ── Cross-source deduplication ─────────────────────────────────────────────
from urllib.parse import urlparse

DOMAIN_CANONICAL = {
    # National Internship Programme portal (not the main rdb.rw site)
    "dev.internship.rw": "internship.rw",
    "internshipdev.rdb.rw": "internship.rw",
    "kora2.rdb.rw": "rdb.rw",
    "www.kora2.rdb.rw": "rdb.rw",
}


def canonical_domain(domain: str) -> str:
    d = (domain or "").lower().replace("www.", "")
    return DOMAIN_CANONICAL.get(d, d)


def root_domain(domain: str) -> str:
    d = canonical_domain(domain)
    parts = d.split(".")
    if len(parts) >= 2 and parts[-1] in ("rw", "com", "org", "net", "de"):
        return ".".join(parts[-2:])
    return d


def normalize_title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())[:56]


def dedupe_key(item: Dict[str, Any]) -> str:
    url = (item.get("apply_link") or item.get("url") or item.get("apply_url") or "").lower().rstrip("/")
    domain = item.get("source_domain") or item.get("domain") or ""
    if not domain and url:
        try:
            domain = urlparse(url).netloc
        except Exception:
            domain = ""
    rd = root_domain(domain)
    tk = normalize_title_key(item.get("title") or "")
    if tk and len(tk) >= 8:
        return f"{rd}|{tk}"
    return url or tk or ""


def dedupe_listings(items: List[dict]) -> List[dict]:
    """Keep highest trust_score per dedupe_key (mirror domains + same title)."""
    best: Dict[str, dict] = {}
    order: List[str] = []
    for item in sorted(items, key=lambda x: float(x.get("trust_score") or 0), reverse=True):
        key = dedupe_key(item)
        if not key:
            continue
        if key not in best:
            order.append(key)
            best[key] = item
    return [best[k] for k in order]
