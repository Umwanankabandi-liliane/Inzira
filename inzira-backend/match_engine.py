"""
Youth profile ↔ opportunity matching for Inzira dashboard.
Rule-based scoring (district, interests, skills, category, trust).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

RWANDA_DISTRICTS = [
    "Gasabo", "Kicukiro", "Nyarugenge", "Bugesera", "Gatsibo", "Kayonza", "Kirehe",
    "Ngoma", "Nyagatare", "Rwamagana", "Huye", "Gisagara", "Nyamagabe", "Nyanza",
    "Nyaruguru", "Ruhango", "Kamonyi", "Muhanga", "Karongi", "Ngororero", "Nyabihu",
    "Rubavu", "Rusizi", "Rutsiro", "Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo",
]

KIGALI = {"Gasabo", "Kicukiro", "Nyarugenge"}

COMPETITION = {
    "scholarship": "high",
    "job": "high",
    "internship": "medium",
    "training": "low",
    "program": "medium",
    "free_course": "low",
    "competition": "medium",
}

# Keywords for profile skill fields (must stay aligned with MATCH_SKILL_FIELDS in app.js).
SKILL_FIELD_KEYWORDS = {
    "ict and software": [
        "ict", "software", "computer", "programming", "developer", "digital", "technology",
        "information technology", "coding", "data science", "cyber", "tech", "it",
        "informatics", "web", "app development",
    ],
    "business": ["business", "management", "entrepreneur", "commerce", "marketing", "administration"],
    "health": ["health", "medical", "nursing", "clinical", "hospital", "medicine", "pharmacy"],
    "agriculture": ["agriculture", "agri", "farming", "livestock", "crop", "horticulture", "animal production"],
    "education": ["education", "teaching", "teacher", "pedagogy", "school", "curriculum"],
    "engineering": ["engineering", "engineer", "mechanical", "electrical", "civil", "chemical engineering"],
    "finance": ["finance", "accounting", "banking", "economics", "audit", "financial"],
    "law": ["law", "legal", "justice", "advocate", "juris"],
    "tourism and hospitality": ["tourism", "hospitality", "hotel", "travel", "culinary"],
    "creative arts and media": ["creative", "arts", "media", "design", "film", "music", "journalism"],
}


def _opp_text(opp: dict) -> str:
    return " ".join([
        opp.get("title") or "",
        opp.get("snippet") or "",
        opp.get("eligibility") or "",
        opp.get("organization") or "",
    ]).lower()


def _keyword_in_text(kw: str, text: str) -> bool:
    """Match keyword/phrase on word boundaries so 'ict' does not hit 'district'."""
    token = str(kw or "").strip().lower()
    if not token or not text:
        return False
    pattern = r"(?<!\w)" + re.escape(token).replace(r"\ ", r"\s+") + r"(?!\w)"
    return re.search(pattern, text) is not None


def _skill_keywords(skill: str) -> List[str]:
    s = str(skill or "").strip().lower()
    if not s:
        return []
    if s in SKILL_FIELD_KEYWORDS:
        return [kw.strip() for kw in SKILL_FIELD_KEYWORDS[s] if kw and str(kw).strip()]
    return [s]


def opportunity_matches_skills(opp: dict, skills: List[str]) -> bool:
    if not skills:
        return True
    text = _opp_text(opp)
    for skill in skills:
        for kw in _skill_keywords(skill):
            if _keyword_in_text(kw, text):
                return True
    return False


# Education levels used by My Matches profile form (must stay aligned with app.js).
EDUCATION_RANK = {
    "high school": 1,
    "diploma": 2,
    "bachelor's degree": 3,
    "master's degree": 4,
}

EDUCATION_KEYWORDS = {
    "high school": [
        "high school", "secondary", "a-level", "a level", "o-level", "o level",
        "senior 6", "s6", "ordinary level", "advanced level",
    ],
    "diploma": ["diploma", "tvet", "certificate", "polytechnic", "advanced diploma"],
    "bachelor's degree": [
        "bachelor", "bachelors", "undergraduate", "bsc", "ba ", "university degree",
        "degree holder", "first degree",
    ],
    "master's degree": [
        "master", "masters", "postgraduate", "mba", "msc", "ma ", "graduate degree",
        "post-graduate", "post graduate",
    ],
}


def _norm_education(education: str) -> str:
    return str(education or "").strip().lower().replace("_", " ")


def opportunity_matches_education(opp: dict, education: str) -> bool:
    """
    Enforce education when the opportunity states a level.
    - No education on profile → pass
    - Opportunity mentions no education level → pass (cannot enforce missing data)
    - Opportunity mentions a level → user must meet or exceed it
    """
    edu = _norm_education(education)
    if not edu:
        return True
    user_rank = EDUCATION_RANK.get(edu)
    if not user_rank:
        tokens = [tok for tok in edu.split() if len(tok) > 3]
        if not tokens:
            return True
        text = _opp_text(opp)
        return any(tok in text for tok in tokens)

    text = _opp_text(opp)
    mentioned = []
    for level, kws in EDUCATION_KEYWORDS.items():
        if any(kw in text for kw in kws):
            mentioned.append(EDUCATION_RANK[level])
    if not mentioned:
        return True
    required = max(mentioned)
    return user_rank >= required


def _norm_list(val) -> List[str]:
    if not val:
        return []
    if isinstance(val, list):
        items = val
    else:
        raw = str(val).strip()
        # Support JSON array strings: '["job","training"]'
        if raw.startswith("[") and raw.endswith("]"):
            try:
                import json
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    items = parsed
                else:
                    items = re.split(r"[,;|]+", raw)
            except Exception:
                items = re.split(r"[,;|]+", raw)
        else:
            items = re.split(r"[,;|]+", raw)
    return [x.strip().lower() for x in items if x and str(x).strip()]


INTEREST_ALIASES = {
    "jobs": "job",
    "job": "job",
    "scholarships": "scholarship",
    "scholarship": "scholarship",
    "internships": "internship",
    "internship": "internship",
    "trainings": "training",
    "training": "training",
    "programs": "program",
    "program": "program",
    "programmes": "program",
    "free_courses": "free_course",
    "free_course": "free_course",
    "competitions": "competition",
    "competition": "competition",
}


def _norm_interests(val) -> List[str]:
    out = []
    for item in _norm_list(val):
        out.append(INTEREST_ALIASES.get(item, item))
    return out


def opportunity_categories(opp: dict) -> List[str]:
    cats: List[str] = []
    for c in opp.get("categories") or []:
        if c:
            cats.append(str(c).lower())
    if opp.get("category"):
        cats.append(str(opp["category"]).lower())
    return list(dict.fromkeys(cats))


def opportunity_matches_interests(opp: dict, interests: List[str]) -> bool:
    if not interests:
        return True
    cats = opportunity_categories(opp)
    return any(c in interests for c in cats)


def profile_completeness(profile: Dict[str, Any]) -> int:
    keys = ("name", "district", "age", "education", "skills", "interests")
    filled = 0
    for k in keys:
        v = profile.get(k)
        if isinstance(v, list):
            if v:
                filled += 1
        elif v:
            filled += 1
    return int(round(filled / len(keys) * 100))


def _district_for_site(domain: str, districts: List[str]) -> str:
    """Deprecated — never assign a fake district. Use detect_district() on listing text only."""
    return ""


def _scope_label(opp: dict) -> str:
    d = (opp.get("district") or "").strip()
    if d:
        return "district"
    return "national"


def format_location(opp: dict) -> str:
    d = (opp.get("district") or "").strip()
    loc = (opp.get("location") or "").strip()
    if d:
        return f"{d}, Rwanda"
    if loc and "national" in loc.lower():
        return loc
    return "Rwanda (national)"


def _district_for_opportunity(opp: dict, districts: List[str]) -> str:
    d = (opp.get("district") or "").strip()
    if d and d in districts:
        return d
    loc = (opp.get("location") or "").lower()
    for name in districts:
        if name.lower() in loc:
            return name
    return ""


def district_radar(sites: List[dict], districts: List[str]) -> List[Dict[str, Any]]:
    counts: Dict[str, Dict[str, int]] = {d: {"total": 0, "job": 0, "scholarship": 0, "internship": 0, "training": 0, "program": 0} for d in districts}
    national = {"total": 0, "job": 0, "scholarship": 0, "internship": 0, "training": 0, "program": 0}
    for s in sites:
        d = _district_for_opportunity(s, districts)
        cat = (s.get("category") or "program").lower()
        bucket = counts.get(d) if d else national
        if bucket is None:
            continue
        bucket["total"] += 1
        if cat in bucket:
            bucket[cat] += 1
        else:
            bucket["program"] += 1

    max_total = max((c["total"] for c in counts.values()), default=1) or 1
    out = []
    for name in districts:
        c = counts.get(name, {"total": 0})
        total = c.get("total", 0)
        density = total / max_total
        if density >= 0.7:
            level = "very_high"
        elif density >= 0.45:
            level = "high"
        elif density >= 0.25:
            level = "medium"
        elif total > 0:
            level = "low"
        else:
            level = "very_low"
        out.append({
            "district": name,
            "total": total,
            "density": round(density, 2),
            "level": level,
            "breakdown": {k: c.get(k, 0) for k in ("job", "scholarship", "internship", "training", "program")},
        })
    return sorted(out, key=lambda x: -x["total"])


def compute_match(profile: Dict[str, Any], opp: dict) -> Dict[str, Any]:
    score = 12.0
    reasons: List[str] = []
    missing: List[str] = []

    district = (profile.get("district") or "").strip()
    interests = _norm_interests(profile.get("interests"))
    skills = _norm_list(profile.get("skills"))
    education = (profile.get("education") or "").strip().lower()

    cat = (opp.get("category") or "program").lower()
    text = " ".join([
        opp.get("title") or "",
        opp.get("snippet") or "",
        opp.get("eligibility") or "",
        opp.get("organization") or "",
    ]).lower()

    trust = opp.get("trust_score") or 0
    if isinstance(trust, (int, float)):
        t = trust / 100.0 if trust > 1 else trust
        score += t * 18

    opp_district = (opp.get("district") or "").strip()
    if district and opp_district and district.lower() == opp_district.lower():
        score += 18
        reasons.append(f"Opportunity in {district}")
    elif district and district.lower() in (opp.get("location") or "").lower():
        score += 12
        reasons.append(f"Relevant to {district}")

    if interests:
        for interest in interests:
            if interest in text or interest in cat:
                score += 12
                reasons.append(f"Matches your interest in {interest}")
                break
    else:
        missing.append("Add interests to improve matching")

    if skills:
        hit = [s for s in skills if opportunity_matches_skills(opp, [s])]
        if hit:
            score += min(20, 6 * len(hit))
            reasons.append(f"Skills match: {', '.join(hit[:3])}")
        else:
            missing.append("Build skills listed on opportunity pages")
    else:
        missing.append("Add skills (e.g. Python, design)")

    if district and district.lower() in text:
        score += 10
        reasons.append(f"Mentions {district}")
    elif district in KIGALI and any(k in text for k in ("kigali", "national", "rwanda")):
        score += 10
        reasons.append("National / Kigali-friendly opportunity")

    if education:
        edu_tokens = education.replace("_", " ").split()
        if any(tok in text for tok in edu_tokens if len(tok) > 3):
            score += 8
            reasons.append("Fits your education level")

    if cat in interests:
        score += 10
        reasons.append(f"Category: {cat}")

    if not reasons:
        reasons.append("Listed on a verified Rwanda opportunity portal")
        score -= 10

    competition = COMPETITION.get(cat, "medium")
    final = int(min(95, max(10, round(score))))

    return {
        "score": final,
        "reasons": reasons[:3],
        "missing": missing[:2],
        "competition": competition,
    }


MIN_MATCH_SCORE = 48
MIN_MATCH_SCORE_CATEGORY = 10


def rank_opportunities(
    profile: Dict[str, Any],
    opportunities: List[dict],
    limit: int = 25,
    *,
    category_filter: Optional[str] = None,
    strict_skills: bool = False,
) -> List[dict]:
    pool = list(opportunities)
    cf = (category_filter or "").strip().lower()
    if cf:
        cf = INTEREST_ALIASES.get(cf, cf)
        pool = [o for o in pool if cf in opportunity_categories(o)]
    else:
        interests = _norm_interests(profile.get("interests"))
        if interests:
            pool = [o for o in pool if opportunity_matches_interests(o, interests)]

    # Field of interest is stored as profile.skills (e.g. "ICT and software").
    # Always hard-filter — never fall back to unrelated opportunities just to fill the list.
    skills = _norm_list(profile.get("skills"))
    if skills:
        skill_pool = [o for o in pool if opportunity_matches_skills(o, skills)]
        if not skill_pool:
            return []
        pool = skill_pool

    education = (profile.get("education") or "").strip()
    if education:
        edu_pool = [o for o in pool if opportunity_matches_education(o, education)]
        if not edu_pool:
            return []
        pool = edu_pool

    ranked = []
    min_score = MIN_MATCH_SCORE_CATEGORY if cf else MIN_MATCH_SCORE
    for opp in pool:
        m = compute_match(profile, opp)
        if m["score"] < min_score:
            continue
        ranked.append({**opp, "match_score": m["score"], "match_reasons": m["reasons"], "match_missing": m["missing"], "competition": m["competition"]})
    ranked.sort(key=lambda x: (-x["match_score"], -(x.get("trust_score") or 0)))
    return ranked[:limit]


def ai_insights(matches: List[dict], radar: List[dict]) -> List[str]:
    insights = []
    if matches:
        top = matches[0]
        insights.append(
            f"Top match: {top.get('title', top.get('domain', 'Opportunity'))} — {top.get('match_score', 0)}% fit for your profile."
        )
    by_cat: Dict[str, int] = {}
    for m in matches[:15]:
        c = (m.get("category") or "program").lower()
        by_cat[c] = by_cat.get(c, 0) + 1
    if by_cat:
        top_cat = max(by_cat, key=by_cat.get)
        insights.append(f"Most matches in your feed are {top_cat.replace('_', ' ')} opportunities this week.")
    hot = [d for d in radar if d.get("level") in ("very_high", "high")][:3]
    if hot:
        names = ", ".join(d["district"] for d in hot)
        insights.append(f"Highest opportunity density: {names}.")
    if len(insights) < 2:
        insights.append("Complete your profile (skills + interests) to unlock sharper recommendations.")
    return insights[:4]
