"""
Extract individual opportunity listings from verified portal pages.
Falls back to category-specific cards when no listings are found in HTML.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from match_engine import RWANDA_DISTRICTS
from registry_db import INZIRA_CATEGORIES, hosts_label, PORTAL_SNIPPET_PREFIX, EXTRACTED_SNIPPET_PREFIX

_DEADLINE_RE = re.compile(
    r"(?:deadline|closing|apply by|due)[:\s]*"
    r"(\d{1,2}[\s/.-][A-Za-z]{3,9}[\s/.-]\d{2,4}|\d{4}-\d{2}-\d{2})",
    re.I,
)
_KIGALI_ALIASES = ("kigali", "city of kigali")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

_LINK_HINT = re.compile(
    r"\b(vacanc|job|career|scholar|bursar|intern|fellow|train|program|"
    r"competition|apply|application|opening|position|recruit|hire|grant|course|tender)\b",
    re.I,
)

_GENERIC_TITLE_RE = re.compile(
    r"^(admissions?|requirements?( and application)?|apply( now)?|contact( us)?|"
    r"home|about( us)?|career guidance|mentorship.*guidance|read more|learn more|"
    r"news|blog|events?|gallery|downloads?|faqs?|login|sign in|services?)$",
    re.I,
)

_JUNK_TITLE_PHRASES = frozenset({
    "application link", "apply here", "click here", "read more", "learn more",
    "download", "submit application", "register now", "view details", "apply online",
    "click to apply", "more info", "see more", "full story", "continue reading",
    "how to apply", "apply for job", "track application", "read article",
    "explore all courses", "call application", "important notice",
    "read her story", "read his story", "application status",
    "application fee deadline", "submit a job", "post a job", "find your network",
})

_NAV_ONLY_TITLES = frozenset({
    "admissions", "requirements and application", "career guidance",
    "mentorship & career guidance", "programs", "services", "apply now",
    "learn more", "read more", "contact us", "about us",
    "how to apply", "apply for job", "track application",
    "admission requirements process track application",
})

_POST_TITLE_RE = re.compile(
    r"^post\s*\d{0,2}\s*"
    r"(\d{1,2}\s+[a-z]{3,9}\s+\d{2,4})?\s*",
    re.I,
)

_SECTION_HEADING_RE = re.compile(
    r"^(internship\s+)?program\s+objectives?\s*:?\s*$|"
    r"^unlock\s+your\s+future\s*:?\s*$|"
    r"^(our\s+)?(mission|vision|values|objectives?)\s*:?\s*$|"
    r"^(why|what|how)\s+(we|us|choose|internship|program)\s+.*:?\s*$|"
    r"^(key\s+)?benefits\s*:?\s*$|"
    r"^about\s+(the\s+)?(program|internship)\s*:?\s*$",
    re.I,
)

_ARTICLE_SELECTORS = (
    "article h2 a[href]",
    "article h3 a[href]",
    ".entry-title a[href]",
    ".post-title a[href]",
    "h2.entry-title a[href]",
    ".job-title a[href]",
    ".listing-title a[href]",
    ".opportunity-title a[href]",
)

_CATEGORY_FROM_TEXT = {
    "scholarship": (r"\bscholar", r"\bbursar", r"\bgrant", r"\bfellowship\b", r"\bhec\b"),
    "job": (r"\bvacanc", r"\bjob\b", r"\bcareer", r"\bposition\b", r"\brecruit", r"\bhire\b", r"\bemployment\b"),
    "internship": (r"\binternship", r"\bintern\b", r"\btrainee\b", r"\battachment\b"),
    "training": (r"\btraining", r"\bbootcamp", r"\bskills\b", r"\btvet\b", r"\bworkshop\b"),
    "competition": (r"\bcompetition", r"\bhackathon", r"\bchallenge\b", r"\bprize\b"),
    "program": (r"\bprogram", r"\bfellowship\b", r"\byouth\b", r"\bempower"),
    "free_course": (r"\bcourse", r"\bmooc\b", r"\blearn\b", r"\bcertification\b"),
}

_CATEGORY_TITLES = {
    "job": "Open job vacancies",
    "scholarship": "Scholarships & grants",
    "internship": "Internship openings",
    "training": "Training programs",
    "competition": "Competitions & challenges",
    "program": "Youth programs",
    "free_course": "Free courses",
}


def fetch_page_html(url: str, timeout: int = 10) -> str:
    try:
        res = requests.get(url, headers=_HEADERS, timeout=timeout)
        res.raise_for_status()
        return res.text
    except Exception:
        return ""


_LISTING_PATH_RE = re.compile(
    r"/(?:jobs?|vacanc(?:y|ies)|careers?|scholar(?:ship)?s?|intern(?:ship)?s?|"
    r"programs?|trainings?|competitions?|courses?|apply|applications?|"
    r"opportunities?|announcements?|posts?|openings?|tenders?)/",
    re.I,
)

_LONG_SLUG_HINTS_RE = re.compile(
    r"(job|apply|vacanc|recruit|scholarship|intern|fellow|train|program|competition|"
    r"tender|position|hiring|opportunit|recruitment|examination|symposium)",
    re.I,
)


def is_long_single_slug_path(path_or_url: str) -> bool:
    """WordPress / CMS posts: /long-slug-with-job-apply-keywords (with or without trailing slash)."""
    path = path_or_url
    if "://" in (path_or_url or ""):
        path = urlparse(path_or_url).path or ""
    slug = (path or "").strip("/").lower()
    if not slug:
        return False
    if slug.startswith("investment-opportunities/"):
        parts = slug.split("/")
        return len(parts) == 2 and bool(parts[1])
    if "/" in slug:
        return False
    if len(slug) >= 20 and _LONG_SLUG_HINTS_RE.search(slug):
        return True
    return len(slug) >= 45


def is_listing_like_path(url: str) -> bool:
    try:
        path = (urlparse(url).path or "").lower()
    except Exception:
        return False
    if _LISTING_PATH_RE.search(path):
        return True
    if is_long_single_slug_path(path):
        return True
    # slug with date or numeric id: /2026/..., /job/12345 (optional trailing slash)
    if re.search(r"/\d{4}/|/\d{5,}|/[\w-]{10,}/?$", path):
        return True
    return False


def is_deep_opportunity_url(url: str) -> bool:
    """Reject homepages and navigation pages masquerading as opportunities."""
    try:
        parsed = urlparse(url)
        path = (parsed.path or "/").strip("/").lower()
    except Exception:
        return False
    if not path:
        return False
    shallow = {
        "news", "about", "contact", "admissions", "home", "index",
        "login", "register", "events", "blog", "gallery",
    }
    if path in shallow:
        return False
    if path.startswith("program-category/"):
        return False
    if path.startswith("category/") and "program" in path:
        return False
    if path.startswith("investment-opportunities/") and path.count("/") == 1:
        return True
    return is_listing_like_path(url) or len(path.split("/")) >= 2


def clean_organization(org: str, domain: str = "", title: str = "") -> str:
    """Use a short host/org label — never a scraped sentence from another listing."""
    org = re.sub(r"\s+", " ", (org or "").strip())
    low = org.lower()
    if len(org) > 42 or re.search(r"\b(join the|apply now|click here|hiring|vacanc)\b", low):
        org = ""
    if org and org.lower() == (title or "").lower()[: len(org)]:
        org = ""
    if not org and domain:
        host = domain.replace("www.", "")
        org = host.split(".")[0].replace("-", " ").title()
    return org[:80]


def is_nav_portal_title(title: str) -> bool:
    low = (title or "").lower().strip()
    if re.match(r"^browse all \d+\+?\s*program", low):
        return True
    if re.search(r"\b(student portal|e-learning|academic calendar|fees & payment)\b", low):
        return True
    if re.search(r"\b(admissions?\s+){2,}", low):
        return True
    words = low.split()
    if len(words) >= 5:
        from collections import Counter
        if max(Counter(words).values()) >= 3:
            return True
    return False


def title_snippet_coherent(title: str, snippet: str) -> bool:
    """Title and description must describe the same opportunity."""
    t = (title or "").lower()
    s = re.sub(r"^\[listing\]\s*", "", (snippet or "").lower()).strip()
    if not t or not s:
        return True
    if s == t.lower() or s.startswith(t.lower()[: min(24, len(t))]):
        return True
    t_words = {w for w in re.findall(r"[a-z]{4,}", t)}
    s_words = {w for w in re.findall(r"[a-z]{4,}", s)}
    if not t_words:
        return True
    overlap = t_words & s_words
    if overlap:
        return True
    long_t = [w for w in t_words if len(w) >= 6]
    return any(w in s for w in long_t)


def extract_listing_detail(url: str, fallback_title: str = "") -> Dict[str, str]:
    """Visit the individual opportunity page and read real title + description."""
    html = fetch_page_html(url, timeout=12)
    if not html.strip():
        return {}

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
        tag.decompose()
    # derive domain early — used in title heuristics and org detection
    domain = urlparse(url).netloc.replace("www.", "")
    title = ""
    for sel in (
        ("meta", {"property": "og:title"}),
        ("meta", {"name": "twitter:title"}),
    ):
        tag = soup.find(sel[0], sel[1])
        if tag and tag.get("content"):
            title = polish_listing_title(tag["content"])
            if title and not is_junk_listing_title(title):
                break
            title = ""

    if not title:
        h1 = soup.find("h1")
        if h1:
            title = polish_listing_title(h1.get_text(" ", strip=True))

    if not title or is_junk_listing_title(title) or _generic_site_title(title, domain):
        title = polish_listing_title(fallback_title)

    snippet = ""
    for sel in (
        ("meta", {"property": "og:description"}),
        ("meta", {"name": "description"}),
    ):
        tag = soup.find(sel[0], sel[1])
        if tag and tag.get("content"):
            snippet = re.sub(r"\s+", " ", tag["content"].strip())[:280]
            if len(snippet) >= 30:
                break
            snippet = ""

    if len(snippet) < 30:
        root = soup.find("article") or soup.find("main") or soup.body
        if root:
            for p in root.find_all("p", limit=8):
                text = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
                if len(text) >= 40 and not text.lower().startswith(("click here", "read more", "share")):
                    snippet = text[:280]
                    break

    page_text = soup.get_text(" ", strip=True)[:3500]
    deadline = detect_deadline(page_text)
    domain = urlparse(url).netloc.replace("www.", "")

    org = ""
    for sel in (
        ("meta", {"property": "og:site_name"}),
        ("meta", {"name": "author"}),
    ):
        tag = soup.find(sel[0], sel[1])
        if tag and tag.get("content"):
            org = clean_organization(tag["content"], domain, title)
            if org:
                break

    location = detect_district(f"{title} {snippet} {page_text[:600]}") or ""
    loc_label = f"{location}, Rwanda" if location else "Rwanda"

    out: Dict[str, str] = {}
    if title:
        out["title"] = title
    if snippet:
        out["snippet"] = snippet
    if deadline:
        out["deadline"] = deadline
    if org:
        out["organization"] = org
    out["location"] = loc_label
    if location:
        out["district"] = location
    return out


def _generic_site_title(title: str, domain: str) -> bool:
    t = (title or "").lower().strip()
    if len(t) < 10:
        return True
    if _SITE_TAGLINE_TITLE.search(t) or is_article_or_listicle_title(t):
        return True
    host = (domain or "").split(".")[0].replace("-", " ").lower()
    if host and host in t and len(t) <= len(host) + 10:
        return True
    # Brand + motto combos e.g. "Scholarships - Free digital opportunities"
    if re.search(r"\bfree\s+digital\s+opportunities?\b", t):
        return True
    if "fdo" in (domain or "").lower() and t.startswith("scholarships"):
        return True
    return t in (
        "mk scholars",
        "home",
        "scholarships",
        "opportunities",
        "news",
        "scholarships - free digital opportunities",
        "free digital opportunities",
    )


def enrich_listing_from_detail_page(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch apply URL and replace title/snippet/org with content from that page."""
    url = (item.get("apply_url") or "").strip()
    if not url or not is_deep_opportunity_url(url):
        return None

    detail = extract_listing_detail(url, fallback_title=item.get("title") or "")
    if not detail:
        return None

    out = dict(item)
    domain = (item.get("source_domain") or urlparse(url).netloc or "").replace("www.", "")
    link_title = polish_listing_title(item.get("title") or "")

    new_title = detail.get("title") or link_title
    new_title = polish_listing_title(new_title)
    if _generic_site_title(new_title, domain) and link_title:
        new_title = link_title
    if new_title and not is_junk_listing_title(new_title):
        out["title"] = new_title

    orig_snippet = re.sub(r"^\[listing\]\s*", "", (item.get("snippet") or ""), flags=re.I).strip()
    snippet_body = detail.get("snippet") or ""
    if snippet_body and title_snippet_coherent(out.get("title") or "", snippet_body):
        out["snippet"] = f"{EXTRACTED_SNIPPET_PREFIX}{snippet_body}"
    elif orig_snippet and title_snippet_coherent(out.get("title") or "", orig_snippet):
        out["snippet"] = f"{EXTRACTED_SNIPPET_PREFIX}{orig_snippet[:280]}"
    elif out.get("title"):
        out["snippet"] = f"{EXTRACTED_SNIPPET_PREFIX}{out['title']}"
    else:
        return None

    if detail.get("deadline"):
        out["deadline"] = detail["deadline"]
    if detail.get("location") and detail.get("district"):
        out["location"] = detail["location"]
        out["district"] = detail["district"]

    org = detail.get("organization") or clean_organization(
        item.get("organization") or "",
        domain,
        out.get("title") or "",
    )
    out["organization"] = clean_organization(org, domain, out.get("title") or "")

    loc = (out.get("location") or "").strip()
    title_low = (out.get("title") or "").lower()
    if loc and "rwanda" not in loc.lower():
        if loc.lower() not in title_low and not out.get("district"):
            out["location"] = "Rwanda"
            out["district"] = ""
    return out


