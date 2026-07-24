"""
Automated website discovery — the model finds domains, not a hand-picked list.

Every search runs web discovery + AI website verification. The registry remembers
what the AI already approved so later searches are faster.
"""

from typing import Dict, List, Optional

from ddgs import DDGS

from discovery_config import DISCOVERY_QUERIES
from rwanda_sources import SKIP_DOMAINS, domain_of
from website_verifier import verify_website_host


def _homepage_url(domain: str) -> str:
    return f"https://{domain}"


def _site_name(domain: str, title: str) -> str:
    if title and domain not in title.lower():
        return title.strip()[:120]
    return domain.replace(".", " ").title()


def build_search_queries(user_query: str, category: Optional[str]) -> List[str]:
    """Build discovery queries from what the user typed — no fixed website list."""
    q = user_query.strip()
    cat = (category or "opportunities").replace("_", " ")
    queries = [
        f"{q} Rwanda {cat} website apply 2025 2026",
        f"Rwanda {cat} portal careers scholarships jobs apply",
        f"{q} Kigali Rwanda opportunities apply",
        f"best Rwanda {cat} websites apply online",
    ]
    if category and category in DISCOVERY_QUERIES:
        queries.extend(DISCOVERY_QUERIES[category][:5])
    # dedupe preserving order
    seen = set()
    out = []
    for item in queries:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def discover_domain_candidates(
    user_query: str,
    category: Optional[str],
    max_domains: int = 18,
) -> List[Dict[str, str]]:
    """Search the open web and return one candidate row per domain."""
    queries = build_search_queries(user_query, category)
    by_domain: Dict[str, Dict[str, str]] = {}

    with DDGS() as ddgs:
        for rw_query in queries:
            if len(by_domain) >= max_domains:
                break
            try:
                for r in list(ddgs.text(rw_query, max_results=10)):
                    url = r.get("href", "")
                    if not url:
                        continue
                    domain = domain_of(url)
                    if not domain or domain in by_domain:
                        continue
                    if any(skip in domain for skip in SKIP_DOMAINS):
                        continue
                    by_domain[domain] = {
                        "domain": domain,
                        "url": _homepage_url(domain),
                        "title": r.get("title", "") or domain,
                        "snippet": r.get("body", "") or "",
                    }
            except Exception as e:
                print(f"  Discovery error ({rw_query[:50]}…): {e}")

    return list(by_domain.values())[:max_domains]


def verify_discovered_websites(
    candidates: List[Dict[str, str]],
    category: Optional[str],
    max_results: int,
) -> List[dict]:
    """Fetch each homepage and let AI decide if it hosts opportunities."""
    import main as m

    verified: List[dict] = []
    for cand in candidates:
        if len(verified) >= max_results:
            break
        domain = cand["domain"]
        url = cand["url"]
        page_text = m.fetch_page_text(url)
        if not page_text:
            page_text = cand.get("snippet", "")
        if not page_text:
            continue

        ai = verify_website_host(page_text, url, category)
        if not ai:
            print(f"  AI rejected: {domain}")
            continue

        cat, trust = ai
        name = _site_name(domain, cand.get("title", ""))
        snippet = page_text[:280] + "..." if len(page_text) > 280 else page_text
        verified.append(m.build_result(
            url=url,
            title=name,
            snippet=snippet,
            category=cat,
            trust_score=trust,
            page_text=page_text,
            organization=name,
        ))
        print(f"  AI verified website: {name} ({domain}, trust={trust:.0f})")

    return verified


def discover_and_verify_websites(
    user_query: str,
    category: Optional[str],
    max_results: int = 15,
    skip_domains: Optional[set] = None,
) -> List[dict]:
    """Full pipeline: web search → homepage fetch → AI website judge."""
    skip = skip_domains or set()
    candidates = discover_domain_candidates(user_query, category, max_domains=max_results * 2)
    candidates = [c for c in candidates if c["domain"] not in skip]
    print(f"  Live discovery: {len(candidates)} candidate domains from web search")
    return verify_discovered_websites(candidates, category, max_results)
