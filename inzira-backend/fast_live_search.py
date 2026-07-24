"""
Fast parallel live search — open-web discovery + quick listing extraction.

Runs under a strict time budget so youth search feels instant while still
finding new portals and individual opportunities (not only pre-stored registry).
"""

from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

from match_engine import RWANDA_DISTRICTS
from rwanda_sources import SKIP_DOMAINS, domain_of

FAST_SEARCH_BUDGET_S = float(os.getenv("INZIRA_FAST_SEARCH_BUDGET", "10"))
FAST_SEARCH_MAX_SITES = int(os.getenv("INZIRA_FAST_SEARCH_MAX_SITES", "4"))
FAST_SEARCH_MAX_PAGES_PER_SITE = int(os.getenv("INZIRA_FAST_SEARCH_MAX_PAGES", "3"))
FAST_SEARCH_MAX_URLS = FAST_SEARCH_MAX_SITES * FAST_SEARCH_MAX_PAGES_PER_SITE
FAST_SEARCH_WORKERS = int(os.getenv("INZIRA_FAST_SEARCH_WORKERS", "6"))
FAST_FETCH_TIMEOUT = float(os.getenv("INZIRA_FAST_FETCH_TIMEOUT", "4.0"))

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def extract_district_from_query(query: str) -> Optional[str]:
    if not query:
        return None
    q = query.lower()
    for district in RWANDA_DISTRICTS:
        if re.search(rf"\b{re.escape(district.lower())}\b", q):
            return district
    return None


def build_fast_queries(
    user_query: str,
    category: Optional[str],
    district: Optional[str],
) -> List[str]:
    q = (user_query or "").strip()
    cat = (category or "").replace("_", " ") or "opportunities"
    dist = f" {district}" if district else " Rwanda"
    base = q or cat
    queries = [
        f"{base}{dist} {cat} apply 2025 2026",
        f"Rwanda{dist} {cat} youth apply online",
        f"{cat}{dist} Rwanda vacancies scholarships apply",
    ]
    seen: Set[str] = set()
    out: List[str] = []
    for item in queries:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out[:3]


def discover_result_urls(
    user_query: str,
    category: Optional[str],
    district: Optional[str],
    skip_domains: Optional[Set[str]] = None,
    max_sites: int = FAST_SEARCH_MAX_SITES,
    max_pages_per_site: int = FAST_SEARCH_MAX_PAGES_PER_SITE,
) -> List[Dict[str, str]]:
    """DuckDuckGo search — up to N sites × M pages, fetched in parallel later."""
    skip = skip_domains or set()
    queries = build_fast_queries(user_query, category, district)
    by_domain: Dict[str, List[Dict[str, str]]] = {}

    with DDGS() as ddgs:
        for rw_query in queries:
            if sum(len(v) for v in by_domain.values()) >= max_sites * max_pages_per_site:
                break
            try:
                for r in list(ddgs.text(rw_query, max_results=10)):
                    url = (r.get("href") or "").strip()
                    if not url or not url.startswith("http"):
                        continue
                    dom = domain_of(url)
                    if not dom or dom in skip:
                        continue
                    if any(s in dom for s in SKIP_DOMAINS):
                        continue
                    bucket = by_domain.setdefault(dom, [])
                    key = url.lower().rstrip("/")
                    if any(x["url"].lower().rstrip("/") == key for x in bucket):
                        continue
                    if len(bucket) >= max_pages_per_site:
                        continue
                    bucket.append({
                        "url": url,
                        "title": (r.get("title") or "").strip(),
                        "snippet": (r.get("body") or "").strip(),
                        "domain": dom,
                    })
                    if len(by_domain) >= max_sites and all(
                        len(v) >= max_pages_per_site for v in by_domain.values()
                    ):
                        break
            except Exception as exc:
                print(f"  Fast discovery error ({rw_query[:48]}…): {exc}")

    ordered_domains = sorted(by_domain.keys(), key=lambda d: len(by_domain[d]), reverse=True)[:max_sites]
    out: List[Dict[str, str]] = []
    for dom in ordered_domains:
        out.extend(by_domain[dom][:max_pages_per_site])
    return out