def _guess_category(text: str, site_categories: List[str], fallback: str = "program") -> str:
    blob = (text or "").lower()
    scores: Dict[str, int] = {}
    for cat, hints in _CATEGORY_FROM_TEXT.items():
        scores[cat] = sum(1 for h in hints if re.search(h, blob))

    if re.search(r"\binternational\b", blob):
        scores["internship"] = max(0, scores.get("internship", 0) - 3)

    # Title says "program" — prefer program only when no stronger category in title
    if re.search(r"\bprogram(me)?\b", blob):
        if not re.search(r"\b(scholarships?|jobs?|vacanc|internships?|competitions?|contests?)\b", blob):
            scores["program"] += 4
        if not re.search(r"\b(training|tvet|bootcamp|workshop|skills development)\b", blob):
            scores["training"] = max(0, scores.get("training", 0) - 2)

    if scores.get("training", 0) and scores.get("program", 0):
        if re.search(r"\b(training|tvet|skills|workshop|bootcamp)\b", blob):
            scores["training"] += 2
        if re.search(r"\b(fellowship|youth program|empower)\b", blob):
            scores["program"] += 2

    best_cat, best_score = max(scores.items(), key=lambda x: x[1], default=(None, 0))
    if best_score > 0:
        return best_cat
    if site_categories:
        return site_categories[0]
    return fallback


