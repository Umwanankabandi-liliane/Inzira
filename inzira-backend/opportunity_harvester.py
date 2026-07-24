"""
Production opportunity harvester — deep per-site crawl + ML gate.

Configured sources (rwanda_sources.py) are crawled every run.
Discovered verified portals rotate in batches (DISCOVERED_BATCH_SIZE per run).
"""

from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

from match_engine import RWANDA_DISTRICTS
from rwanda_sources import (
    CATEGORY_CRAWL_PATHS,
    DEFAULT_LISTING_PATHS,
    DISCOVERED_HARVEST_BUDGETS,
    harvest_config_for,
    is_configured_source,
    listing_urls_for,
    source_config_for_domain,
)
from site_crawler import CrawlSummary, crawl_one_source

__all__ = [
    "CATEGORY_CRAWL_PATHS",
    "DEFAULT_PATHS",
    "crawl_urls_for_site",
    "harvest_website",
    "harvest_all_verified",
    "harvest_verified_for_category",
    "plan_harvest_run",
    "INCLUDE_DISCOVERED_IN_HARVEST",
    "HARVEST_ALL_DISCOVERED",
    "format_coverage_table",
    "print_coverage_table",
]

DEFAULT_PATHS = DEFAULT_LISTING_PATHS

INCLUDE_DISCOVERED_IN_HARVEST = os.getenv("INCLUDE_DISCOVERED_IN_HARVEST", "1").strip().lower() in (
    "1", "true", "yes",
)
HARVEST_ALL_DISCOVERED = os.getenv("INZIRA_HARVEST_ALL_DISCOVERED", "0").strip().lower() in (
    "1", "true", "yes",
)
DISCOVERED_BATCH_SIZE = int(os.getenv("DISCOVERED_BATCH_SIZE", "25"))
_DOMAIN_WORKERS = int(os.getenv("INZIRA_HARVEST_DOMAIN_WORKERS", "5"))
_ZERO_STREAK_DEPRIORITIZE = 3
_registry_write_lock = threading.Lock()


def crawl_urls_for_site(site: Dict[str, Any], max_urls: int = 10) -> List[str]:
    urls = listing_urls_for(site)
    return urls[:max_urls] if max_urls else urls


def _site_row_to_config(row: Dict[str, Any]) -> Dict[str, Any]:
    site = dict(row)
    if isinstance(site.get("categories"), str):
        try:
            site["categories"] = json.loads(site["categories"])
        except Exception:
            site["categories"] = [site["categories"]]
    domain = (site.get("domain") or "").replace("www.", "")
    seed = source_config_for_domain(domain)
    if seed:
        for key in ("listing_urls", "paths", "harvest", "seed_strict"):
            if key in seed and key not in site:
                site[key] = seed[key]
    if not site.get("url") and site.get("apply_link"):
        site["url"] = site["apply_link"]
    return site


