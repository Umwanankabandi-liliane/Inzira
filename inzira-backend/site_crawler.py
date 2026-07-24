"""
Deep per-site crawler for Inzira harvest.

Crawls listing pages, pagination, sitemaps, and internal links on ONE domain,
extracts detail pages, and passes each through verify_with_ai.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from detail_page_extractor import extract_detail_page, is_js_shell_page
from opportunity_extractor import EXTRACTED_SNIPPET_PREFIX, is_deep_opportunity_url, is_junk_listing_title, is_long_single_slug_path, is_procurement_listing
from rwanda_sources import DEFAULT_HARVEST_BUDGETS, DISCOVERED_HARVEST_BUDGETS, harvest_config_for, is_configured_source, listing_urls_for

USER_AGENT = "InziraBot/1.0 (+student research project, Rwanda)"
REQUEST_TIMEOUT = 20
DELAY_BETWEEN_REQUESTS_S = 1.5
THIN_DOMAIN_PROBE_PAGES = 3
THIN_DOMAIN_MAX_PAGES = 10

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source",
})

_OPPORTUNITY_PATH_RE = re.compile(
    r"/(?:jobs?|vacanc(?:y|ies)|careers?|scholar(?:ship)?s?|intern(?:ship)?s?|"
    r"programs?|trainings?|competitions?|courses?|apply|applications?|"
    r"opportunities?|announcements?|posts?|openings?|tenders?|category)/",
    re.I,
)

_PAGINATION_RE = re.compile(
    r"(?:^|[?&])(?:page|paged|p|offset)=\d+",
    re.I,
)

_PAGINATION_PATH_RE = re.compile(r"/page/\d+/?$", re.I)

_JOB_BOARD_DETAIL_RE = re.compile(r"/job/[^/]+/?$", re.I)
_NOISE_LISTING_RE = re.compile(r"(forms\.|all-employers|/employers)", re.I)


@dataclass
class CrawlSummary:
    domain: str = ""
    pages_fetched: int = 0
    listing_pages: int = 0
    detail_pages_found: int = 0
    passed_ml: int = 0
    stored: int = 0
    skipped_duplicate: int = 0
    skipped_robots: int = 0
    errors: int = 0
    js_rendered_suspect: bool = False
    skip_fast_applied: bool = False
    seen_detail_urls: List[str] = field(default_factory=list)
    unchanged_detail_urls: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    rejection_counts: Dict[str, int] = field(default_factory=dict)

    def record_rejection(self, reason: str) -> None:
        self.rejection_counts[reason] = self.rejection_counts.get(reason, 0) + 1

    def top_rejection(self) -> str:
        if not self.rejection_counts:
            return ""
        return max(self.rejection_counts, key=lambda k: self.rejection_counts[k])

    def as_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "pages_fetched": self.pages_fetched,
            "listing_pages": self.listing_pages,
            "detail_pages_found": self.detail_pages_found,
            "passed_ml": self.passed_ml,
            "stored": self.stored,
            "skipped_duplicate": self.skipped_duplicate,
            "skipped_unchanged": self.skipped_duplicate,
            "skipped_robots": self.skipped_robots,
            "errors": self.errors,
            "js_rendered_suspect": self.js_rendered_suspect,
            "skip_fast_applied": self.skip_fast_applied,
            "top_rejection": self.top_rejection(),
            "rejection_counts": dict(self.rejection_counts),
            "seen_detail_urls": self.seen_detail_urls,
            "unchanged_detail_urls": self.unchanged_detail_urls,
            "messages": self.messages[-20:],
        }


def normalize_url(url: str) -> str:
    try:
        parsed = urlparse((url or "").strip())
    except Exception:
        return (url or "").strip().lower().rstrip("/")
    if not parsed.scheme or not parsed.netloc:
        return (url or "").strip().lower().rstrip("/")
    q = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in _TRACKING_PARAMS]
    clean = parsed._replace(
        fragment="",
        query=urlencode(q) if q else "",
        netloc=parsed.netloc.lower(),
    )
    out = urlunparse(clean).rstrip("/")
    return out


def root_domain(host: str) -> str:
    h = (host or "").lower().replace("www.", "")
    return h


def host_on_site(url: str, site_root: str) -> bool:
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return False
    root = site_root.lower().replace("www.", "")
    return host == root or host.endswith("." + root)


def content_hash(text: str) -> str:
    blob = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(blob.encode("utf-8", errors="ignore")).hexdigest()[:20]


class DomainRobots:
    def __init__(self, base_url: str, user_agent: str = USER_AGENT):
        self.user_agent = user_agent
        self.parser = RobotFileParser()
        self._loaded = False
        self._base = base_url.rstrip("/")
        try:
            robots_url = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/robots.txt"
            self.parser.set_url(robots_url)
            res = requests.get(robots_url, headers={"User-Agent": user_agent}, timeout=REQUEST_TIMEOUT)
            # Only treat a successful text robots.txt as authoritative. Many hosts
            # return HTML 404 pages; a virgin RobotFileParser then can_fetch()=False
            # and would block the entire crawl.
            if res.ok:
                ctype = (res.headers.get("content-type") or "").lower()
                body = res.text or ""
                looks_html = "<html" in body[:200].lower() or "text/html" in ctype
                if not looks_html:
                    self.parser.parse(body.splitlines())
                    self._loaded = True
        except Exception:
            self._loaded = False

    def allowed(self, url: str) -> bool:
        if not self._loaded:
            return True
        try:
            return self.parser.can_fetch(self.user_agent, url)
        except Exception:
            return True


def discover_sitemap_urls(base_url: str, robots: DomainRobots) -> List[str]:
    found: List[str] = []
    scheme = urlparse(base_url).scheme or "https"
    host = urlparse(base_url).netloc
    candidates = [
        f"{scheme}://{host}/sitemap.xml",
        f"{scheme}://{host}/sitemap_index.xml",
        f"{scheme}://{host}/wp-sitemap.xml",
    ]
    try:
        robots_url = f"{scheme}://{host}/robots.txt"
        res = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        if res.ok:
            for line in res.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    candidates.append(line.split(":", 1)[1].strip())
    except Exception:
        pass

    seen_maps: Set[str] = set()
    for sm_url in candidates:
        sm_url = sm_url.strip()
        if not sm_url or sm_url in seen_maps:
            continue
        seen_maps.add(sm_url)
        found.extend(_parse_sitemap(sm_url, depth=0))
    return found


def _parse_sitemap(url: str, depth: int = 0) -> List[str]:
    if depth > 2:
        return []
    try:
        res = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        if not res.ok or "<" not in res.text:
            return []
        root = ET.fromstring(res.text)
    except Exception:
        return []

    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    locs: List[str] = []
    for loc in root.findall(f".//{ns}loc"):
        if loc.text:
            locs.append(loc.text.strip())

    if root.tag.endswith("sitemapindex") or any("sitemap" in (l or "").lower() for l in locs[:3]):
        nested: List[str] = []
        for child in locs[:12]:
            if child.lower().endswith(".xml"):
                nested.extend(_parse_sitemap(child, depth + 1))
        return nested
    return locs


def opportunity_like_url(url: str) -> bool:
    try:
        path = (urlparse(url).path or "").lower()
    except Exception:
        return False
    if not path or path == "/":
        return False
    if _OPPORTUNITY_PATH_RE.search(path):
        return True
    if re.search(r"/\d{4}/\d{2}/|/\d{5,}|/[\w-]{12,}/?$", path):
        return True
    if is_long_single_slug_path(path):
        return True
    return is_deep_opportunity_url(url)


def _link_hint(text: str, href: str) -> bool:
    blob = f"{text} {href}".lower()
    return bool(re.search(
        r"\b(vacanc|job|career|scholar|bursar|intern|fellow|train|program|"
        r"competition|apply|opening|position|recruit|hire|grant|course|tender)\b",
        blob,
    ))


def extract_internal_links(html: str, page_url: str, site_root: str) -> List[str]:
    links: List[str] = []
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return links
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = urljoin(page_url, href)
        if not host_on_site(full, site_root):
            continue
        norm = normalize_url(full)
        text = (a.get_text() or "").strip()
        if opportunity_like_url(norm) or _link_hint(text, href):
            links.append(norm)
    return links


def extract_pagination_links(html: str, page_url: str, site_root: str) -> List[str]:
    out: List[str] = []
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return out

    for link in soup.find_all("link", rel=True):
        rel = " ".join(link.get("rel") or []).lower()
        if "next" in rel and link.get("href"):
            full = urljoin(page_url, link["href"])
            if host_on_site(full, site_root):
                out.append(normalize_url(full))

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = (a.get_text() or "").strip().lower()
        if text in ("next", "»", "›", "older posts", "older", "next page", "next →", "→"):
            full = urljoin(page_url, href)
            if host_on_site(full, site_root):
                out.append(normalize_url(full))
        full = urljoin(page_url, href)
        if host_on_site(full, site_root):
            norm = normalize_url(full)
            if _PAGINATION_RE.search(norm) or _PAGINATION_PATH_RE.search(urlparse(norm).path or ""):
                out.append(norm)
    return list(dict.fromkeys(out))


def _visible_word_count(html: str) -> int:
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return len(re.findall(r"\b\w+\b", text))
    except Exception:
        return 0


_SHALLOW_SKIP_PATHS = frozenset({
    "about", "about-us", "contact", "terms", "terms-of-use", "privacy", "privacy-policy",
    "login", "register", "cookie", "cookies", "faq", "help", "sitemap",
})


def _looks_like_post_url(path: str) -> bool:
    """Delegate to shared long-slug / sector-page detection."""
    return is_long_single_slug_path(path or "")


_NAV_DETAIL_SKIP = ("/author/", "/category/", "/tag/", "/wp-content/", "/feed/")


def _prioritize_detail_links(links: List[str]) -> List[str]:
    """Drop author/category noise; prefer long job/scholarship slugs (fdo.net.rw etc.)."""
    unique = list(dict.fromkeys(links))
    scored: List[Tuple[int, str]] = []
    for url in unique:
        low = url.lower()
        if any(s in low for s in _NAV_DETAIL_SKIP):
            continue
        if "/page/" in low and low.rstrip("/").split("/")[-1].isdigit():
            continue
        if is_long_single_slug_path(low):
            scored.append((0, url))
        else:
            scored.append((1, url))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [u for _, u in scored]


def classify_page(html: str, url: str) -> str:
    """
    Return 'detail', 'listing', or 'skip'.
    Listing = many similar internal opportunity links; detail = substantial unique body.
    """
    try:
        parsed = urlparse(url)
        site_root = root_domain(parsed.netloc)
        path = (parsed.path or "/").strip("/").lower()
    except Exception:
        return "skip"

    leaf = path.split("/")[-1] if path else ""
    if leaf in _SHALLOW_SKIP_PATHS or path in _SHALLOW_SKIP_PATHS:
        return "skip"

    links = extract_internal_links(html, url, site_root)
    opp_links = [u for u in links if opportunity_like_url(u)]
    words = _visible_word_count(html)

    if _looks_like_post_url(path):
        if words >= 50 or extract_detail_page(html, url):
            return "detail"

    # Job-board detail URLs (e.g. jobinrwanda.com/job/slug) often embed many sidebar links.
    if re.match(r"^jobs?/[^/]+$", path):
        listing_leaves = {
            "all", "featured", "internships", "consultancy", "tender", "others",
            "public-adverts", "public", "category", "categories", "search",
        }
        if leaf not in listing_leaves:
            if words >= 40 or extract_detail_page(html, url):
                return "detail"

    if len(opp_links) >= 6:
        return "listing"
    if is_deep_opportunity_url(url):
        if words >= 50:
            return "detail"
        if extract_detail_page(html, url):
            return "detail"
    return "skip"


class DeepSiteCrawler:
    """BFS crawl of one configured source domain."""

    def __init__(
        self,
        site: Dict[str, Any],
        *,
        budgets: Optional[Dict[str, int]] = None,
        existing_hashes: Optional[Dict[str, str]] = None,
        existing_listing_urls: Optional[Set[str]] = None,
        log: Optional[Callable[[str], None]] = None,
        category_focus: Optional[str] = None,
    ):
        self.site = dict(site)
        self.category_focus = (category_focus or "").strip().lower() or None
        self.domain = (site.get("domain") or "").replace("www.", "")
        self.base_url = (site.get("url") or "").strip().rstrip("/")
        cfg = harvest_config_for(
            self.domain,
            discovered=not is_configured_source(self.domain),
        )
        self.budgets = {**cfg, **(budgets or {})}
        self.max_pages = int(self.budgets.get("max_pages", DEFAULT_HARVEST_BUDGETS["max_pages"]))
        self.max_depth = int(self.budgets.get("max_depth", DEFAULT_HARVEST_BUDGETS["max_depth"]))
        self.max_detail_pages = int(self.budgets.get("max_detail_pages", DEFAULT_HARVEST_BUDGETS["max_detail_pages"]))
        self.request_timeout = int(self.budgets.get("request_timeout", REQUEST_TIMEOUT))
        self.existing_hashes = existing_hashes or {}
        self.existing_listing_urls = {
            normalize_url(u) for u in (existing_listing_urls or set()) if u
        }
        self.log = log or (lambda _m: None)
        self.summary = CrawlSummary(domain=self.domain)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self._robots = DomainRobots(self.base_url)
        self._last_fetch_at = 0.0
        self._new_hashes: Dict[str, str] = {}

    def _pause(self) -> None:
        elapsed = time.time() - self._last_fetch_at
        if elapsed < DELAY_BETWEEN_REQUESTS_S:
            time.sleep(DELAY_BETWEEN_REQUESTS_S - elapsed)

    def _fetch(self, url: str) -> Tuple[str, str]:
        if not self._robots.allowed(url):
            self.summary.skipped_robots += 1
            return "", ""
        self._pause()
        try:
            res = self._session.get(url, timeout=self.request_timeout, allow_redirects=True)
            self._last_fetch_at = time.time()
            self.summary.pages_fetched += 1
            if not res.ok:
                return "", ""
            ctype = (res.headers.get("content-type") or "").lower()
            if "html" not in ctype and "text" not in ctype:
                return "", ""
            return res.text, res.url
        except Exception as exc:
            self.summary.errors += 1
            self.summary.messages.append(f"fetch {url}: {exc}")
            self._last_fetch_at = time.time()
            return "", ""

    def _seeds(self) -> List[str]:
        seeds = listing_urls_for(self.site, category_focus=self.category_focus)
        if not self.site.get("seed_strict"):
            for u in discover_sitemap_urls(self.base_url, self._robots)[:25]:
                if host_on_site(u, self.domain) and opportunity_like_url(u):
                    seeds.append(normalize_url(u))
            seeds.append(normalize_url(self.base_url))
        return list(dict.fromkeys(seeds))

    def _verify_and_build(self, extracted: Dict[str, str], page_url: str, category_hint: Optional[str]) -> Optional[dict]:
        import main as m
        from record_normalizer import normalize_extracted_record

        page_text = extracted.get("page_text") or extracted.get("snippet") or ""
        if len(page_text) < 80:
            self.summary.record_rejection("short-text")
            return None
        title = extracted.get("title") or ""
        if is_procurement_listing(title, page_text):
            self.summary.record_rejection("procurement")
            return None
        deadline_hint = extracted.get("deadline") or ""
        if not m.has_open_application_signals(page_text):
            self.summary.record_rejection("closed")
            return None
        if not m.is_rwanda_relevant(f"{extracted.get('title', '')} {page_text}", page_url):
            self.summary.record_rejection("relevance")
            return None

        ai = m.verify_with_ai(page_text, category_hint)
        if not ai:
            self.summary.record_rejection("ml-gate")
            return None
        category, trust = ai
        title = extracted.get("title") or ""
        if is_junk_listing_title(title):
            self.summary.record_rejection("junk-title")
            return None

        snippet = extracted.get("snippet") or page_text[:300]
        result = m.build_result(
            url=normalize_url(extracted.get("canonical_url") or page_url),
            title=title,
            snippet=snippet,
            category=category,
            trust_score=trust,
            page_text=page_text,
            organization=extracted.get("organization") or "",
        )
        self.summary.passed_ml += 1

        ner = {
            "organization": result.get("organization") or "",
            "deadline": result.get("deadline") or "",
            "location": result.get("location") or "",
        }
        polished = normalize_extracted_record(
            {
                "title": result.get("title") or title,
                "organization": extracted.get("organization") or result.get("organization") or "",
                "deadline": extracted.get("deadline") or result.get("deadline") or "",
                "location": extracted.get("location") or result.get("location") or "",
                "district": extracted.get("district") or "",
                "snippet": result.get("snippet") or snippet,
                "page_text": page_text,
            },
            page_url=page_url,
            domain=self.domain,
            page_text=page_text,
            ner_entities=ner,
        )
        if not polished:
            self.summary.record_rejection("normalizer")
            return None
        result.update({
            "title": polished["title"],
            "organization": polished["organization"],
            "deadline": polished["deadline"],
            "location": polished["location"],
            "snippet": polished["snippet"],
        })
        result["district"] = polished.get("district", "")
        result["category"] = category
        result["trust_score"] = trust
        return result

    def _to_registry_item(self, result: dict) -> dict:
        from opportunity_extractor import EXTRACTED_SNIPPET_PREFIX
        from record_normalizer import normalize_registry_item

        detail_url = (result.get("url") or result.get("apply_link") or "").strip()
        item = {
            "title": result.get("title") or "",
            "category": result.get("category") or "program",
            "organization": result.get("organization") or "",
            "location": result.get("location") or "",
            "district": result.get("district") or "",
            "deadline": result.get("deadline") or "",
            "eligibility": result.get("eligibility") or "",
            "snippet": f"{EXTRACTED_SNIPPET_PREFIX}{result.get('snippet') or ''}",
            "apply_url": detail_url,
            "source_url": detail_url,
            "source_domain": self.domain,
            "trust_score": float(result.get("trust_score") or 0),
        }
        return normalize_registry_item(item, domain=self.domain)

    def run(self) -> Tuple[List[dict], CrawlSummary, Dict[str, str]]:
        queue: Deque[Tuple[str, int]] = deque()
        seen_pages: Set[str] = set()
        seen_details: Set[str] = set()
        stored: List[dict] = []

        category_hint = self.category_focus
        if not category_hint:
            cats = self.site.get("categories") or []
            if isinstance(cats, str):
                try:
                    cats = json.loads(cats)
                except Exception:
                    cats = [cats]
            category_hint = cats[0] if cats else None

        for seed in self._seeds():
            if host_on_site(seed, self.domain):
                queue.append((seed, 0))

        js_shell_hits = 0
        opportunity_links_found = 0

        while queue and self.summary.pages_fetched < self.max_pages:
            url, depth = queue.popleft()
            norm = normalize_url(url)
            if norm in seen_pages or depth > self.max_depth:
                continue
            seen_pages.add(norm)

            html, final_url = self._fetch(norm)
            if not html:
                continue
            if final_url:
                norm = normalize_url(final_url)
                seen_pages.add(norm)

            if is_js_shell_page(html):
                js_shell_hits += 1
                if js_shell_hits >= 2 and self.summary.detail_pages_found == 0:
                    self.summary.js_rendered_suspect = True
                    self.summary.messages.append("early_abort: js_rendered_suspect")
                    self.log(f"  ! {self.domain}: early abort (js_rendered_suspect)")
                    break

            page_kind = classify_page(html, norm)

            if page_kind == "listing":
                self.summary.listing_pages += 1
                detail_links: List[str] = []
                other_links: List[str] = []
                for link in extract_internal_links(html, norm, self.domain):
                    if link in seen_pages or _NOISE_LISTING_RE.search(link):
                        continue
                    if opportunity_like_url(link) and is_deep_opportunity_url(link):
                        detail_links.append(link)
                    else:
                        other_links.append(link)
                job_board_details = [l for l in detail_links if _JOB_BOARD_DETAIL_RE.search(l)]
                if len(job_board_details) >= 5:
                    detail_links = list(dict.fromkeys(job_board_details))
                    other_links = []
                elif detail_links:
                    detail_links = [l for l in detail_links if not _NOISE_LISTING_RE.search(l)]
                opportunity_links_found += len(detail_links)
                if len(job_board_details) < 5:
                    for link in extract_pagination_links(html, norm, self.domain):
                        if link not in seen_pages and not _NOISE_LISTING_RE.search(link):
                            queue.appendleft((link, depth))
                for link in reversed(_prioritize_detail_links(detail_links)):
                    queue.appendleft((link, depth + 1))
                nav_cap = 0 if len(job_board_details) >= 5 else (5 if len(detail_links) >= 8 else 40)
                for link in other_links[:nav_cap]:
                    queue.append((link, depth + 1))
                if (
                    self.summary.pages_fetched >= THIN_DOMAIN_PROBE_PAGES
                    and opportunity_links_found == 0
                    and self.summary.detail_pages_found == 0
                    and self.max_pages > THIN_DOMAIN_MAX_PAGES
                ):
                    self.max_pages = THIN_DOMAIN_MAX_PAGES
                    self.summary.skip_fast_applied = True
                    self.summary.messages.append("skip_fast: thin_domain budget=10")
                    self.log(
                        f"  ! {self.domain}: skip-fast "
                        f"(no opportunity links in first {THIN_DOMAIN_PROBE_PAGES} pages)"
                    )
                continue

            if page_kind != "detail":
                continue

            if len(seen_details) >= self.max_detail_pages:
                break

            extracted = extract_detail_page(html, norm)
            if not extracted:
                continue

            detail_url = normalize_url(extracted.get("canonical_url") or norm)
            if detail_url in seen_details:
                continue
            title = extracted.get("title") or ""
            if is_junk_listing_title(title):
                continue
            seen_details.add(detail_url)
            self.summary.detail_pages_found += 1
            self.summary.seen_detail_urls.append(detail_url)

            page_text = extracted.get("page_text") or extracted.get("snippet") or ""
            h = content_hash(page_text)
            self._new_hashes[detail_url] = h
            if self.existing_hashes.get(detail_url) == h and detail_url in self.existing_listing_urls:
                self.summary.skipped_duplicate += 1
                self.summary.unchanged_detail_urls.append(detail_url)
                continue

            try:
                result = self._verify_and_build(extracted, detail_url, category_hint)
            except Exception as exc:
                self.summary.errors += 1
                self.summary.messages.append(f"verify {detail_url}: {exc}")
                continue
            if not result:
                continue

            item = self._to_registry_item(result)
            stored.append(item)
            self.summary.stored += 1

        if js_shell_hits >= 2:
            self.summary.js_rendered_suspect = True
            self.log(f"  ! {self.domain}: js_rendered_suspect ({js_shell_hits} thin pages)")

        self.log(
            f"  {self.domain}: pages={self.summary.pages_fetched} details={self.summary.detail_pages_found} "
            f"ml_ok={self.summary.passed_ml} stored={self.summary.stored} dup_skip={self.summary.skipped_duplicate} "
            f"errors={self.summary.errors}"
        )
        return stored, self.summary, self._new_hashes


def crawl_one_source(
    site: Dict[str, Any],
    *,
    budgets: Optional[Dict[str, int]] = None,
    existing_hashes: Optional[Dict[str, str]] = None,
    existing_listing_urls: Optional[Set[str]] = None,
    log: Optional[Callable[[str], None]] = None,
    category_focus: Optional[str] = None,
) -> Tuple[List[dict], CrawlSummary, Dict[str, str]]:
    crawler = DeepSiteCrawler(
        site,
        budgets=budgets,
        existing_hashes=existing_hashes,
        existing_listing_urls=existing_listing_urls,
        log=log,
        category_focus=category_focus,
    )
    return crawler.run()
