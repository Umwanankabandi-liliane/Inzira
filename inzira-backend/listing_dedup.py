"""Backward-compatible re-export — dedupe logic lives in listing_quality.py."""

from listing_quality import (
    DOMAIN_CANONICAL,
    canonical_domain,
    dedupe_key,
    dedupe_listings,
    normalize_title_key,
    root_domain,
)

__all__ = [
    "DOMAIN_CANONICAL",
    "canonical_domain",
    "dedupe_key",
    "dedupe_listings",
    "normalize_title_key",
    "root_domain",
]
