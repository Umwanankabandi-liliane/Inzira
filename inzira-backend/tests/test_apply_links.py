"""Tests for apply URL resolution and live listing re-validation."""

from listing_curation import coalesce_apply_urls, resolve_apply_link
from listing_revalidation import validate_listing_url


def test_resolve_apply_link_prefers_detail_over_homepage():
    item = {
        "apply_url": "https://example.rw/",
        "source_url": "https://example.rw/jobs/software-engineer-intern",
    }
    url, label = resolve_apply_link(item)
    assert url.endswith("software-engineer-intern")
    assert label == "visit_listing"


def test_resolve_apply_link_flags_homepage_only():
    item = {
        "apply_url": "https://portal.rw/",
        "source_url": "https://portal.rw/",
    }
    url, label = resolve_apply_link(item)
    assert url == "https://portal.rw/"
    assert label == "search_on_site"


def test_resolve_apply_link_discards_non_url_ner_text():
    item = {
        "apply_url": "Apply online before September",
        "source_url": "https://jobs.rw/listing/123",
    }
    url, label = resolve_apply_link(item)
    assert url.endswith("/listing/123")
    assert label == "visit_listing"


def test_coalesce_apply_urls_sets_source_to_detail():
    item = {
        "apply_url": "https://jobs.rw/vacancy/42",
        "source_url": "https://jobs.rw/",
    }
    apply_url, source_url = coalesce_apply_urls(item)
    assert apply_url.endswith("/vacancy/42")
    assert source_url.endswith("/vacancy/42")


def test_validate_listing_url_rejects_invalid_scheme():
    result = validate_listing_url("ftp://bad.example/job")
    assert result["ok"] is False
    assert result["reason"] == "invalid_url"
