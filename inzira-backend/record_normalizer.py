"""
Presentation normalization for harvested opportunity records.

Cleans titles, organizations, deadlines, locations, and snippets so cards
match how opportunities read on the source site.
"""

from __future__ import annotations

import html as html_lib
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from match_engine import RWANDA_DISTRICTS
from opportunity_extractor import detect_district, polish_listing_title
from rwanda_sources import source_config_for_domain

try:
    from dateutil import parser as date_parser
except ImportError:  # pragma: no cover
    date_parser = None

_TITLE_SEP_RE = re.compile(r"\s*[\|–—]\s*|\s+-\s+")
_GENERIC_TITLES = frozenset({
    "jobs", "job", "vacancies", "vacancy", "home", "about us", "about",
    "careers", "opportunities", "opportunity", "scholarships", "internships",
    "training", "programs", "news", "blog", "contact", "login", "register",
    "terms of use", "privacy policy", "default job application form",
})
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_KIGALI_ALIASES = ("kigali", "city of kigali")


def clean_text(value: str) -> str:
    if not value:
        return ""
    text = html_lib.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def domain_display_name(domain: str) -> str:
    d = (domain or "").lower().replace("www.", "").strip()
    if not d:
        return "Rwanda Portal"
    label = d.split(".")[0].replace("-", " ").replace("_", " ").strip()
    return label.title() if label else d


def site_display_name(domain: str) -> str:
    src = source_config_for_domain(domain)
    if src and src.get("name"):
        return clean_text(src["name"])
    return domain_display_name(domain)


def is_generic_listing_title(title: str) -> bool:
    t = clean_text(title).lower().strip(" -|,")
    if not t or len(t) < 4:
        return True
    if t in _GENERIC_TITLES:
        return True
    if re.match(r"^(jobs?|vacancies|careers|opportunities)\s*(in\s+)?rwanda\??$", t):
        return True
    return False


def strip_site_suffix(title: str, *, site_name: str = "", domain: str = "") -> str:
    t = clean_text(title)
    if not t:
        return ""
    site_low = clean_text(site_name).lower()
    domain_root = (domain or "").lower().replace("www.", "").split(".")[0]
    hints = {x for x in (site_low, domain_root, domain.lower().replace("www.", "")) if x}

    parts = _TITLE_SEP_RE.split(t, maxsplit=1)
    if len(parts) == 2:
        left, right = parts[0].strip(), parts[1].strip().lower()
        for hint in hints:
            if hint and (hint in right or right in hint):
                return left
        # common portal suffixes even if name differs slightly
        for suffix in ("job in rwanda", "free digital opportunities", "kigalijob"):
            if suffix in right:
                return left
    return t


def trim_title(title: str, max_len: int = 120) -> str:
    t = polish_listing_title(clean_text(title))
    if len(t) <= max_len:
        return t
    cut = t[:max_len].rsplit(" ", 1)[0].strip()
    return cut or t[:max_len].strip()


def normalize_title(
    title: str,
    *,
    site_name: str = "",
    domain: str = "",
) -> str:
    t = trim_title(strip_site_suffix(title, site_name=site_name, domain=domain))
    if is_generic_listing_title(t):
        return ""
    return t


def parse_deadline_iso(raw: str, *, page_text: str = "") -> str:
    """Return YYYY-MM-DD or empty string when unparseable."""
    candidates = [raw]
    if page_text and not raw:
        from opportunity_extractor import detect_deadline
        detected = detect_deadline(page_text)
        if detected:
            candidates.append(detected)

    for cand in candidates:
        text = clean_text(cand)
        if not text:
            continue
        if date_parser is not None:
            try:
                dt = date_parser.parse(text, dayfirst=True, fuzzy=True)
                if 2000 <= dt.year <= 2100:
                    return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError, OverflowError):
                pass
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})", text)
        if m and date_parser is not None:
            try:
                dt = date_parser.parse(f"{m.group(1)} {m.group(2)} {m.group(3)}", dayfirst=True)
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

    if page_text and date_parser is not None:
        for m in re.finditer(
            r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2})\b",
            clean_text(page_text),
        ):
            iso = parse_deadline_iso(m.group(1))
            if iso:
                return iso
    return ""


def normalize_organization(
    organization: str,
    *,
    ner_organization: str = "",
    domain: str = "",
    site_name: str = "",
) -> str:
    for cand in (organization, ner_organization, site_name, domain_display_name(domain)):
        c = clean_text(cand)
        if not c:
            continue
        low = c.lower()
        if low in _GENERIC_TITLES or low == (domain or "").lower():
            continue
        if len(c) > 80:
            c = c[:80].rsplit(" ", 1)[0].strip()
        return c
    return domain_display_name(domain)


