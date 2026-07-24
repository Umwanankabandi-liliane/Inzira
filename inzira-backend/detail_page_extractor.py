"""
Extract one opportunity record from a single detail page (HTML).

Priority: schema.org JSON-LD → semantic HTML (h1, article body).
Presentation normalization applied via record_normalizer.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from opportunity_extractor import (
    detect_deadline,
    detect_district,
    polish_listing_title,
)
from record_normalizer import normalize_extracted_record

_SCHEMA_TYPES = frozenset({
    "jobposting",
    "educationaloccupationalprogram",
    "course",
    "event",
    "scholarship",
})


def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _iter_json_ld_nodes(data: Any) -> List[dict]:
    if isinstance(data, dict):
        if "@graph" in data and isinstance(data["@graph"], list):
            return [n for n in data["@graph"] if isinstance(n, dict)]
        return [data]
    if isinstance(data, list):
        out: List[dict] = []
        for item in data:
            out.extend(_iter_json_ld_nodes(item))
        return out
    return []


def _schema_type(node: dict) -> str:
    raw = node.get("@type") or ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    return str(raw).lower().replace(" ", "")


def _org_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or "").strip()
    if isinstance(value, str):
        return value.strip()
    return ""


def _location_text(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for key in ("addressLocality", "addressRegion", "name"):
            v = value.get(key)
            if v:
                parts.append(str(v))
        return ", ".join(parts)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and value:
        return _location_text(value[0])
    return ""


def extract_json_ld_record(html: str, page_url: str) -> Optional[Dict[str, str]]:
    """Return structured fields from JobPosting / EducationalOccupationalProgram JSON-LD."""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return None

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        for node in _iter_json_ld_nodes(payload):
            st = _schema_type(node)
            if st not in _SCHEMA_TYPES and not any(t in st for t in ("job", "program", "course")):
                continue
            title = str(node.get("title") or node.get("name") or "").strip()
            if not title or len(title) < 4:
                continue
            org = _org_name(node.get("hiringOrganization") or node.get("provider") or node.get("organizer"))
            deadline = str(
                node.get("validThrough")
                or node.get("endDate")
                or node.get("applicationDeadline")
                or ""
            ).strip()
            if deadline and "T" in deadline:
                deadline = deadline.split("T", 1)[0]
            loc = _location_text(node.get("jobLocation") or node.get("location"))
            desc = re.sub(r"\s+", " ", str(node.get("description") or ""))[:1200]
            out: Dict[str, str] = {
                "title": title,
                "organization": org,
                "deadline": deadline,
                "location": loc or "",
                "snippet": desc[:400] if desc else "",
                "canonical_url": str(node.get("url") or page_url).strip(),
                "page_text": desc,
                "extraction": "json_ld",
            }
            district = detect_district(f"{title} {loc} {desc}")
            if district:
                out["district"] = district
            return out
    return None


def extract_html_record(html: str, page_url: str) -> Optional[Dict[str, str]]:
    """Fallback extraction: title priority h1 → og:title → <title>."""
    if not html.strip():
        return None
    soup = BeautifulSoup(html, "html.parser")

    canonical = page_url
    link = soup.find("link", rel=lambda v: v and "canonical" in str(v).lower())
    if link and link.get("href"):
        canonical = link["href"].strip()

    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)

    if not title:
        for sel in (
            ("meta", {"property": "og:title"}),
            ("meta", {"name": "twitter:title"}),
        ):
            tag = soup.find(sel[0], sel[1])
            if tag and tag.get("content"):
                title = tag["content"].strip()
                if title:
                    break

    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()

    if not title or len(title) < 4:
        return None

    body_soup = BeautifulSoup(html, "html.parser")
    root = body_soup.find("article") or body_soup.find("main") or body_soup.body
    page_text = ""
    if root:
        root_copy = BeautifulSoup(str(root), "html.parser")
        for tag in root_copy(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
            tag.decompose()
        page_text = _visible_text(root_copy)
    if len(page_text) < 80:
        page_text = _visible_text(BeautifulSoup(html, "html.parser"))

    return {
        "title": title,
        "organization": "",
        "deadline": detect_deadline(page_text),
        "location": "",
        "district": "",
        "snippet": "",
        "canonical_url": canonical,
        "page_text": page_text[:4000],
        "word_count": str(_word_count(page_text)),
        "extraction": "html",
    }


def extract_detail_page(html: str, page_url: str) -> Optional[Dict[str, str]]:
    """One detail page → normalized extraction dict (before ML gate)."""
    domain = urlparse(page_url).netloc.replace("www.", "")
    record = extract_json_ld_record(html, page_url)
    if record:
        if not record.get("page_text"):
            fallback = extract_html_record(html, page_url)
            record["page_text"] = (fallback or {}).get("page_text", record.get("snippet", ""))
    else:
        record = extract_html_record(html, page_url)

    if not record:
        return None

    page_text = record.get("page_text") or ""
    return normalize_extracted_record(
        record,
        page_url=page_url,
        domain=domain,
        page_text=page_text,
    )


def is_js_shell_page(html: str) -> bool:
    if not html:
        return False
    soup = BeautifulSoup(html, "html.parser")
    scripts = len(soup.find_all("script"))
    words = _word_count(_visible_text(soup))
    raw = html[:4000].lower()
    # Tiny React/Vue shells (e.g. internship.rw) often have few scripts but an empty root.
    if words < 80 and scripts >= 1 and (
        'id="root"' in raw or "id='root'" in raw or 'id="app"' in raw or "id='app'" in raw
    ):
        return True
    return scripts >= 8 and words < 200
