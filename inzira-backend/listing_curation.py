"""
Auto-curation verdicts for registry opportunity rows.

Returns (verdict, reason) where verdict is keep | suspect | remove.
Suspect rows stay visible until human review marks remove/recategorize.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

UR_ADMISSION_DOMAINS = frozenset({"efiling.ur.ac.rw", "ur.ac.rw", "www.ur.ac.rw", "www.efiling.ur.ac.rw"})

_FILE_DOWNLOAD_RE = re.compile(r"\.(pdf|doc|docx|xls|xlsx)(\?|$)", re.I)

# ── Commemoration / news / events ───────────────────────────────────────────
_EVENT_TITLE = re.compile(
    r"(?i)\b("
    r"kwibuka\b"
    r"|commemorat"
    r"|remarkable\s+journey"
    r"|supercharged\s+beginning"
    r"|visit\s+of\b.+\bto\b"
    r"|hosts?\b.+\b(retreat|conference|summit|gala|ceremony)"
    r"|wins?\s+\d+(st|nd|rd|th)\s+place"
    r"|award\s+ceremony"
    r"|press\s+release"
    r"|blog\b"
    r")\b"
)
_EVENT_URL = re.compile(r"/(blog|news|events?|press|stories?)/", re.I)

# ── Study materials ─────────────────────────────────────────────────────────
_MATERIAL_TITLE = re.compile(
    r"(?i)\b("
    r"past\s+papers?"
    r"|exam(?:ination)?s?\s+past"
    r"|revision\s+notes?"
    r"|study\s+guide"
    r"|textbook"
    r"|syllabus\s+download"
    r"|marking\s+scheme"
    r")\b"
)

# ── B2B / professional services (not youth apply opportunities) ─────────────
_SERVICE_TITLE = re.compile(
    r"(?i)\b("
    r"team\s+building\b"
    r"|conferences?\s*&\s*corporate\s+events?"
    r"|management\s+consulting"
    r"|advisory\s+services?"
    r"|recruitment\s*&\s*executive\s+search"
    r"|executive\s+search"
    r"|cv\s+writing"
    r"|career\s+coaching"
    r"|corporate\s+events?"
    r"|business\s+directory"
    r")\b"
)

# ── Orphan page fragments / nav chrome ────────────────────────────────────
_FRAGMENT_TITLE = re.compile(
    r"(?i)^\s*("
    r"acceptance\s+letters?"
    r"|who\s+should\s+apply\b"
    r"|find\s+your\s+network"
    r"|submit\s+a\s+job\b"
    r"|post\s+a\s+job\b"
    r"|employer\s+login"
    r"|business\s+directory"
    r"|international\s+student\s+resident"
    r"|chaque\s+solution\s+est\s+motiv"
    r"|application\s+form\s+for\s+examination"
    r"|national\s+examination"
    r")\b"
)
_FRAGMENT_SHORT = re.compile(
    r"(?i)^\s*(home|about|contact|services|downloads?|faqs?|login|register)\s*$"
)

# ── jobwebrwanda geo-index family ───────────────────────────────────────────
_JOBWEBRWANDA_DOMAIN = re.compile(r"(^|\.)jobwebrwanda\.com$", re.I)
_GEO_INDEX_TITLE = re.compile(
    r"(?i)^\s*("
    r"(northern|southern|eastern|western)\s+province"
    r"|kigali(\s+city)?"
    r"|\w+\s+jobs?\s+in\s+rwanda"
    r"|jobs?\s+in\s+\w+"
    r"|location[s]?\s*$"
    r")\s*$"
)
_GEO_INDEX_URL = re.compile(r"/locations?/", re.I)

# ── SEO aggregator / nav junk (not real apply listings) ─────────────────────
_SEO_AGGREGATOR_DOMAINS = frozenset({
    "rwandajobsearch.com",
    "jobwebrwanda.com",
})
_SEO_AGGREGATOR_URL = re.compile(
    r"/(faq|contact|pricing|job-pricing|best-job|job-vacancy-in-rwanda|graduate-salaries|locations?)/",
    re.I,
)
_SEO_AGGREGATOR_TITLE = re.compile(
    r"(?i)\b("
    r"jobs?\s+in\s+\w+"
    r"|job\s+vacanc(?:y|ies)\s+in"
    r"|best\s+job\s+openings"
    r"|job\s+posting"
    r"|graduate\s+salaries"
    r"|explore\s+jobs?\s+in"
    r"|current\s+job\s+vacanc"
    r")\b"
)
_MCFDN_NEWS_URL = re.compile(r"mastercardfdn\.org.*/(news|articles)/", re.I)
_MCFDN_NAV_TITLE = re.compile(
    r"(?i)^\s*("
    r"our\s+career\s+opportunities"
    r"|explore\s+the\s+series"
    r"|program\s+development\s+guide"
    r")\s*$"
)
_NAV_PORTAL_TITLE = re.compile(
    r"(?i)^\s*("
    r"explore\s+jobs?\s+opportunities"
    r"|mastercard\s+foundation\s+scholars\s+program"
    r")\s*$"
)
_NAV_PORTAL_URL = re.compile(
    r"(youthplatform\.co\.rw/opportunities/|mastercardfdn\.org.*/(scholars-program|our-programs)/)",
    re.I,
)
_EXTERNAL_SHARE_URL = re.compile(r"(facebook\.com/sharer|twitter\.com/intent)", re.I)

# ── Compromised / blocked domains (never publish) ───────────────────────────
BLOCKED_SOURCE_DOMAINS = frozenset({
    "debaterwanda.org",
    "www.debaterwanda.org",
})

# ── Gambling / foreign-language injection spam ──────────────────────────────
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_GAMBLING_SPAM_RE = re.compile(
    r"(?i)\b("
    r"casino|glücksspiel|glucksspiel|slot(?:s)?|jackpot|roulette|poker|wager|betting|"
    r"online-casino|chicken\s*road|need\s+for\s+slots|baxterbet|vegashero|happyjokers|"
    r"bonus\s+rewards|gaming\s+with|spieler|joueurs\s+avisés|играч"
    r")\b",
)
_GERMAN_SPAM_RE = re.compile(
    r"(?i)\b("
    r"für|und\s+der|mit\s+der|anbietervergleich|glücksspiel|strategien|"
    r"besondere\s+routenplanung|abenteurer|sorgfältige|unbekanntes\s+terrain|"
    r"langfristigen\s+erfolg|im\s+online"
    r")\b",
)
_FRENCH_SPAM_RE = re.compile(
    r"(?i)\b("
    r"dans\s+l.?univers|authentique\s+immersion|pour\s+les\s+joueurs|"
    r"stratégies\s+innovantes|immersion\s+dans"
    r")\b",
)
_ENGLISH_OPPORTUNITY_RE = re.compile(
    r"(?i)\b("
    r"scholarship|fellowship|bursary|grant|internship|vacanc|apply|admission|"
    r"deadline|cohort|program|training|rwanda|kigali|fully\s+funded|daad|master"
    r")\b",
)

_B2R_NEWS_RE = re.compile(
    r"(?i)b2r\s+farms.*\b(grows\s+to|visits\s+farmers|hosts\s+students)\b",
)
_JOB_MISFILED_AS_SCHOLAR_RE = re.compile(
    r"(?i)\b(lecturer|assistant\s+professor|professor|faculty\s+position)\b",
)
_TRAINING_BLOG_TITLE = re.compile(
    r"(?i)\b("
    r"from\s+firewood\s+to\s+briquettes"
    r"|passion\s+to\s+profession"
    r"|case\s+study:\s*virtual\s+coaching"
    r")\b",
)
_JOB_MISFILED_AS_TRAINING_RE = re.compile(
    r"(?i)\b("
    r"forward\s+deployed\s+data\s+analyst"
    r"|writing\s+centre\s+assistant"
    r"|lecturer\s*/\s*assistant\s+professor"
    r"|lecturer\b|assistant\s+professor"
    r")\b",
)
_REGULATORY_POLICY_RE = re.compile(
    r"(?i)\b("
    r"sets\s+the\s+requirements\s+for\s+institutions"
    r"|requirements\s+for\s+institutions\s+and\s+industries"
    r")\b",
)
_ENROLLMENT_ACTION_RE = re.compile(
    r"(?i)\b("
    r"apply\s+now|call\s+for\s+applications|enroll|enrol|register\s+now|"
    r"how\s+to\s+apply|application\s+deadline|apply\s+by|submit\s+your\s+application|"
    r"applications\s+open|apply\s+today"
    r")\b",
)


def foreign_language_spam_reason(title: str, snippet: str = "") -> Optional[str]:
    """
  Reject injected spam in German, French, Bulgarian/Cyrillic, or gambling text.
  Allow English (or Kinyarwanda) opportunity listings including international programs.
    """
    blob = f"{title} {snippet}".strip()
    if not blob:
        return None
    if _CYRILLIC_RE.search(blob):
        return "rejected-foreign-lang"
    if _GAMBLING_SPAM_RE.search(blob):
        return "rejected-gambling"
    if _GERMAN_SPAM_RE.search(blob):
        return "rejected-foreign-lang"
    if _FRENCH_SPAM_RE.search(blob):
        return "rejected-foreign-lang"
    # French diacritics without any English opportunity signal
    if re.search(r"[àâäéèêëïîôùûüç]", blob) and not _ENGLISH_OPPORTUNITY_RE.search(blob):
        return "rejected-foreign-lang"
  # German umlauts without English opportunity signal
    if re.search(r"[äöüß]", blob, re.I) and not _ENGLISH_OPPORTUNITY_RE.search(blob):
        return "rejected-foreign-lang"
    return None


def is_file_download_url(url: str) -> bool:
    return bool(_FILE_DOWNLOAD_RE.search((url or "").strip()))


def is_ur_admission(item: Dict[str, Any]) -> bool:
    domain = (item.get("source_domain") or item.get("domain") or "").lower().replace("www.", "")
    apply_url = (item.get("apply_url") or item.get("apply_link") or item.get("url") or "").lower()
    if domain not in {d.replace("www.", "") for d in UR_ADMISSION_DOMAINS}:
        return False
    return "/program/" in apply_url or "efiling.ur.ac.rw" in apply_url


def normalize_ur_admission_fields(item: Dict[str, Any]) -> Dict[str, Any]:
    """UR degree programs are admissions (program category only)."""
    out = dict(item)
    if is_ur_admission(out):
        out["subtype"] = "admission"
        out["category"] = "program"
        out["categories"] = ["program"]
    return out


def resolve_apply_link(item: Dict[str, Any]) -> Tuple[str, str]:
    """
    Return (apply_url, apply_label).
    Prefer deep detail-page URLs over portal homepages.
    """
    from opportunity_extractor import is_deep_opportunity_url

    def _valid_http(u: str) -> bool:
        u = (u or "").strip()
        return u.startswith(("http://", "https://")) and " " not in u

    def _shallow(u: str) -> bool:
        return not u or not _valid_http(u) or not is_deep_opportunity_url(u)

    apply_url = (item.get("apply_url") or item.get("apply_link") or item.get("url") or "").strip()
    source_url = (item.get("source_url") or "").strip()

    if apply_url and not _valid_http(apply_url):
        apply_url = ""

    if is_file_download_url(apply_url):
        if source_url and _valid_http(source_url) and not is_file_download_url(source_url):
            return source_url, "application_form_download"
        return apply_url, "application_form_download"

    if _shallow(apply_url):
        if source_url and not _shallow(source_url):
            return source_url, "visit_listing"
        best = apply_url or source_url
        if best:
            return best, "search_on_site"
        return "", "search_on_site"

    if _shallow(source_url) or not source_url:
        return apply_url, "visit_site"

    return apply_url, "visit_site"


def coalesce_apply_urls(item: Dict[str, Any]) -> Tuple[str, str]:
    """Normalize stored apply/source URLs before SQLite save."""
    apply_url, _label = resolve_apply_link(item)
    source_url = (item.get("source_url") or "").strip()
    from opportunity_extractor import is_deep_opportunity_url

    if apply_url and is_deep_opportunity_url(apply_url):
        if not source_url or not is_deep_opportunity_url(source_url):
            source_url = apply_url
    return apply_url, source_url or apply_url


def auto_curation_verdict(item: Dict[str, Any]) -> Tuple[str, str]:
    """
    Classify a listing for curation.
    keep — publishable
    suspect — visible but flagged for human review (reason prefixed rejected-*)
    remove — auto-purge candidate
    """
    from opportunity_extractor import (
        is_article_or_listicle_title,
        is_junk_listing_title,
        is_nav_portal_title,
        is_procurement_listing,
        polish_listing_title,
    )

    title = polish_listing_title(item.get("title") or "")
    snippet = re.sub(r"^\[listing\]\s*", "", (item.get("snippet") or ""), flags=re.I)
    apply_url = (item.get("apply_url") or item.get("apply_link") or item.get("url") or "").strip()
    source_url = (item.get("source_url") or "").strip()
    domain = (item.get("source_domain") or item.get("domain") or "").lower().replace("www.", "")
    blob = f"{title} {snippet} {apply_url} {source_url}".lower()

    if not title:
        return "remove", "empty_title"

    bare_domain = domain.replace("www.", "")
    if bare_domain in {d.replace("www.", "") for d in BLOCKED_SOURCE_DOMAINS}:
        return "remove", "blocked-domain"

    lang_reason = foreign_language_spam_reason(title, snippet)
    if lang_reason:
        return "remove", lang_reason

    if _B2R_NEWS_RE.search(title) or (
        bare_domain == "b2rfarms.com" and _EVENT_URL.search(apply_url)
    ):
        return "remove", "rejected-event"

    stored_cat = (item.get("category") or "").lower()
    if stored_cat == "scholarship" and _JOB_MISFILED_AS_SCHOLAR_RE.search(title):
        return "remove", "wrong_category"

    if _TRAINING_BLOG_TITLE.search(title):
        return "remove", "rejected-event"

    if stored_cat == "training" and _JOB_MISFILED_AS_TRAINING_RE.search(title):
        return "remove", "wrong_category"

    if _REGULATORY_POLICY_RE.search(title) or _REGULATORY_POLICY_RE.search(snippet):
        if not _ENROLLMENT_ACTION_RE.search(blob):
            return "remove", "rejected-policy"

    # UR admissions are always keep once normalized
    if is_ur_admission(item):
        return "keep", ""

    if is_procurement_listing(title, snippet):
        return "remove", "procurement"

    if _EVENT_TITLE.search(title):
        return "remove", "rejected-event"
    if (_EVENT_URL.search(apply_url) or _EVENT_URL.search(source_url)):
        if not re.search(
            r"\b(call\s+for|vacanc|scholarship|fellowship|internship|apply|admission|cohort|program)\b",
            title,
            re.I,
        ):
            return "remove", "rejected-event"

    if _MATERIAL_TITLE.search(title) or _MATERIAL_TITLE.search(snippet):
        return "remove", "rejected-material"

    if _SERVICE_TITLE.search(title):
        return "remove", "rejected-service"

    if _FRAGMENT_TITLE.search(title) or _FRAGMENT_SHORT.match(title):
        return "remove", "rejected-fragment"

    if _JOBWEBRWANDA_DOMAIN.search(domain):
        if _GEO_INDEX_TITLE.match(title) or _GEO_INDEX_URL.search(apply_url):
            return "remove", "rejected-geo-index"
        if title.lower() in {"submit a job", "post a job", "find your network"}:
            return "remove", "rejected-fragment"

    bare_domain = domain.replace("www.", "")
    if bare_domain in _SEO_AGGREGATOR_DOMAINS:
        if (
            _SEO_AGGREGATOR_TITLE.search(title)
            or _SEO_AGGREGATOR_URL.search(apply_url)
            or _SEO_AGGREGATOR_URL.search(source_url)
            or _GEO_INDEX_TITLE.match(title)
        ):
            return "remove", "rejected-aggregator"

    if _EXTERNAL_SHARE_URL.search(apply_url):
        return "remove", "rejected-fragment"

    if _NAV_PORTAL_TITLE.match(title) or _NAV_PORTAL_URL.search(apply_url):
        return "remove", "rejected-fragment"

    if bare_domain == "mastercardfdn.org":
        if re.search(r"/(scholars-program|our-programs)/", apply_url, re.I):
            if (item.get("category") or "").lower() == "job":
                return "remove", "rejected-fragment"

    if bare_domain == "mastercardfdn.org":
        if _MCFDN_NEWS_URL.search(apply_url) or _MCFDN_NEWS_URL.search(source_url):
            return "remove", "rejected-event"
        if _MCFDN_NAV_TITLE.match(title):
            return "remove", "rejected-fragment"
        if re.search(r"/(careers-at-the-mastercard-foundation|program-development-guide)/", apply_url, re.I):
            return "remove", "rejected-fragment"

    if bare_domain == "qsourcing.com":
        if re.search(r"/recruitment-services/?$", apply_url, re.I):
            return "remove", "rejected-service"
        if re.search(r"/(news|articles|celebrates-\d+-years)/", apply_url, re.I):
            return "remove", "rejected-event"

    if is_junk_listing_title(title) or is_nav_portal_title(title):
        return "remove", "junk_title"

    if is_article_or_listicle_title(title):
        return "remove", "listicle"

    # Direct file download with no listing page — suspect, not auto-remove
    if is_file_download_url(apply_url) and (not source_url or is_file_download_url(source_url)):
        if not re.search(r"\b(vacanc|scholar|intern|fellowship|program|apply|admission)\b", blob):
            return "suspect", "rejected-material:file-download-only"

    # Blog paths on opportunity sites (not real listings)
    if re.search(r"/blog/", apply_url, re.I):
        if not re.search(
            r"\b(vacanc|scholarship|internship|fellowship|call\s+for|apply|admission|cohort)\b",
            title,
            re.I,
        ):
            return "remove", "rejected-event"

    try:
        from listing_quality import is_current_listing, is_rwanda_relevant_listing
        if not is_current_listing({**item, "title": title, "snippet": snippet}):
            return "remove", "expired_or_stale"
        if not is_rwanda_relevant_listing({**item, "title": title, "snippet": snippet}):
            return "remove", "not_rwanda_relevant"
    except Exception:
        pass

    return "keep", ""


def should_auto_purge(item: Dict[str, Any]) -> Optional[str]:
    verdict, reason = auto_curation_verdict(item)
    if verdict == "remove":
        return reason or "remove"
    return None