def category_from_title(title: str) -> Optional[str]:
    """Strong signals from listing title — must match the tag shown to youth."""
    t = (title or "").lower()
    if re.search(r"\binternational\b", t):
        pass
    elif re.search(r"\binternships?\b", t) or (
        re.search(r"\bintern\b", t) and not re.search(r"\binternational\b", t)
    ):
        return "internship"
    elif re.search(
        r"\b(scholarships?|bursaries?|bursary|grants?|fellowships?)\b"
        r"|\bscholars?\s+program(me)?\b"
        r"|\bfoundation\s+scholars?\b"
        r"|\bmastercard\s+foundation\s+scholars?\b"
        r"|\bfully\s+funded\b"
        r"|\btuition\s+(fee\s+)?waiver\b",
        t,
    ):
        return "scholarship"
    elif re.search(r"\b(jobs?|vacancies?|vacancy|employment|hiring|recruitment)\b", t) or (
        re.search(r"\bjob\b", t) and not re.search(r"\bprogram", t)
    ):
        return "job"
    elif re.search(r"\benseignants?\b", t):
        return "job"
    elif re.search(r"\b(competitions?|contests?|hackathons?)\b", t) or (
        re.search(r"\bchallenge\b", t) and not re.search(r"\bprogram", t)
    ):
        return "competition"
    elif re.search(
        r"\b(training|tvet|bootcamp|workshop|skills development|accreditation)\b",
        t,
    ):
        return "training"
    elif re.search(r"\b(free\s+)?(online\s+)?courses?\b|mooc\b", t):
        return "free_course"
    elif re.search(r"\bprogram(me)?\b", t):
        return "program"
    return None