def normalize_location_fields(
    location: str,
    district: str = "",
    *,
    page_text: str = "",
) -> tuple[str, str]:
    blob = clean_text(f"{location} {district} {page_text[:600]}")
    found = detect_district(blob) or ""
    if not found:
        low = blob.lower()
        if any(a in low for a in _KIGALI_ALIASES):
            found = "Gasabo"
    if found and found in RWANDA_DISTRICTS:
        return f"{found}, Rwanda", found
    low = blob.lower()
    if "kigali" in low:
        return "Kigali, Rwanda", found or ""
    if re.search(r"\brwanda\b", low):
        return "Rwanda", ""
    return "", ""


_BOILERPLATE_RE = re.compile(
    r"\b(listing on\s+\S+|apply on (the )?official portal|click here to apply|read more)\b",
    re.I,
)


def normalize_snippet(body_text: str, *, fallback: str = "", max_len: int = 300) -> str:
    text = clean_text(body_text or fallback)
    if not text:
        return ""
    text = _BOILERPLATE_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    if fallback and len(clean_text(fallback)) >= 40 and len(text) < 40:
        text = clean_text(fallback)

    sentences: list[str] = []
    for sent in _SENTENCE_SPLIT_RE.split(text):
        s = sent.strip()
        if len(s) < 20:
            continue
        if s.lower().startswith(("click here", "read more", "share this", "apply here")):
            continue
        sentences.append(s)
        joined = " ".join(sentences)
        if len(sentences) >= 3 or len(joined) >= max_len:
            break

    snippet = " ".join(sentences) if sentences else text
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0].strip()
    return snippet


def normalize_extracted_record(
    record: Dict[str, Any],
    *,
    page_url: str = "",
    domain: str = "",
    page_text: str = "",
    ner_entities: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Clean one extracted detail-page dict. Returns None if title is a listing page."""
    if not record:
        return None
    ner = ner_entities or {}
    dom = (domain or urlparse(page_url).netloc or "").replace("www.", "")
    site_name = site_display_name(dom)

    title = normalize_title(
        record.get("title") or "",
        site_name=site_name,
        domain=dom,
    )
    if not title:
        return None

    org = normalize_organization(
        record.get("organization") or "",
        ner_organization=ner.get("organization", ""),
        domain=dom,
        site_name=site_name,
    )
    deadline = parse_deadline_iso(
        record.get("deadline") or "",
        page_text=page_text or record.get("page_text") or "",
    )
    if not deadline and ner.get("deadline"):
        deadline = parse_deadline_iso(ner.get("deadline", ""))

    location, district = normalize_location_fields(
        record.get("location") or ner.get("location", ""),
        record.get("district") or "",
        page_text=page_text or record.get("page_text") or "",
    )
    snippet = normalize_snippet(
        page_text or record.get("page_text") or "",
        fallback=record.get("snippet") or "",
    )

    out = dict(record)
    out["title"] = title
    out["organization"] = org
    out["deadline"] = deadline
    out["location"] = location
    out["district"] = district
    out["snippet"] = snippet
    return out


def normalize_registry_item(item: Dict[str, Any], *, domain: str = "") -> Dict[str, Any]:
    """Final presentation pass before SQLite save."""
    dom = (domain or item.get("source_domain") or "").replace("www.", "")
    site_name = site_display_name(dom)
    snippet_raw = item.get("snippet") or ""
    if snippet_raw.startswith("[listing] "):
        snippet_raw = snippet_raw[len("[listing] "):]
    elif snippet_raw.startswith("[portal] "):
        snippet_raw = snippet_raw[len("[portal] "):]

    title = normalize_title(item.get("title") or "", site_name=site_name, domain=dom)
    org = normalize_organization(
        item.get("organization") or "",
        domain=dom,
        site_name=site_name,
    )
    deadline = parse_deadline_iso(item.get("deadline") or "")
    location, district = normalize_location_fields(
        item.get("location") or "",
        item.get("district") or "",
        page_text=f"{title} {snippet_raw}",
    )
    snippet = normalize_snippet(snippet_raw, fallback=title)

    out = dict(item)
    if title:
        out["title"] = title
    out["organization"] = org
    out["deadline"] = deadline
    out["location"] = location
    out["district"] = district
    if snippet:
        prefix = "[listing] " if (item.get("snippet") or "").startswith("[listing]") else ""
        out["snippet"] = f"{prefix}{snippet}" if prefix else snippet

    from listing_curation import coalesce_apply_urls
    apply_url, source_url = coalesce_apply_urls(out)
    if apply_url:
        out["apply_url"] = apply_url
    if source_url:
        out["source_url"] = source_url
    return out
