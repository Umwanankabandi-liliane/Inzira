from match_engine import (
    opportunity_matches_education,
    opportunity_matches_skills,
    rank_opportunities,
)


def test_rank_opportunities_respects_profile_interests():
    profile = {
        "district": "Kicukiro",
        "education": "Diploma",
        "skills": ["ICT"],
        "interests": ["job"],
    }
    opportunities = [
        {
            "title": "ICT Job in Kicukiro",
            "category": "job",
            "trust_score": 90,
            "district": "Kicukiro",
            "snippet": "Great fit",
        },
        {
            "title": "Scholarship in Huye",
            "category": "scholarship",
            "trust_score": 95,
            "district": "Huye",
            "snippet": "Not a job",
        },
    ]

    ranked = rank_opportunities(profile, opportunities, limit=10)

    assert len(ranked) == 1
    assert ranked[0]["category"] == "job"
    assert ranked[0]["title"] == "ICT Job in Kicukiro"


def test_rank_opportunities_category_filter_excludes_other_categories():
    profile = {"district": "Gasabo", "interests": ["program"], "skills": []}
    opportunities = [
        {"title": "UR Masters in Animal Production", "category": "program", "trust_score": 90, "snippet": "graduate"},
        {"title": "Tech Internship", "category": "internship", "trust_score": 85, "snippet": "software developer"},
        {"title": "Marketing Internship", "category": "internship", "trust_score": 80, "snippet": "business intern"},
    ]

    ranked = rank_opportunities(profile, opportunities, limit=10, category_filter="internship")

    assert len(ranked) == 2
    assert all(r["category"] == "internship" for r in ranked)


def test_rank_opportunities_strict_skills_with_category():
    profile = {
        "district": "Kigali",
        "interests": ["internship"],
        "skills": ["ICT and software"],
    }
    opportunities = [
        {"title": "Software Developer Intern", "category": "internship", "trust_score": 88, "snippet": "ICT team"},
        {"title": "Animal Production Internship", "category": "internship", "trust_score": 90, "snippet": "farm work"},
        {"title": "UR Masters Energy Economics", "category": "program", "trust_score": 95, "snippet": "graduate program"},
    ]

    ranked = rank_opportunities(
        profile,
        opportunities,
        limit=10,
        category_filter="internship",
        strict_skills=True,
    )

    assert len(ranked) == 1
    assert ranked[0]["title"] == "Software Developer Intern"


def test_opportunity_matches_skills_ict_keywords():
    opp = {"title": "Junior Developer", "category": "job", "snippet": "software engineering role", "organization": ""}
    assert opportunity_matches_skills(opp, ["ICT and software"]) is True
    assert opportunity_matches_skills(opp, ["Agriculture"]) is False
    # "ict" must not match inside the word "district"
    district_opp = {"title": "Nurse at District Hospital", "category": "job", "snippet": "clinical nursing role"}
    assert opportunity_matches_skills(district_opp, ["ICT and software"]) is False


def test_rank_no_fallback_when_interest_category_empty():
    profile = {"interests": ["internship"], "skills": []}
    opportunities = [
        {"title": "UR Masters Program", "category": "program", "trust_score": 95, "snippet": "phd"},
    ]

    ranked = rank_opportunities(profile, opportunities, limit=10)

    assert ranked == []


def test_rank_no_soft_fallback_when_field_of_interest_empty():
    """ICT field must not fall back to agriculture / unrelated opportunities."""
    profile = {
        "district": "Nyanza",
        "education": "Bachelor's degree",
        "skills": ["ICT and software"],
        "interests": ["job"],
    }
    opportunities = [
        {
            "title": "Farm Extension Officer",
            "category": "job",
            "trust_score": 92,
            "district": "Nyanza",
            "snippet": "agriculture and livestock support",
        },
        {
            "title": "Nurse at District Hospital",
            "category": "job",
            "trust_score": 90,
            "district": "Nyanza",
            "snippet": "clinical nursing role",
        },
    ]

    ranked = rank_opportunities(profile, opportunities, limit=10)

    assert ranked == []


def test_rank_field_of_interest_keeps_only_ict():
    profile = {
        "district": "Gasabo",
        "education": "Bachelor's degree",
        "skills": ["ICT and software"],
        "interests": ["job"],
    }
    opportunities = [
        {
            "title": "Junior Software Developer",
            "category": "job",
            "trust_score": 88,
            "district": "Gasabo",
            "snippet": "ICT and programming role for bachelor holders",
        },
        {
            "title": "Agriculture Field Officer",
            "category": "job",
            "trust_score": 95,
            "district": "Gasabo",
            "snippet": "farming extension",
        },
    ]

    ranked = rank_opportunities(profile, opportunities, limit=10)

    assert len(ranked) == 1
    assert ranked[0]["title"] == "Junior Software Developer"


def test_education_excludes_when_requirement_too_high():
    opp = {
        "title": "Research Analyst",
        "category": "job",
        "snippet": "Master's degree required in economics",
        "eligibility": "masters holders only",
    }
    assert opportunity_matches_education(opp, "High school") is False
    assert opportunity_matches_education(opp, "Master's degree") is True
    assert opportunity_matches_education(opp, "Bachelor's degree") is False


def test_education_passes_when_opportunity_silent():
    opp = {"title": "Software Developer", "category": "job", "snippet": "ICT coding role", "eligibility": ""}
    assert opportunity_matches_education(opp, "Diploma") is True