def align_category_with_title(title: str, category: str, snippet: str = "") -> str:
    """Ensure stored/displayed category matches what the listing title/snippet says."""
    from_title = category_from_title(title)
    if from_title:
        return from_title
    if snippet:
        from_snippet = category_from_title(f"{title} {snippet}")
        if from_snippet:
            return from_snippet
    return (category or "program").lower().strip()


def refine_listing_category(
    title: str,
    blob: str,
    site_categories: List[str],
    guess: str,
) -> str:
    """Keyword pass + title alignment; optional RoBERTa when INZIRA_HARVEST_USE_ML=1."""
    improved = _guess_category(f"{title} {blob}", site_categories, guess)
    improved = align_category_with_title(title, improved)
    if os.getenv("INZIRA_HARVEST_USE_ML", "0").strip().lower() not in ("1", "true", "yes"):
        return improved
    try:
        import main as m
        text = f"{title}. {blob[:400]}"
        model_cat, conf = m.classify_category(text)
        if model_cat == "not_opportunity" or conf < 0.55:
            return improved
        if conf >= 0.72 or model_cat in site_categories:
            return model_cat
        if conf >= 0.62 and improved == model_cat:
            return model_cat
    except Exception:
        pass
    return improved


def _clean_title(text: str) -> str:
    return polish_listing_title(text)


