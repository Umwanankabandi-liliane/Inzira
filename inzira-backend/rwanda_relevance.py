"""
Rwanda relevance policy (A/B/C).

Tier A: Rwanda-specific content signals OR configured official Rwanda source.
Tier B: International opportunities explicitly open to Africans / East Africa /
        international / developing countries / remote-global, and not excluding Rwanda.
        These are kept with scope='international'.
Tier C: Explicit foreign-only restrictions (e.g., 'Kenyan citizens only', 'must be based in Nairobi',
        country-lists that exclude Rwanda) are rejected.

Location fields must never be used as a relevance shortcut when they were defaulted.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Literal, Optional, Tuple
from urllib.parse import urlparse

from match_engine import RWANDA_DISTRICTS
from rwanda_sources import is_configured_source

_CONTENT_MARKERS = ("rwanda", "rwandan", "kigali")
_DISTRICT_LOWER = tuple(d.lower() for d in RWANDA_DISTRICTS)
_DEFAULT_LOCATION_VALUES = frozenset({"", "rwanda", "rwanda (national)"})
_LISTING_PREFIX_RE = re.compile(r"^\[(?:listing|portal)\]\s*", re.I)

# Tier B: explicit international accessibility cues (inclusive)
_INTL_INCLUSIVE_RE = re.compile(
    r"\b(open to|eligible|accepting|welcome|applications? (are )?open)\b.*\b("
    r"international|worldwide|global|all countries|all nationalit|any nationality|"
    r"developing countr|low[- ]income countr|sub[- ]saharan|east afric|african|"
    r"remote\b.*\b(global|worldwide|africa)|online\b"
    r")",
    re.I,
)
_INTL_SIMPLE_CUES_RE = re.compile(
    r"\b(international students?|worldwide|global|remote\b|open to afric|east afric|sub[- ]saharan|developing countr)\b",
    re.I,
)

# Tier C: explicit exclusions / foreign-only restrictions
_CITIZENS_ONLY_RE = re.compile(
    r"\b(citizens?|nationals?)\s+of\s+([a-z][a-z .'-]{2,})\s+only\b|\b([a-z][a-z .'-]{2,})\s+citizens?\s+only\b",
    re.I,
)
_MUST_BE_BASED_RE = re.compile(
    r"\b(must|should)\s+be\s+(based|resident|living)\s+in\s+([a-z][a-z .'-]{2,})\b",
    re.I,
)
_EXCLUDES_RWANDA_RE = re.compile(
    r"\b(excluding|except)\b[^.]{0,80}\brwanda\b",
    re.I,
)

Scope = Literal["rwanda", "international"]


def domain_of_url(url: str) -> str:
    try:
        return (urlparse(url or "").netloc or "").lower().replace("www.", "")
    except Exception:
        return ""


def strip_listing_prefix(snippet: str) -> str:
    return _LISTING_PREFIX_RE.sub("", snippet or "").strip()


def is_default_location(location: str) -> bool:
    return (location or "").strip().lower() in _DEFAULT_LOCATION_VALUES


def is_official_rwanda_source(domain: str) -> bool:
    """Configured Rwandan official portals in rwanda_sources.py."""
    dom = (domain or "").replace("www.", "").lower()
    return bool(dom) and is_configured_source(dom)


def has_rwanda_content_signals(text: str) -> bool:
    """True when title/body/URL text mentions Rwanda, Kigali, or a district name."""
    low = (text or "").lower()
    if any(m in low for m in _CONTENT_MARKERS):
        return True
    return any(d in low for d in _DISTRICT_LOWER)


def _tier_c_exclusion(text: str) -> bool:
    low = (text or "").lower()
    if _EXCLUDES_RWANDA_RE.search(low):
        return True
    if _CITIZENS_ONLY_RE.search(low):
        # Allow "Rwandan citizens only" (still Rwanda relevant)
        if "rwanda" in low or "rwandan" in low:
            return False
        return True
    if _MUST_BE_BASED_RE.search(low):
        # Allow "based in Kigali/Rwanda"
        if "rwanda" in low or "kigali" in low:
            return False
        return True
    return False


def _tier_b_international_inclusive(text: str) -> bool:
    low = (text or "").lower()
    if _tier_c_exclusion(low):
        return False
    # Strong pattern or simpler cues
    if _INTL_INCLUSIVE_RE.search(low):
        return True
    if _INTL_SIMPLE_CUES_RE.search(low):
        # Guardrail: avoid accepting obvious single-country listings without inclusive cue context
        return True
    return False


def classify_scope_from_text(text: str, url: str = "", *, source_domain: str = "") -> Optional[Scope]:
    """
    Return scope if listing should be kept, else None.
    - scope='rwanda' for Tier A (Rwanda-specific or configured official source)
    - scope='international' for Tier B (explicitly open to Africans/international and not excluding Rwanda)
    - None for Tier C or irrelevant content
    """
    domain = (source_domain or domain_of_url(url)).replace("www.", "").lower()
    blob = f"{text or ''} {url or ''} {domain}"
    if is_official_rwanda_source(domain):
        return "rwanda"
    if has_rwanda_content_signals(blob):
        return "rwanda"
    if _tier_b_international_inclusive(blob):
        return "international"
    return None


def is_rwanda_relevant_content(text: str, url: str = "") -> bool:
    """
    Harvest-time gate: page content + URL only (never injected location fields).
  """
    return classify_scope_from_text(text, url) is not None


def is_rwanda_relevant_listing(item: Dict[str, Any]) -> bool:
    """
    Registry listing check: title, snippet, apply URL, source domain.
    Location counts only when substantively extracted (not a default placeholder).
    """
    domain = (item.get("source_domain") or item.get("domain") or "").replace("www.", "").lower()
    apply_url = (item.get("apply_url") or item.get("url") or item.get("apply_link") or "").strip()
    title = item.get("title") or ""
    snippet = strip_listing_prefix(item.get("snippet") or "")
    location = item.get("location") or ""
    if is_default_location(location):
        location = ""
    blob = " ".join(x for x in (title, snippet, apply_url, location) if x)
    return classify_scope_from_text(blob, apply_url, source_domain=domain) is not None


def listing_scope(item: Dict[str, Any]) -> str:
    """Return 'rwanda' | 'international' | ''."""
    domain = (item.get("source_domain") or item.get("domain") or "").replace("www.", "").lower()
    apply_url = (item.get("apply_url") or item.get("url") or item.get("apply_link") or "").strip()
    title = item.get("title") or ""
    snippet = strip_listing_prefix(item.get("snippet") or "")
    location = item.get("location") or ""
    if is_default_location(location):
        location = ""
    blob = " ".join(x for x in (title, snippet, apply_url, location) if x)
    scope = classify_scope_from_text(blob, apply_url, source_domain=domain)
    return scope or ""
