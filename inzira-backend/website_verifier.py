"""
AI checks whether a WEBSITE hosts apply-able opportunities (not a single post).

Job boards and aggregators (Opportunity Desk, Job in Rwanda, Igire…) often fail
strict single-page classifiers — this module detects opportunity *portals*.
"""

from typing import Optional, Tuple

PORTAL_SIGNALS = [
    "job", "jobs", "vacancy", "vacancies", "career", "careers", "recruitment",
    "scholarship", "scholarships", "internship", "internships", "fellowship",
    "training", "program", "programme", "opportunity", "opportunities",
    "apply", "application", "hiring", "courses", "bootcamp", "competition",
]

MIN_TRUST_PORTAL = 48
MIN_TRUST_PAGE = 62


def is_opportunity_portal(page_text: str) -> bool:
    """True when the page looks like a portal listing many opportunities."""
    t = page_text.lower()
    hits = sum(1 for s in PORTAL_SIGNALS if s in t)
    has_apply = any(x in t for x in ("apply", "application", "register", "submit"))
    has_listings = any(x in t for x in ("job", "jobs", "vacancy", "scholarship", "internship"))
    return hits >= 4 and has_apply and has_listings


def verify_website_host(
    page_text: str,
    url: str,
    matched_category: Optional[str] = None,
) -> Optional[Tuple[str, float]]:
    """
    Returns (category, trust_score) if AI judges this WEBSITE hosts opportunities.
    Used by live search and build_registry verify — not manual curation.
    """
    import main as m

    if len(page_text) < 60:
        return None
    if not m.is_rwanda_relevant(f"{page_text} {url}", url):
        return None

    portal = is_opportunity_portal(page_text)
    has_open = m.has_open_application_signals(page_text)
    if not portal and not has_open:
        return None

    bert_label, bert_conf = m.classify_binary(page_text)
    if bert_label == 0 and not portal:
        return None
    if bert_label == 0 and portal and bert_conf > 0.92:
        return None

    category, _ = m.classify_category(page_text)
    if category == "not_opportunity":
        if portal:
            category = matched_category or m.infer_category_from_text(page_text, "program")
        else:
            return None

    if matched_category and category != matched_category:
        related = {matched_category, "program", "training"}
        if category not in related and not portal:
            return None

    trust = m.compute_trust_score(page_text, url)
    floor = MIN_TRUST_PORTAL if portal else MIN_TRUST_PAGE
    if trust < floor:
        return None

    return category, trust