def polish_listing_title(text: str) -> str:
    """Normalize scraped titles to clear Opportunity Desk-style headlines."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return ""

    t = _POST_TITLE_RE.sub("", t)
    t = re.sub(r"^(read more|learn more|apply now|view|details)\s*[-:]*\s*", "", t, flags=re.I)

    # Split glued blog metadata: "2023Refugees ProgramBy initiating..."
    t = re.sub(r"(\d{4})([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
    t = re.sub(
        r"\b(Program|Fellowship|Scholarship|Internship)(By|Apply|The|Deadline)\b",
        r"\1 \2",
        t,
        flags=re.I,
    )

    # Drop description tail accidentally merged into title
    t = re.split(
        r"\b(By initiating|Applications are|Apply now|Deadline:|Read more|Click here)\b",
        t,
        maxsplit=1,
        flags=re.I,
    )[0].strip()

    # ALL CAPS → readable title case (keep short acronyms)
    letters = [c for c in t if c.isalpha()]
    if len(letters) >= 12 and sum(1 for c in letters if c.isupper()) / len(letters) > 0.85:
        words = []
        for w in t.split():
            if w.isupper() and len(w) <= 5:
                words.append(w)
            else:
                words.append(w.capitalize() if w.isupper() else w)
        t = " ".join(words)

    return t[:120].strip(" -|,")


# Supplier / government procurement — not youth-facing opportunities.
_PROCUREMENT_TITLE_LEAD = re.compile(
    r"^(tender\s+notice|request\s+for\s+(quotation|quotations|proposal|proposals|tender)|"
    r"rfq\b|invitation\s+(to|for)\s+bid|call\s+for\s+(quotation|quotations|tenders?)|"
    r"framework\s+contract|notice\s+of\s+(intent\s+to\s+award|award)|"
    r"call\s+for\s+proposals\s+to\s+be\s+funded)",
    re.I,
)
_TOR_PROCUREMENT = re.compile(
    r"^terms\s+of\s+reference\s*(\(?\s*tor\s*\)?\s*)?for\s+"
    r"(supply|delivery|office\s+renovation|the\s+supply|end\s+term\s+evaluation|"
    r"evaluation\s+to\s+determine|facilitators\s+of)",
    re.I,
)
_EOI_SUPPLIER = re.compile(
    r"^(call\s+for\s+)?expression\s+of\s+interest\s*(\(?\s*eoi?\s*\)?\s*)?"
    r"(for\s+)?(construction|rehabilitation|provision|supply|the\s+provision|"
    r"organization(al)?\s+development|implementation\s+of)",
    re.I,
)
_YOUTH_POSITION_SIGNAL = re.compile(
    r"\b(vacanc(y|ies)|position|officer|manager|intern(ship)?|trainee|lecturer|"
    r"analyst|coordinator|attachment|graduate\s+program|fellowship|scholarship|"
    r"bursary|recruitment|now\s+hiring|job\s+title|reporting\s+to|assistant\s+to\s+the)\b",
    re.I,
)
_KINYARWANDA_TENDER = re.compile(
    r"^itangazo\s+.*\b(isoko|kugemura|gupiganira|abati|ibikomo)\b",
    re.I,
)


def is_procurement_listing(title: str, text: str = "") -> bool:
    """
    True for tender notices, RFQs, supplier EOIs, and similar B2B procurement posts.
    Youth jobs (e.g. Procurement Officer vacancy) are not procurement content.
    """
    t = polish_listing_title(title or "")
    if not t:
        return False
    low = t.lower()
    blob = f"{t} {text or ''}".lower()

    if _YOUTH_POSITION_SIGNAL.search(t) and not _PROCUREMENT_TITLE_LEAD.match(t):
        if re.search(r"\b(procurement|supply)\s+officer\b", t, re.I):
            return False
        if not low.startswith(("tender", "rfq", "request for", "call for quotation")):
            return False

    if _PROCUREMENT_TITLE_LEAD.match(t):
        return True
    if _TOR_PROCUREMENT.match(t):
        return True
    if _EOI_SUPPLIER.match(t):
        return True
    if _KINYARWANDA_TENDER.search(t):
        return True
    if low.startswith("call for proposals") and not _YOUTH_POSITION_SIGNAL.search(blob):
        return True
    if re.match(r"^request for\s+\w*\s*quotation", low):
        return True
    if re.search(r"\bframework\s+contract\b", low):
        return True
    if re.search(r"\btender\s+for\b", t, re.I) and not _YOUTH_POSITION_SIGNAL.search(t):
        return True
    if re.match(r"^(call\s+for\s+)?expression\s+of\s+interest\b", t, re.I):
        if not _YOUTH_POSITION_SIGNAL.search(t):
            return True
    return False


_GUIDE_OR_LISTICLE_TITLE = re.compile(
    r"(?i)^\s*("
    r"finding\s+\w+"
    r"|how\s+to\s+(find|get|apply|win)\b"
    r"|guide\s+to\b"
    r"|tips?\s+for\s+(finding|getting)\b"
    r"|everything\s+you\s+need\s+to\s+know\b"
    r"|top\s+\d+\b"
    r"|\d+\s+remote\b.{0,60}\b(opportunities?|jobs?|freelance)\b"
    r"|\d+\s+freelance\b"
    r"|.+\bopportunities?\s+available\b"
    r")"
)
_SITE_TAGLINE_TITLE = re.compile(
    r"(?i)^\s*("
    r"scholarships?\s*[-–|:]\s*free\s+digital\s+opportunities?"
    r"|free\s+digital\s+opportunities?\s*$"
    r"|scholarships?\s+and\s+opportunities?\s*$"
    r")"
)


def is_article_or_listicle_title(title: str) -> bool:
    """True for guide/listicle/roundup pages that are not single youth listings."""
    t = (title or "").strip()
    if not t:
        return True
    if _GUIDE_OR_LISTICLE_TITLE.search(t) or _SITE_TAGLINE_TITLE.search(t):
        return True
    low = t.lower()
    if re.search(r"\b(list\s+of|round\s*-?\s*up|compiled\s+list|step-by-step\s+guide)\b", low):
        return True
    return False


def is_junk_listing_title(title: str) -> bool:
    t = (title or "").strip()
    if len(t) < 12:
        return True
    low = t.lower()
    if _SECTION_HEADING_RE.match(t) or _SECTION_HEADING_RE.match(low):
        return True
    if low.rstrip().endswith(":") and len(t) < 45:
        return True
    if "program objectives" in low or "unlock your future" in low:
        return True
    if low in _JUNK_TITLE_PHRASES or low in _NAV_ONLY_TITLES:
        return True
    if is_article_or_listicle_title(t):
        return True
    if re.match(r"^(application\s*link|apply\s*here|click\s*here)$", low):
        return True
    if re.match(r"^post\d", low):
        return True
    if low.startswith("permanent link to:"):
        return True
    if re.match(r"^(admission requirements|how to apply|track application)", low):
        return True
    if re.match(r"^\[?email\s*protected\]?$", low) or "@" in t and " " not in t.strip():
        return True
    if re.match(r"^opportunities:\s*\d+\s*open\s*\|", low):
        return True
    if is_nav_portal_title(t):
        return True
    if re.match(r"^(internship program objectives|program objectives|unlock your future|objectives|about the program|where to apply)\s*:?\s*$", low):
        return True
    if low.endswith(":") and len(t) < 40:
        return True
    if _GENERIC_TITLE_RE.match(t):
        return True
    # Mostly non-letters (garbled scrape)
    alpha = sum(1 for c in t if c.isalpha())
    if alpha < len(t) * 0.45:
        return True
    return False


def _same_host(base_url: str, href: str) -> bool:
    try:
        return urlparse(base_url).netloc.replace("www.", "") == urlparse(href).netloc.replace("www.", "")
    except Exception:
        return False


def _is_quality_listing(title: str, href: str, context: str = "") -> bool:
    title = polish_listing_title(title)
    if is_junk_listing_title(title):
        return False
    blob = f"{title} {context} {href}".lower()
    if not _LINK_HINT.search(blob):
        return False
    return True


def _category_matches_title(title: str, category: str) -> bool:
    return align_category_with_title(title, category) == (category or "").lower().strip()


def detect_district(text: str, districts: Optional[List[str]] = None) -> str:
    """Parse Rwanda district name from listing or page text."""
    districts = districts or RWANDA_DISTRICTS
    blob = (text or "").lower()
    for name in districts:
        if name.lower() in blob:
            return name
    if any(a in blob for a in _KIGALI_ALIASES):
        return "Gasabo"
    return ""


def detect_deadline(text: str) -> str:
    m = _DEADLINE_RE.search(text or "")
    return m.group(1).strip() if m else ""


def _district_from_location(location: str, districts: Optional[List[str]] = None) -> str:
    return detect_district(location or "", districts)


def fallback_opportunities(site: Dict[str, Any], districts: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """One opportunity card per category the portal hosts."""
    cats = site.get("categories") or []
    if isinstance(cats, str):
        try:
            cats = json.loads(cats)
        except Exception:
            cats = [cats]
    if not cats:
        cats = ["program"]

    name = site.get("name") or site.get("organization") or site.get("domain") or "Portal"
    org = site.get("organization") or name
    location = site.get("location") or "Rwanda"
    district = _district_from_location(location, districts)
    apply_url = site.get("apply_link") or site.get("url") or ""
    snippet = site.get("snippet") or f"Browse and apply for {hosts_label(cats)} on the official portal."
    trust = float(site.get("trust_score") or 0)
    source_url = site.get("url") or apply_url
    domain = site.get("domain") or ""

    out: List[Dict[str, Any]] = []
    for cat in cats:
        if cat not in INZIRA_CATEGORIES:
            continue
        title = f"{_CATEGORY_TITLES.get(cat, cat.replace('_', ' ').title())} at {name}"
        out.append({
            "title": title,
            "category": cat,
            "organization": org,
            "location": location,
            "district": district,
            "deadline": site.get("deadline") or "",
            "snippet": f"{PORTAL_SNIPPET_PREFIX}Browse verified {hosts_label([cat])} on {name}.",
            "apply_url": apply_url,
            "source_url": source_url,
            "source_domain": domain,
            "trust_score": trust,
        })
    return out or [{
        "title": f"Opportunities at {name}",
        "category": "program",
        "organization": org,
        "location": location,
        "district": district,
        "deadline": "",
        "snippet": f"{PORTAL_SNIPPET_PREFIX}{snippet}",
        "apply_url": apply_url,
        "source_url": source_url,
        "source_domain": domain,
        "trust_score": trust,
    }]


def extract_from_html(
    html: str,
    base_url: str,
    site: Dict[str, Any],
    districts: Optional[List[str]] = None,
    max_items: int = 12,
) -> List[Dict[str, Any]]:
    if not html.strip():
        return fallback_opportunities(site, districts)

    site_cats = site.get("categories") or []
    if isinstance(site_cats, str):
        try:
            site_cats = json.loads(site_cats)
        except Exception:
            site_cats = [site_cats]

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    seen: set[str] = set()
    found: List[Dict[str, Any]] = []
    org = site.get("organization") or site.get("name") or site.get("domain") or ""
    location = site.get("location") or "Rwanda"
    district = _district_from_location(location, districts)
    trust = float(site.get("trust_score") or 0)
    source_url = site.get("url") or base_url
    domain = site.get("domain") or ""
    page_text = soup.get_text(" ", strip=True)[:4000]

    def add(title: str, href: str, cat: Optional[str] = None, context: str = "") -> None:
        title = polish_listing_title(title)
        if not _is_quality_listing(title, href, context):
            return
        href = urljoin(base_url, href)
        if not is_deep_opportunity_url(href):
            return
        key = href.lower().rstrip("/")
        if key in seen:
            return
        seen.add(key)
        blob = f"{title} {context or ''}"
        category = cat or refine_listing_category(title, blob, site_cats, _guess_category(f"{title} {href}", site_cats))
        if not _category_matches_title(title, category):
            return
        item_district = detect_district(blob, districts)
        if item_district:
            item_location = f"{item_district}, Rwanda"
        else:
            item_district = ""
            item_location = "Rwanda (national)"
        detail = re.sub(r"\s+", " ", (context or "").strip())[:220]
        if not detail or detail.lower() == title.lower():
            detail = title
        found.append({
            "title": title,
            "category": category,
            "organization": clean_organization(org, domain, title),
            "location": item_location,
            "district": item_district,
            "deadline": detect_deadline(blob),
            "snippet": f"{EXTRACTED_SNIPPET_PREFIX}{detail}",
            "apply_url": href,
            "source_url": source_url,
            "source_domain": domain,
            "trust_score": trust,
        })

    for sel in _ARTICLE_SELECTORS:
        for link in soup.select(sel):
            href = (link.get("href") or "").strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            text = (link.get("title") or link.get_text() or "").strip()
            parent = link.find_parent("article") or link.find_parent("li") or link.parent
            ctx = parent.get_text(" ", strip=True)[:200] if parent else ""
            add(text, href, context=ctx)
            if len(found) >= max_items:
                break
        if len(found) >= max_items:
            break

    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").strip()
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = urljoin(base_url, href)
        if not _same_host(base_url, full) and not _LINK_HINT.search(href):
            continue
        blob = f"{text} {href}"
        if not _LINK_HINT.search(blob):
            continue
        add(text, href)
        if len(found) >= max_items:
            break

    if len(found) < max_items:
        for li in soup.find_all("li"):
            link = li.find("a", href=True)
            if not link:
                continue
            text = (li.get_text() or link.get_text() or "").strip()
            href = link["href"].strip()
            if not _LINK_HINT.search(f"{text} {href}"):
                continue
            add(text, href)
            if len(found) >= max_items:
                break

    if len(found) < max_items:
        for card in soup.select("article, .post, .job, .vacancy, .listing, .opportunity, .card"):
            link = card.find("a", href=True)
            if not link:
                continue
            title = _clean_title(link.get_text() or card.get_text())
            if len(title) < 8:
                continue
            add(title, link["href"], context=card.get_text())
            if len(found) >= max_items:
                break

    if found:
        return found[:max_items]

    return fallback_opportunities(site, districts)


def extract_for_website(
    site: Dict[str, Any],
    html: Optional[str] = None,
    districts: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    url = site.get("url") or site.get("apply_link") or ""
    page_html = html if html is not None else fetch_page_html(url)
    return extract_from_html(page_html, url, site, districts=districts)
