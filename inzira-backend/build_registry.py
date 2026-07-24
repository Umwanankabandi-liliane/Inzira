#!/usr/bin/env python3
"""
Inzira Registry Operations — production pipeline for MIFOTRA / deployment.

The mobile app reads the registry instantly. This script builds the registry
in the background (scheduled daily or weekly):

  python build_registry.py refresh   # seed candidates → discover web → AI verify
  python build_registry.py discover  # find new domains only
  python build_registry.py verify    # AI verify queued + existing sites
  python build_registry.py opportunities  # extract listings from verified portals
  python build_registry.py stats     # counts + last refresh time
"""

import argparse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "registry.db")


def get_registry():
    from registry_db import Registry
    reg = Registry(DB_PATH)
    reg.init_db()
    return reg


def cmd_seed(reg) -> None:
    from rwanda_sources import RWANDA_SOURCES
    from registry_db import website_snippet
    print(f"Queueing {len(RWANDA_SOURCES)} bootstrap candidates...")
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
        print(f"  + {source['name']} ({source['domain']})")
    print("Done. Run 'refresh' or 'verify' to AI-approve sites for the app.")


def cmd_discover(reg) -> None:
    from registry_pipeline import run_discover
    print("Discovering candidate websites from the open web...")
    added = run_discover(reg)
    print(f"Discovery complete. {added} new URLs queued for AI verification.")


def cmd_verify(reg) -> None:
    print("Loading AI models (1-2 minutes)...")
    from registry_pipeline import run_verify
    n = run_verify(reg)
    print(f"\nVerification complete. {n} websites AI-approved this run.")


def cmd_refresh(reg) -> None:
    print("=== Inzira registry refresh (production) ===\n")
    from registry_pipeline import run_refresh
    summary = run_refresh(reg)
    print("\n=== Refresh complete ===")
    print(f"  New candidates discovered : {summary['discovered']}")
    print(f"  Verified this run         : {summary['verified_this_run']}")
    print(f"  Total verified in registry: {summary['verified_total']}")
    print(f"  Last refresh              : {summary['last_refresh_at']}")
    print("\nRestart or keep API running — app search reads registry instantly.")


def cmd_opportunities(reg) -> None:
    from opportunity_sync import sync_all_verified
    print("Extracting individual opportunities from verified portals...")
    sync_all_verified(reg)


def cmd_stats(reg) -> None:
    s = reg.stats()
    report = reg.discovery_report(new_days=7)
    print("\n-- Inzira Registry (MIFOTRA) --")
    print(f"  Verified websites (all TLDs)    : {s['verified_open']}")
    print(f"  Opportunity listings            : {s.get('verified_opportunities', 0)}")
    print(f"  New verified (last 7 days)      : {report.get('new_verified_last_days', 0)}")
    print(f"  New domains detected (7 days)     : {report.get('new_domains_detected_last_days', 0)}")
    print(f"  Pending AI verification           : {s['pending_urls']}")
    print(f"  Last refresh                      : {s.get('last_refresh_at') or 'never'}")
    print(f"  Last discovery scan               : {s.get('last_discovery_at') or 'never'}")
    print("\n  Verified by domain type:")
    for tld, n in sorted(report.get("verified_by_tld", {}).items(), key=lambda x: -x[1]):
        print(f"    {tld:10s} {n}")
    print("\n  Verified by category:")
    for cat, n in s["by_category"].items():
        print(f"    {cat:14s} {n}")
    print()


def cmd_report(reg) -> None:
    report = reg.discovery_report(new_days=7)
    print("\n=== MIFOTRA Discovery Report ===")
    print(f"Total verified websites : {report['verified_open']}")
    print(f"New this week (verified): {report['new_verified_last_days']}")
    print(f"New domains detected    : {report['new_domains_detected_last_days']}")
    print("\nBy TLD:")
    for tld, n in sorted(report.get("verified_by_tld", {}).items(), key=lambda x: -x[1]):
        print(f"  {tld:10s} {n}")
    print("\nRecent discovery events:")
    for ev in report.get("recent_discovery_events", [])[:20]:
        tag = "NEW" if ev["is_new_domain"] else "known"
        print(f"  [{tag}] {ev['domain']} via {ev['method']} ({ev['tld']})")
    print()


def main():
    parser = argparse.ArgumentParser(description="Inzira registry operations")
    parser.add_argument(
        "command",
        choices=["seed", "discover", "verify", "refresh", "opportunities", "all", "stats", "report"],
        help="seed | discover | verify | refresh | opportunities | all | stats | report",
    )
    args = parser.parse_args()
    reg = get_registry()

    if args.command == "seed":
        cmd_seed(reg)
    elif args.command == "discover":
        cmd_discover(reg)
    elif args.command == "verify":
        cmd_verify(reg)
    elif args.command == "refresh":
        cmd_refresh(reg)
    elif args.command == "opportunities":
        cmd_opportunities(reg)
    elif args.command == "all":
        cmd_refresh(reg)
        cmd_stats(reg)
    elif args.command == "stats":
        cmd_stats(reg)
    elif args.command == "report":
        cmd_report(reg)


if __name__ == "__main__":
    main()
