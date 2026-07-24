"""
Multi-source discovery engine — finds ALL Rwanda opportunity websites.

Sources (no .gov bias):
  1. Open web search — job boards, aggregators, NGOs (.com / .org / .rw / any TLD)
  2. Link crawl — follow outbound links from known opportunity portals
  3. Seed bootstrap — optional starting URLs only

MIFOTRA uses the registry report to see: total list + newly detected sites.
"""

import re
import time
from typing import Dict, List, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

from discovery_config import (
    DISCOVERY_QUERIES,
    DISCOVERY_DELAY_SECONDS,
    DISCOVERY_MAX_PER_QUERY,
    PORTAL_SEED_QUERIES,
)
from rwanda_sources import SKIP_DOMAINS, domain_of

LINK_CRAWL_USER_AGENT = "Mozilla/5.0 (compatible; InziraDiscovery/1.0; +https://inzira.rw)"
OPPORTUNITY_LINK_WORDS = re.compile(
    r"(job|jobs|career|vacancy|scholarship|intern|training|program|opportunity|"
    r"apply|recruit|fellowship|competition|course|hire|talent)",
    re.I,
)
RWANDA_HINT = re.compile(r"rwanda|kigali|\.rw\b", re.I)


def _is_skipped(domain: str) -> bool:
    return not domain or any(skip in domain for skip in SKIP_DOMAINS)


def _homepage(domain: str) -> str:
    return f"https://{domain}"


def _tld_bucket(domain: str) -> str:
    if domain.endswith(".gov.rw"):
        return ".gov.rw"
    if domain.endswith(".ac.rw"):
        return ".ac.rw"
    if domain.endswith(".rw"):
        return ".rw"
    if domain.endswith(".org"):
        return ".org"
    if domain.endswith(".com"):
        return ".com"
    parts = domain.rsplit(".", 1)
    return f".{parts[-1]}" if len(parts) > 1 else "other"


def discover_from_web_search(reg) -> Tuple[int, int]:
    """Search the open web per category. Returns (queued, new_domains)."""
    queued = 0
    new_domains = 0
    seen: Set[str] = set()

    all_queries: List[Tuple[str, str]] = []
    for category, queries in DISCOVERY_QUERIES.items():
        for q in queries:
            all_queries.append((category, q))
    for q in PORTAL_SEED_QUERIES:
        all_queries.append(("program", q))

    with DDGS() as ddgs:
        for category, query in all_queries:
            try:
                for r in list(ddgs.text(query, max_results=DISCOVERY_MAX_PER_QUERY)):
                    url = r.get("href", "")
                    if not url:
                        continue
                    domain = domain_of(url)
                    if not domain or domain in seen or _is_skipped(domain):
                        continue
                    seen.add(domain)
                    is_new = reg.register_discovery(
                        domain=domain,
                        url=_homepage(domain),
                        category=category,
                        method="web_search",
                        detail=query,
                    )
                    if reg.add_pending(_homepage(domain), domain, category, discovered_via=query):
                        queued += 1
                    if is_new:
                        new_domains += 1
                        print(f"    NEW {domain} ({_tld_bucket(domain)}) via search")
                    else:
                        print(f"    known {domain}")
            except Exception as e:
                print(f"  Search error: {e}")
            time.sleep(DISCOVERY_DELAY_SECONDS)

    return queued, new_domains


def _extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        full = urljoin(base_url, href)
        if full.startswith("http"):
            links.append(full)
    return links


def discover_from_link_crawl(reg, max_portals: int = 25) -> Tuple[int, int]:
    """
    Crawl verified opportunity portals and extract linked external domains.
    Finds sites portals link to — often new job boards and program sites.
    """
    queued = 0
    new_domains = 0
    seen: Set[str] = set()
    portals = reg.list_crawl_seeds(limit=max_portals)

    for row in portals:
        source_domain = row["domain"]
        source_url = row["url"]
        try:
            resp = requests.get(
                source_url,
                headers={"User-Agent": LINK_CRAWL_USER_AGENT},
                timeout=10,
            )
            if resp.status_code >= 400:
                continue
            links = _extract_links(resp.text, source_url)
        except Exception:
            continue

        for link in links:
            domain = domain_of(link)
            if not domain or domain in seen or domain == source_domain:
                continue
            if _is_skipped(domain):
                continue
            # Keep links that look opportunity-related OR mention Rwanda
            link_l = link.lower()
            if not OPPORTUNITY_LINK_WORDS.search(link_l) and not RWANDA_HINT.search(link_l):
                if not RWANDA_HINT.search(domain):
                    continue
            seen.add(domain)
            is_new = reg.register_discovery(
                domain=domain,
                url=_homepage(domain),
                category=None,
                method="link_crawl",
                detail=f"from:{source_domain}",
            )
            if reg.add_pending(_homepage(domain), domain, None, discovered_via=f"link:{source_domain}"):
                queued += 1
            if is_new:
                new_domains += 1
                print(f"    NEW {domain} (link from {source_domain})")

        time.sleep(0.8)

    return queued, new_domains


def discover_from_search_queue(reg) -> Tuple[int, int]:
    """Prioritize youth searches that had sparse registry hits."""
    queued = 0
    new_domains = 0
    rows = []
    try:
        rows = reg.list_search_harvest_queue(limit=15)
    except Exception:
        return 0, 0
    if not rows:
        return 0, 0

    print("\n-- Discovery: queued youth searches (sparse results) --")
    seen: Set[str] = set()
    with DDGS() as ddgs:
        for row in rows:
            query = (row["query"] or "").strip()
            category = (row["category"] or "").strip() or "program"
            if not query:
                reg.mark_search_harvest_processed(row["id"])
                continue
            rw_query = f"{query} Rwanda {category.replace('_', ' ')} apply"
            try:
                for r in list(ddgs.text(rw_query, max_results=DISCOVERY_MAX_PER_QUERY)):
                    url = r.get("href", "")
                    if not url:
                        continue
                    domain = domain_of(url)
                    if not domain or domain in seen or _is_skipped(domain):
                        continue
                    seen.add(domain)
                    is_new = reg.register_discovery(
                        domain=domain,
                        url=_homepage(domain),
                        category=category,
                        method="search_queue",
                        detail=query,
                    )
                    if reg.add_pending(_homepage(domain), domain, category, discovered_via=f"search:{query}"):
                        queued += 1
                    if is_new:
                        new_domains += 1
                        print(f"    NEW {domain} (search queue: {query[:40]})")
            except Exception as exc:
                print(f"  Search queue error ({query[:40]}): {exc}")
            reg.mark_search_harvest_processed(row["id"])
            time.sleep(DISCOVERY_DELAY_SECONDS)
    return queued, new_domains


def run_full_discovery(reg) -> dict:
    """All discovery sources — search queue + web search + link crawl."""
    print("\n-- Discovery: youth search queue (nightly priority) --")
    queue_q, queue_new = discover_from_search_queue(reg)

    print("\n-- Discovery: open web (all TLDs: .com, .org, .rw, …) --")
    web_q, web_new = discover_from_web_search(reg)

    print("\n-- Discovery: link crawl from known portals --")
    link_q, link_new = discover_from_link_crawl(reg)

    total_new = queue_new + web_new + link_new
    reg.set_meta("last_discovery_at", __import__("registry_db", fromlist=["_utc_now"])._utc_now())
    reg.set_meta("last_discovery_new_domains", str(total_new))

    return {
        "search_queue_queued": queue_q,
        "web_search_queued": web_q,
        "link_crawl_queued": link_q,
        "new_domains_found": total_new,
        "total_pending": reg.stats().get("pending_urls", 0),
    }
