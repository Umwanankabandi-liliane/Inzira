"""
Background registry pipeline for production (MIFOTRA operations).

Run on a schedule — NOT during user search:
  python build_registry.py refresh

Discover → AI verify → save to registry.db → app reads registry instantly.
"""

from typing import Callable, Optional


def run_discover(reg) -> int:
    """Find candidate domains from all sources. Returns total queued."""
    from discovery_engine import run_full_discovery
    summary = run_full_discovery(reg)
    print(f"\nDiscovery summary: {summary}")
    return summary.get("web_search_queued", 0) + summary.get("link_crawl_queued", 0)


def run_verify(reg, log: Optional[Callable[[str], None]] = None) -> int:
    """AI-verify all sites and pending URLs. Returns verified count."""
    import json
    import main as m
    from website_verifier import verify_website_host

    out = log or print
    verified_count = 0

    def verify_and_save(domain: str, name: str, url: str,
                        categories_hint: list, source: str) -> None:
        nonlocal verified_count
        page_text = m.fetch_page_text(url)
        if not page_text:
            out(f"  X {domain} - could not fetch")
            reg.upsert_website(
                domain=domain, name=name, url=url,
                categories=categories_hint or ["program"],
                verified=False, has_open=False, source=source,
            )
            return

        cat_hint = categories_hint[0] if categories_hint else None
        ai = verify_website_host(page_text, url, cat_hint)
        if not ai:
            out(f"  X {domain} - AI rejected")
            reg.upsert_website(
                domain=domain, name=name, url=url,
                categories=categories_hint or ["program"],
                verified=False, has_open=False, source=source,
            )
            return

        cat, trust = ai
        all_cats = list(set(categories_hint + [cat]))
        reg.upsert_website(
            domain=domain, name=name, url=url,
            categories=all_cats,
            trust_score=trust,
            has_open=True,
            verified=True,
            snippet=page_text[:280] + "...",
            organization=name,
            apply_link=url,
            source=source,
        )
        verified_count += 1
        out(f"  OK {name} ({domain}) trust={trust:.0f}")
        try:
            from opportunity_sync import sync_opportunities_for_website
            sync_opportunities_for_website(
                reg,
                {
                    "domain": domain,
                    "name": name,
                    "url": url,
                    "categories": all_cats,
                    "trust_score": trust,
                    "verified": 1,
                    "has_open_applications": 1,
                    "snippet": page_text[:280] + "...",
                    "organization": name,
                    "apply_link": url,
                    "location": "Rwanda",
                },
                log=out,
            )
        except Exception as exc:
            out(f"  ! opportunities {domain}: {exc}")

    for row in reg.list_all_websites():
        cats = json.loads(row["categories"])
        verify_and_save(row["domain"], row["name"], row["url"], cats, row["source"])

    for row in reg.list_pending(limit=500):
        cat = row["suggested_category"] or "program"
        verify_and_save(row["domain"], row["domain"], row["url"], [cat], "discovered")
        reg.remove_pending(row["url"])

    return verified_count


def run_refresh(reg, include_seed: bool = True) -> dict:
    """Full production refresh: optional seed → discover → verify."""
    if include_seed:
        from rwanda_sources import RWANDA_SOURCES
        from registry_db import website_snippet
        for source in RWANDA_SOURCES:
            reg.upsert_website(
                domain=source["domain"],
                name=source["name"],
                url=source["url"],
                categories=source["categories"],
                trust_score=0.0,
                has_open=False,
                verified=False,
                snippet=website_snippet(source["name"], source["categories"]),
                source="seed",
            )

    discovered = run_discover(reg)
    print(f"Discovery queued candidates for AI verification")
    print("Loading AI models for verification...")
    verified = run_verify(reg)
    try:
        from opportunity_sync import sync_all_verified
        sync_all_verified(reg, log=print)
    except Exception as exc:
        print(f"Opportunity extraction skipped: {exc}")
    reg.set_meta("last_refresh_at", __import__("registry_db", fromlist=["_utc_now"])._utc_now())
    reg.set_meta("last_refresh_verified", str(verified))

    stats = reg.stats()
    report = reg.discovery_report(new_days=7)
    return {
        "discovered": discovered,
        "verified_this_run": verified,
        "verified_total": stats["verified_open"],
        "new_domains_last_7_days": report.get("new_domains_detected_last_days", 0),
        "verified_by_tld": report.get("verified_by_tld", {}),
        "last_refresh_at": reg.get_meta("last_refresh_at"),
    }