def _fetch_html(url: str) -> str:
    try:
        res = requests.get(url, headers=_HEADERS, timeout=FAST_FETCH_TIMEOUT)
        res.raise_for_status()
        return res.text
    except Exception:
        return ""


def _page_text_from_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ", strip=True).split()[:400])


def _listing_to_api(item: Dict[str, Any]) -> Dict[str, Any]:
    apply_url = item.get("apply_url") or item.get("url") or ""
    return {
        "url": apply_url,
        "title": item.get("title") or "",
        "category": item.get("category") or "program",
        "categories": [item.get("category") or "program"],
        "trust_score": float(item.get("trust_score") or 0),
        "organization": item.get("organization") or "",
        "deadline": item.get("deadline") or "",
        "eligibility": item.get("eligibility") or "",
        "location": item.get("location") or "Rwanda",
        "district": item.get("district") or "",
        "apply_link": apply_url,
        "snippet": item.get("snippet") or "",
        "source_domain": item.get("source_domain") or domain_of(apply_url),
        "source": "live_fast",
    }


def _scrape_one_url(
    cand: Dict[str, str],
    category: Optional[str],
    district: Optional[str],
) -> List[Dict[str, Any]]:
    import main as m
    from opportunity_extractor import EXTRACTED_SNIPPET_PREFIX, extract_from_html
    from listing_quality import is_publishable_listing
    from inzira_features import compute_listing_trust

    url = cand["url"]
    dom = cand.get("domain") or domain_of(url)
    html = _fetch_html(url)
    if not html:
        return []

    page_text = _page_text_from_html(html)
    combined = f"{cand.get('title', '')} {cand.get('snippet', '')} {page_text}"
    if not m.is_rwanda_relevant(combined, url):
        return []

    site = {
        "domain": dom,
        "name": cand.get("title") or dom,
        "url": f"https://{dom}",
        "organization": cand.get("title") or dom,
        "categories": [category] if category else ["program"],
        "trust_score": 72,
        "location": f"{district}, Rwanda" if district else "Rwanda",
    }

    listings = extract_from_html(
        html,
        url,
        site,
        districts=RWANDA_DISTRICTS,
        max_items=6,
    )

    out: List[Dict[str, Any]] = []
    if listings:
        for item in listings:
            api = _listing_to_api(item)
            api["trust_score"] = compute_listing_trust(api, site_trust=float(site["trust_score"]))
            if category and api.get("category") != category:
                related = {category, "program", "training"}
                if api.get("category") not in related:
                    continue
            if is_publishable_listing({
                "title": api.get("title"),
                "category": api.get("category"),
                "snippet": api.get("snippet", "").replace(EXTRACTED_SNIPPET_PREFIX, ""),
                "location": api.get("location"),
                "organization": api.get("organization"),
                "deadline": api.get("deadline"),
                "apply_url": api.get("apply_link"),
                "source_domain": api.get("source_domain"),
            }):
                out.append(api)
        return out

    # Single opportunity page (not a portal listing many jobs)
    ai = m.verify_with_ai(page_text, category)
    if not ai:
        from website_verifier import verify_website_host
        ai = verify_website_host(page_text, url, category)
    if not ai:
        return []

    cat, trust = ai
    title = cand.get("title") or dom.replace(".", " ").title()
    snippet = page_text[:280] + ("..." if len(page_text) > 280 else "")
    api = m.build_result(
        url=url,
        title=title,
        snippet=snippet,
        category=cat,
        trust_score=trust,
        page_text=page_text,
        organization=site["organization"],
    )
    api["source_domain"] = dom
    api["source"] = "live_fast"
    if district:
        api["district"] = district
    if is_publishable_listing({
        "title": api.get("title"),
        "category": api.get("category"),
        "snippet": api.get("snippet"),
        "location": api.get("location"),
        "organization": api.get("organization"),
        "deadline": api.get("deadline"),
        "apply_url": api.get("apply_link"),
        "source_domain": dom,
    }):
        out.append(api)
    return out