def _meta_json(reg, key: str, default: Any) -> Any:
    raw = reg.get_meta(key, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _last_harvested_at(reg, domain: str) -> str:
    return reg.get_meta(f"last_harvested_at:{domain}", "")


def _is_deprioritized(reg, domain: str) -> bool:
    return reg.get_meta(f"harvest_deprioritized:{domain}", "") == "1"


def _zero_streak(reg, domain: str) -> int:
    try:
        return int(reg.get_meta(f"harvest_zero_streak:{domain}", "0") or "0")
    except ValueError:
        return 0


def _budgets_for_site(reg, domain: str) -> Dict[str, int]:
    discovered = not is_configured_source(domain)
    cfg = harvest_config_for(domain, discovered=discovered)
    if discovered and _is_deprioritized(reg, domain):
        cfg = {k: max(1, int(v) // 2) for k, v in cfg.items()}
    return cfg


def plan_harvest_run(
    reg,
    *,
    limit: int = 500,
    all_discovered: Optional[bool] = None,
) -> Tuple[List[Any], List[Any], List[str]]:
    """
    Return (configured_rows, discovered_rows_for_run, discovered_domain_names).
    When all_discovered=True, every verified discovered domain is included.
  """
    if all_discovered is None:
        all_discovered = HARVEST_ALL_DISCOVERED

    rows = reg.list_verified_rows(limit=limit)
    configured: List[Any] = []
    discovered: List[Any] = []

    for row in rows:
        site = dict(row)
        domain = (site.get("domain") or "").replace("www.", "")
        if not site.get("verified") or not site.get("has_open_applications"):
            continue
        if is_configured_source(domain):
            configured.append(row)
        elif INCLUDE_DISCOVERED_IN_HARVEST:
            discovered.append(row)

    def sort_key(row: Any) -> tuple:
        domain = dict(row).get("domain", "")
        dep = 1 if _is_deprioritized(reg, domain) else 0
        last = _last_harvested_at(reg, domain) or "1970-01-01"
        return (dep, last, domain)

    discovered.sort(key=sort_key)
    if all_discovered:
        batch = discovered
    else:
        batch = discovered[:DISCOVERED_BATCH_SIZE]
    batch_names = [dict(r).get("domain", "") for r in batch]
    return configured, batch, batch_names


def _load_existing_hashes(reg, domain: str) -> Dict[str, str]:
    return _meta_json(reg, f"harvest_hashes:{domain}", {})


def _load_existing_listing_urls(reg, domain: str) -> set:
    from site_crawler import normalize_url
    urls = reg.list_apply_urls_for_domain(domain)
    return {normalize_url(u) for u in urls if u}


def _save_harvest_meta(
    reg,
    domain: str,
    summary: CrawlSummary,
    hashes: Dict[str, str],
    *,
    stored_count: int,
) -> None:
    from registry_db import _utc_now

    with _registry_write_lock:
        reg.set_meta(f"harvest_hashes:{domain}", json.dumps(hashes))
        reg.set_meta(f"harvest_last_summary:{domain}", json.dumps(summary.as_dict()))
        reg.set_meta(f"last_harvested_at:{domain}", _utc_now())

        streak = _zero_streak(reg, domain)
        if stored_count <= 0:
            streak += 1
        else:
            streak = 0
        reg.set_meta(f"harvest_zero_streak:{domain}", str(streak))
        if streak >= _ZERO_STREAK_DEPRIORITIZE:
            reg.set_meta(f"harvest_deprioritized:{domain}", "1")
        elif stored_count > 0:
            reg.set_meta(f"harvest_deprioritized:{domain}", "0")


def _parse_categories(site: Dict[str, Any]) -> List[str]:
    cats = site.get("categories") or []
    if isinstance(cats, str):
        try:
            cats = json.loads(cats)
        except Exception:
            cats = [cats]
    return [str(c).lower() for c in cats if c]


def _site_matches_category(site: Dict[str, Any], category: str) -> bool:
    cat = (category or "").strip().lower()
    if not cat:
        return True
    if cat in _parse_categories(site):
        return True
    domain = (site.get("domain") or "").replace("www.", "")
    src = source_config_for_domain(domain)
    if src and cat in [str(c).lower() for c in (src.get("categories") or [])]:
        return True
    return False


def harvest_website(
    site: Dict[str, Any],
    districts: Optional[List[str]] = None,
    *,
    max_pages: Optional[int] = None,
    max_per_page: int = 15,
    pause_s: float = 0.35,
    log: Optional[Callable[[str], None]] = None,
    reg=None,
    budgets: Optional[Dict[str, int]] = None,
    category_focus: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], CrawlSummary]:
    _ = districts or RWANDA_DISTRICTS
    out = log or (lambda _m: None)
    site_cfg = _site_row_to_config(site)
    domain = (site_cfg.get("domain") or "").replace("www.", "")

    if budgets is None:
        budgets = _budgets_for_site(reg, domain) if reg else harvest_config_for(
            domain, discovered=not is_configured_source(domain),
        )
    if max_pages is not None:
        budgets = {**budgets, "max_pages": int(max_pages)}

    existing_hashes = _load_existing_hashes(reg, domain) if reg else {}
    existing_listing_urls = _load_existing_listing_urls(reg, domain) if reg else set()

    items, summary, new_hashes = crawl_one_source(
        site_cfg,
        budgets=budgets,
        existing_hashes=existing_hashes,
        existing_listing_urls=existing_listing_urls,
        log=out,
        category_focus=category_focus,
    )

    if reg and domain:
        merged_hashes = {**existing_hashes, **new_hashes}
        _save_harvest_meta(reg, domain, summary, merged_hashes, stored_count=summary.stored)

    return items, summary


def harvest_verified_for_category(
    reg,
    category: str,
    *,
    log: Optional[Callable[[str], None]] = None,
    progress: Optional[Callable[[str, int, str], None]] = None,
    limit: int = 500,
) -> int:
    """
    Deep-crawl every verified portal that hosts this category (scholarship, job, …).
    Used when youth search by category so results come from official listing pages.
    """
    cat = (category or "").strip().lower()
    if not cat:
        return 0
    out = log or (lambda _m: None)
    rows = reg.list_verified_rows(limit=limit)
    matching = [row for row in rows if _site_matches_category(dict(row), cat)]
    total_sites = len(matching)
    if not total_sites:
        return 0

    out(f"Category harvest ({cat}) — {total_sites} verified portals")
    total_stored = 0
    for idx, row in enumerate(matching, 1):
        domain = dict(row).get("domain", "")
        kind = "configured" if is_configured_source(domain) else "discovered"
        if progress:
            pct = 12 + int(58 * idx / max(total_sites, 1))
            progress("deep_harvest", pct, f"[{idx}/{total_sites}] Scraping {domain}…")
        n, _ = _harvest_one_site(
            reg, row, out,
            source_kind=kind,
            quiet=True,
            category_focus=cat,
        )
        total_stored += n
        out(f"[{idx}/{total_sites}] {domain} — present {n}")
    return total_stored


def _harvest_one_site(
    reg,
    row,
    log: Callable[[str], None],
    *,
    source_kind: str = "configured",
    quiet: bool = False,
    category_focus: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    site = _site_row_to_config(dict(row))
    domain = site.get("domain") or ""
    if not site.get("verified") or not site.get("has_open_applications"):
        with _registry_write_lock:
            reg.delete_opportunities_for_domain(domain)
        return 0, {"domain": domain, "source_kind": source_kind, "skipped": "not verified/open"}

    try:
        items, summary = harvest_website(
            site, log=log if not quiet else (lambda _m: None), reg=reg,
            category_focus=category_focus,
        )
        with _registry_write_lock:
            n = reg.replace_opportunities_for_domain(
                domain, items, seen_apply_urls=summary.seen_detail_urls,
            )
            if reg and domain:
                from registry_db import _utc_now
                reg.set_meta(f"harvest_last_summary:{domain}", json.dumps({
                    **summary.as_dict(),
                    "new_this_run": summary.stored,
                    "present_after_run": n,
                }))
        if not quiet:
            log(f"  [{source_kind}] {domain}: {n} listings stored")
        row_data = summary.as_dict()
        row_data["source_kind"] = source_kind
        row_data["new_this_run"] = summary.stored
        row_data["present_after_run"] = n
        return n, row_data
    except Exception as exc:
        if not quiet:
            log(f"  ! [{source_kind}] {domain}: {exc}")
        return 0, {
            "domain": domain,
            "source_kind": source_kind,
            "errors": 1,
            "messages": [str(exc)],
        }


def format_coverage_table(rows: List[Dict[str, Any]]) -> str:
    """Format funnel coverage table, sorted by present_after_run descending."""
    lines = [
        f"{'domain':<28} {'pages':>5} {'detail':>6} {'new':>5} "
        f"{'present':>7} {'skip-unc':>8} {'top-reject':<14} {'js':>3}",
        "-" * 88,
    ]
    for r in sorted(
        rows,
        key=lambda x: (-int(x.get("present_after_run", x.get("stored", 0)) or 0), x.get("domain", "")),
    ):
        top = r.get("top_rejection") or ""
        if not top and r.get("rejection_counts"):
            top = max(r["rejection_counts"], key=r["rejection_counts"].get)
        present = r.get("present_after_run", r.get("stored", 0))
        new_run = r.get("new_this_run", r.get("passed_ml", 0))
        lines.append(
            f"{r.get('domain',''):<28} "
            f"{r.get('pages_fetched',0):>5} "
            f"{r.get('detail_pages_found',0):>6} "
            f"{new_run:>5} "
            f"{present:>7} "
            f"{r.get('skipped_unchanged', r.get('skipped_duplicate', 0)):>8} "
            f"{top:<14} "
            f"{'Y' if r.get('js_rendered_suspect') else 'N':>3}"
        )
    lines.append(f"\nTotal sites crawled: {len(rows)}")
    lines.append(
        f"Total new this run: {sum(int(r.get('new_this_run', r.get('passed_ml', 0)) or 0) for r in rows)}"
    )
    lines.append(
        f"Total present after run: {sum(int(r.get('present_after_run', r.get('stored', 0)) or 0) for r in rows)}"
    )
    return "\n".join(lines)


def format_category_totals(label: str, opp_by_cat: Dict[str, int]) -> str:
    lines = [f"\n{label} — opportunities by category:"]
    total = 0
    for cat, n in sorted(opp_by_cat.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {cat:<16} {n:>5}")
        total += int(n)
    lines.append(f"  {'TOTAL':<16} {total:>5}")
    return "\n".join(lines)


def _append_progress_line(outfile: str, line: str) -> None:
    with open(outfile, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def print_coverage_table(rows: List[Dict[str, Any]], *, outfile: Optional[str] = None) -> None:
    text = format_coverage_table(rows)
    print("\nCoverage table (sorted by present_after_run):")
    print(text)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")


def harvest_all_verified(
    reg,
    log=None,
    limit: int = 500,
    *,
    pause_between_sites: float = 0.5,
    all_discovered: Optional[bool] = None,
    coverage_outfile: Optional[str] = None,
    stats_before: Optional[Dict[str, Any]] = None,
) -> int:
    """Crawl configured sources + discovered portals (batch or all)."""
    from ml_runtime import ensure_models_loaded
    from registry_db import _utc_now

    ensure_models_loaded()

    if all_discovered is None:
        all_discovered = HARVEST_ALL_DISCOVERED

    out = log or (lambda m: print(m, flush=True))
    configured, discovered_batch, batch_names = plan_harvest_run(
        reg, limit=limit, all_discovered=all_discovered,
    )
    run_rows: List[Tuple[Any, str]] = [(r, "configured") for r in configured]
    for row in discovered_batch:
        kind = "discovered-deprioritized" if _is_deprioritized(reg, dict(row).get("domain", "")) else "discovered"
        run_rows.append((row, kind))

    mode_label = "all discovered" if all_discovered else f"batch {DISCOVERED_BATCH_SIZE}"
    workers = max(1, _DOMAIN_WORKERS)
    out(
        f"Deep harvest — {len(configured)} configured + {len(discovered_batch)} discovered ({mode_label}), "
        f"include_discovered={INCLUDE_DISCOVERED_IN_HARVEST}, workers={workers}"
    )
    if batch_names and not all_discovered:
        out(f"  Discovered batch: {', '.join(batch_names[:12])}" + (
            f" … +{len(batch_names) - 12} more" if len(batch_names) > 12 else ""
        ))
    elif all_discovered and batch_names:
        out(f"  All {len(batch_names)} discovered domains queued")

    total_sites = len(run_rows)
    if coverage_outfile:
        with open(coverage_outfile, "w", encoding="utf-8") as fh:
            fh.write(f"Harvest progress — {total_sites} sites, workers={workers}\n")
            fh.flush()

    total = 0
    coverage: List[Dict[str, Any]] = []
    progress_lock = threading.Lock()
    completed = 0

    def _run_one(row: Any, kind: str) -> Tuple[int, Dict[str, Any]]:
        return _harvest_one_site(reg, row, out, source_kind=kind, quiet=True)

    if workers <= 1:
        for idx, (row, kind) in enumerate(run_rows, 1):
            domain = dict(row).get("domain", "")
            n, cov = _harvest_one_site(reg, row, out, source_kind=kind, quiet=True)
            total += n
            coverage.append(cov)
            line = f"[{idx}/{total_sites}] {domain} — present {n}"
            out(line)
            if coverage_outfile:
                _append_progress_line(coverage_outfile, line)
            if pause_between_sites > 0 and idx < total_sites:
                time.sleep(pause_between_sites)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_run_one, row, kind): dict(row).get("domain", "")
                for row, kind in run_rows
            }
            for fut in as_completed(futures):
                domain = futures[fut]
                try:
                    n, cov = fut.result()
                except Exception as exc:
                    n, cov = 0, {
                        "domain": domain,
                        "errors": 1,
                        "messages": [str(exc)],
                    }
                with progress_lock:
                    total += n
                    coverage.append(cov)
                    completed += 1
                    line = f"[{completed}/{total_sites}] {domain} — present {n}"
                    out(line)
                    if coverage_outfile:
                        _append_progress_line(coverage_outfile, line)

    now = _utc_now()
    harvest_mode = "deep_crawl+all_discovered" if all_discovered else "deep_crawl+rotation"
    reg.set_meta("last_opportunity_sync_at", now)
    reg.set_meta("last_opportunity_sync_count", str(total))
    reg.set_meta("last_opportunity_harvest_mode", harvest_mode)
    reg.set_meta("harvest_last_run_at", now)
    reg.set_meta("harvest_last_run_all_discovered", "1" if all_discovered else "0")
    reg.set_meta("harvest_last_run_configured", json.dumps([dict(r).get("domain") for r in configured]))
    reg.set_meta("harvest_last_run_discovered_batch", json.dumps(batch_names))
    reg.set_meta("harvest_last_run_coverage", json.dumps(coverage))
    if stats_before:
        reg.set_meta("harvest_stats_before", json.dumps(stats_before))
        reg.set_meta("harvest_stats_after", json.dumps(reg.stats()))
    deprioritized = [
        dict(r).get("domain")
        for r in reg.list_verified_rows(limit=limit)
        if _is_deprioritized(reg, dict(r).get("domain", ""))
    ]
    reg.set_meta("harvest_deprioritized_domains", json.dumps(deprioritized))
    out(f"Harvest complete — {total} listings stored ({len(coverage)} sites crawled).")
    table_text = format_coverage_table(coverage)
    print_coverage_table(coverage, outfile=None)
    if coverage_outfile:
        with open(coverage_outfile, "a", encoding="utf-8") as fh:
            fh.write("\n\n" + table_text + "\n")
            if stats_before:
                after = reg.stats()
                fh.write(format_category_totals("BEFORE", stats_before.get("opportunities_by_category", {})))
                fh.write("\n")
                fh.write(format_category_totals("AFTER", after.get("opportunities_by_category", {})))
                fh.write("\n")
            fh.flush()
    return total


def harvest_coverage_report(reg) -> List[Dict[str, Any]]:
    """Return last run coverage rows for MIFOTRA / CLI."""
    return _meta_json(reg, "harvest_last_run_coverage", [])
