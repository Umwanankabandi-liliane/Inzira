"""Rwanda relevance gate — content signals only, not defaulted location."""

from rwanda_relevance import (
    has_rwanda_content_signals,
    is_rwanda_relevant_content,
    is_rwanda_relevant_listing,
    listing_scope,
)


def test_kenya_listing_rejected_despite_prefilled_location():
    """Kenya event with location='Rwanda' must fail — location is not a relevance signal."""
    item = {
        "title": "FREE VIRTUAL EVENT: Apply to Participate in the Kenya National Youth Climate Statement",
        "snippet": "[listing] Applications are open for young people in Kenya (LCOY Kenya 2026).",
        "location": "Rwanda",
        "apply_url": "https://opportunitytracker.ug/kenya-youth-climate-2026",
        "source_domain": "opportunitytracker.ug",
    }
    assert not is_rwanda_relevant_listing(item)

def test_east_african_inclusive_kept_international_scope():
    item = {
        "title": "Nairobi Fellowship 2026",
        "snippet": "[listing] Open to East African students. Remote participation available.",
        "location": "",
        "apply_url": "https://example.org/fellowship/nairobi-2026",
        "source_domain": "example.org",
    }
    assert is_rwanda_relevant_listing(item)
    assert listing_scope(item) == "international"


def test_kenyan_citizens_only_rejected_tier_c():
    item = {
        "title": "Job opening — Kenya",
        "snippet": "[listing] Kenyan citizens only. Must be based in Nairobi.",
        "location": "",
        "apply_url": "https://example.org/jobs/kenya-only",
        "source_domain": "example.org",
    }
    assert not is_rwanda_relevant_listing(item)
    assert listing_scope(item) == ""


def test_rwanda_in_title_passes():
    assert is_rwanda_relevant_content(
        "Senior Data Analyst at Raising The Village — Kigali, Rwanda",
        "https://example.com/jobs/analyst",
    )


def test_configured_official_domain_passes_without_rwanda_word():
    assert is_rwanda_relevant_content(
        "Human Resources Officer — apply online",
        "https://www.jobinrwanda.com/job/hr-officer",
    )


def test_district_name_in_body_passes():
    assert has_rwanda_content_signals("Vacancy based in Gasabo district")


def test_foreign_scholarship_rejected():
    item = {
        "title": "FZ Julich PhD Position - Analysis of Integrated Power, Gas and Hydrogen",
        "snippet": "[listing] Fully funded PhD in Germany at Forschungszentrum Jülich.",
        "location": "Rwanda",
        "apply_url": "https://scholarshiptab.com/fz-julich-phd",
        "source_domain": "scholarshiptab.com",
    }
    assert not is_rwanda_relevant_listing(item)