def run_fast_live_search(
    query: str,
    category: Optional[str] = None,
    district: Optional[str] = None,
    max_results: int = 15,
    skip_domains: Optional[Set[str]] = None,
    registry=None,
    progress: Optional[Callable[[int, int, str], None]] = None,
    budget_s: float = FAST_SEARCH_BUDGET_S,
    max_sites: int = FAST_SEARCH_MAX_SITES,
    max_pages_per_site: int = FAST_SEARCH_MAX_PAGES_PER_SITE,
) -> List[Dict[str, Any]]:
    """
    Discover pages on the open web, extract listings, AI-filter scams/junk.
    Returns API-ready opportunity dicts within budget_s seconds (default 10s).
    """
    started = time.monotonic()
    district = district or extract_district_from_query(query)
    candidates = discover_result_urls(
        query,
        category,
        district,
        skip_domains=skip_domains,
        max_sites=max_sites,
        max_pages_per_site=max_pages_per_site,
    )
    if not candidates:
        return []

    site_domains = []
    for cand in candidates:
        dom = cand.get("domain") or domain_of(cand.get("url", ""))
        if dom and dom not in site_domains:
            site_domains.append(dom)
    sites_total = len(site_domains) or 1
    if progress:
        progress(0, sites_total, f"Quick web check: {sites_total} site{'s' if sites_total != 1 else ''}…")

    print(f"  Fast live: scraping {len(candidates)} URLs across {sites_total} sites (budget {budget_s}s)...")
    collected: List[Dict[str, Any]] = []
    seen_apply: Set[str] = set()
    sites_checked: Set[str] = set()

    workers = min(FAST_SEARCH_WORKERS, len(candidates))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_scrape_one_url, cand, category, district): cand
            for cand in candidates
        }
        for fut in as_completed(futures):
            if time.monotonic() - started >= budget_s:
                break
            cand = futures[fut]
            dom = cand.get("domain") or domain_of(cand.get("url", ""))
            try:
                for item in fut.result():
                    key = (item.get("apply_link") or item.get("url") or "").lower().rstrip("/")
                    if not key or key in seen_apply:
                        continue
                    seen_apply.add(key)
                    collected.append(item)
            except Exception as exc:
                print(f"  Fast scrape failed {cand.get('url', '')[:60]}: {exc}")
            if dom and dom not in sites_checked:
                sites_checked.add(dom)
                if progress:
                    progress(
                        len(sites_checked),
                        sites_total,
                        f"Quick web check: {len(sites_checked)} site{'s' if len(sites_checked) != 1 else ''}…",
                    )
            if len(collected) >= max_results:
                break

    if registry and collected:
        try:
            registry.upsert_live_listings(collected)
            for item in collected[:8]:
                dom = item.get("source_domain") or domain_of(item.get("url", ""))
                if dom:
                    registry.upsert_website(
                        domain=dom,
                        name=item.get("organization") or dom,
                        url=f"https://{dom}",
                        categories=item.get("categories") or [item.get("category") or "program"],
                        trust_score=float(item.get("trust_score") or 70),
                        has_open=True,
                        verified=True,
                        snippet=item.get("snippet") or "",
                        organization=item.get("organization") or dom,
                        location=item.get("location") or "Rwanda",
                        apply_link=item.get("apply_link") or item.get("url") or f"https://{dom}",
                        source="live_fast",
                    )
        except Exception as exc:
            print(f"  Fast live persist skipped: {exc}")

    elapsed = time.monotonic() - started
    print(f"  Fast live: {len(collected)} listings in {elapsed:.1f}s")
    return collected[:max_results]
