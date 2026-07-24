"""
Sync extracted opportunities into registry.db for verified websites.
Uses full multi-page harvest (production) — not single-page demo scrape.
"""

from __future__ import annotations

import json
from typing import Callable, Optional

from opportunity_harvester import harvest_website, harvest_all_verified


def sync_opportunities_for_website(reg, website_row, html=None, log=None) -> int:
    """Harvest real listings from one verified portal. Returns count saved."""
    out = log or (lambda _m: None)
    site = dict(website_row)
    if isinstance(site.get("categories"), str):
        try:
            site["categories"] = json.loads(site["categories"])
        except Exception:
            site["categories"] = [site["categories"]]

    if not site.get("verified") or not site.get("has_open_applications"):
        reg.delete_opportunities_for_domain(site.get("domain") or "")
        return 0

    items, summary = harvest_website(site, log=out, reg=reg)
    n = reg.replace_opportunities_for_domain(
        site.get("domain") or "", items, seen_apply_urls=summary.seen_detail_urls,
    )
    out(f"  {site.get('domain')}: {n} listings harvested")
    return n


def sync_all_verified(reg, log: Optional[Callable[[str], None]] = None, limit: int = 500) -> int:
    return harvest_all_verified(reg, log=log, limit=limit)
