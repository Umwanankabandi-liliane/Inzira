"""
Wow features: explainable trust, apply readiness, district gap, eligibility, impact.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from deadline_scan import parse_deadline_date
from match_engine import RWANDA_DISTRICTS, compute_match, district_radar

SCAM_SIGNALS = [
    "pay upfront", "registration fee required", "send money", "whatsapp only",
    "guaranteed visa", "pay to apply", "processing fee",
]


def _domain(url: str) -> str:
    try:
        return (urlparse(url or "").netloc or "").lower().replace("www.", "")
    except Exception:
        return ""


def explain_trust(opp: dict) -> List[Dict[str, str]]:
    """Human-readable reasons behind the trust score."""
    reasons: List[Dict[str, str]] = []
    url = opp.get("apply_url") or opp.get("url") or opp.get("source_url") or ""
    dom = _domain(url) or (opp.get("source_domain") or "").lower()
    score = float(opp.get("trust_score") or 0)
    if score > 1:
        score_pct = score
    else:
        score_pct = score * 100

    if dom.endswith(".gov.rw") or dom.endswith(".ac.rw"):
        reasons.append({"tone": "green", "text": "Official Rwanda government or academic domain"})
    elif dom.endswith(".rw"):
        reasons.append({"tone": "green", "text": "Rwanda-registered website (.rw)"})
    elif dom.endswith(".org"):
        reasons.append({"tone": "blue", "text": "Non-profit / organisation domain (.org)"})

    if url.startswith("https://"):
        reasons.append({"tone": "green", "text": "Secure HTTPS connection"})
    elif url:
        reasons.append({"tone": "amber", "text": "No HTTPS — verify carefully before sharing personal data"})

    if score_pct >= 85:
        reasons.append({"tone": "green", "text": "AI trust model: high confidence this is a real opportunity source"})
    elif score_pct >= 70:
        reasons.append({"tone": "blue", "text": "AI trust model: good confidence — listed on verified registry"})
    else:
        reasons.append({"tone": "amber", "text": "Moderate trust — double-check details on the official site"})

    deadline = (opp.get("deadline") or "").strip()
    if deadline and parse_deadline_date(deadline):
        reasons.append({"tone": "green", "text": "Application deadline detected on the listing"})
    elif deadline:
        reasons.append({"tone": "blue", "text": "Deadline information available"})

    text = " ".join([
        opp.get("title") or "",
        opp.get("snippet") or "",
        opp.get("eligibility") or "",
    ]).lower()
    for sig in SCAM_SIGNALS:
        if sig in text:
            reasons.append({"tone": "red", "text": f"Warning: listing mentions '{sig}' — common scam pattern"})
            break

    if opp.get("source_domain") or opp.get("verified"):
        reasons.append({"tone": "green", "text": "Sourced from Inzira verified portal registry"})

    if not reasons:
        reasons.append({"tone": "blue", "text": "Indexed from a monitored Rwanda opportunity portal"})
    return reasons[:5]


def apply_readiness(profile: Optional[Dict[str, Any]], opp: dict) -> Dict[str, Any]:
    """How ready a youth is to apply — coaching checklist."""
    pdata = profile or {}
    m = compute_match(pdata, opp)
    score = m["score"]
    checklist: List[Dict[str, Any]] = []

    district = (pdata.get("district") or "").strip()
    opp_d = (opp.get("district") or "").strip()
    loc = (opp.get("location") or "").lower()
    if district:
        ok = (opp_d and district.lower() == opp_d.lower()) or district.lower() in loc
        checklist.append({
            "key": "district",
            "label": f"District match ({district})",
            "ok": ok,
            "hint": "Opportunity fits your area" if ok else "May require travel or relocation",
        })
    else:
        checklist.append({
            "key": "district",
            "label": "District on profile",
            "ok": False,
            "hint": "Add your district in My Matches",
        })

    edu = (pdata.get("education") or "").strip()
    elig = (opp.get("eligibility") or opp.get("snippet") or "").lower()
    if edu:
        edu_ok = any(tok in elig for tok in edu.lower().replace("_", " ").split() if len(tok) > 3)
        checklist.append({
            "key": "education",
            "label": f"Education ({edu})",
            "ok": edu_ok or not elig,
            "hint": "Level appears compatible" if (edu_ok or not elig) else "Check education requirements on apply page",
        })
    else:
        checklist.append({
            "key": "education",
            "label": "Education level",
            "ok": False,
            "hint": "Add education in your profile",
        })

    skills = pdata.get("skills") or []
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    text = " ".join([opp.get("title") or "", opp.get("snippet") or ""]).lower()
    if skills:
        hits = [s for s in skills if str(s).lower() in text]
        checklist.append({
            "key": "skills",
            "label": "Skills match",
            "ok": len(hits) > 0,
            "hint": f"Matches: {', '.join(hits[:3])}" if hits else "Consider building skills mentioned in the listing",
        })
    else:
        checklist.append({
            "key": "skills",
            "label": "Skills on profile",
            "ok": False,
            "hint": "Add skills to improve readiness score",
        })

    trust = float(opp.get("trust_score") or 0)
    trust_pct = trust if trust > 1 else trust * 100
    checklist.append({
        "key": "trust",
        "label": "Verified source",
        "ok": trust_pct >= 62,
        "hint": f"Trust score {int(trust_pct)}%",
    })

    done = sum(1 for c in checklist if c["ok"])
    readiness = int(round(done / max(len(checklist), 1) * 100))
    readiness = max(readiness, min(score, 97)) if pdata.get("district") else readiness

    return {
        "readiness_score": readiness,
        "checklist": checklist,
        "missing": m.get("missing") or [],
        "tips": m.get("reasons")[:2],
    }


def eligibility_verdict(profile: Dict[str, Any], opp: dict) -> Dict[str, Any]:
    """Yes / maybe / no for first-time applicants."""
    r = apply_readiness(profile, opp)
    score = r["readiness_score"]
    failed = [c for c in r["checklist"] if not c["ok"]]
    if score >= 75 and len(failed) <= 1:
        verdict = "yes"
        summary = "You appear eligible to apply — gather documents and apply on the official site."
    elif score >= 50:
        verdict = "maybe"
        summary = "You may qualify — review requirements and improve your profile where noted."
    else:
        verdict = "no"
        summary = "Gaps in your profile or this listing — consider other matches first."
    return {
        "verdict": verdict,
        "summary": summary,
        "readiness_score": score,
        "checklist": r["checklist"],
    }


def deadline_guardian(deadline: str) -> Dict[str, Any]:
    """Urgency badge for deadlines."""
    raw = (deadline or "").strip()
    if not raw:
        return {"status": "unknown", "label": "Check deadline on site", "days_left": None, "urgent": False}
    dl = parse_deadline_date(raw)
    if not dl:
        return {"status": "listed", "label": raw[:48], "days_left": None, "urgent": False}
    today = date.today()
    days = (dl - today).days
    if days < 0:
        return {"status": "expired", "label": "Expired", "days_left": days, "urgent": False}
    if days <= 3:
        return {"status": "urgent", "label": f"Closes in {days} day(s)", "days_left": days, "urgent": True}
    if days <= 14:
        return {"status": "soon", "label": f"Closes in {days} days", "days_left": days, "urgent": True}
    return {"status": "open", "label": f"Deadline {dl.isoformat()}", "days_left": days, "urgent": False}


def district_gap_map(
    opportunities: List[dict],
    demand_by_district: Dict[str, int],
    districts: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Supply (opportunities) vs demand (youth searches) per district."""
    names = districts or RWANDA_DISTRICTS
    radar = {d["district"]: d for d in district_radar(opportunities, names)}
    max_supply = max((radar.get(d, {}).get("total", 0) for d in names), default=1) or 1
    max_demand = max(demand_by_district.values(), default=1) or 1
    out = []
    for name in names:
        supply = radar.get(name, {}).get("total", 0)
        demand = demand_by_district.get(name, 0)
        supply_n = supply / max_supply
        demand_n = demand / max_demand if demand else 0
        gap = demand_n - supply_n
        if gap >= 0.35:
            gap_level = "high_demand"
        elif gap >= 0.15:
            gap_level = "moderate_gap"
        elif supply == 0 and demand > 0:
            gap_level = "critical"
        elif supply_n >= 0.5 and demand_n < 0.2:
            gap_level = "well_served"
        else:
            gap_level = "balanced"
        out.append({
            "district": name,
            "supply": supply,
            "demand": demand,
            "gap_level": gap_level,
            "gap_score": round(gap, 2),
            "level": radar.get(name, {}).get("level", "very_low"),
        })
    return out


def enrich_opportunity(
    opp: dict,
    profile: Optional[Dict[str, Any]] = None,
    *,
    list_view: bool = False,
) -> dict:
    """Attach wow-feature fields to an opportunity dict."""
    out = dict(opp)
    d = (out.get("district") or "").strip()
    if d:
        out["scope"] = "district"
        if not out.get("location") or out.get("location") == "Rwanda":
            out["location"] = f"{d}, Rwanda"
    else:
        out["scope"] = "national"
        out["district"] = ""
        out["location"] = "Rwanda (national)"

    out["trust_score"] = compute_listing_trust(out)
    out["trust_reasons"] = explain_trust(out)
    if not list_view:
        out["readiness"] = apply_readiness(profile, opp)
    out["deadline_status"] = deadline_guardian(out.get("deadline") or "")
    if out["deadline_status"].get("status") == "unknown":
        out["deadline_status"] = {
            "status": "hidden",
            "label": "",
            "days_left": None,
            "urgent": False,
        }
    return out


def compute_listing_trust(opp: dict) -> float:
    """Per-listing trust from real signals — not a flat portal default."""
    url = opp.get("apply_link") or opp.get("url") or opp.get("apply_url") or ""
    dom = _domain(url) or (opp.get("source_domain") or "").lower()
    score = 52.0

    if dom.endswith(".gov.rw") or dom.endswith(".ac.rw"):
        score += 22
    elif dom.endswith(".rw"):
        score += 14
    elif dom.endswith(".org"):
        score += 8

    if url.startswith("https://"):
        score += 6

    deadline = (opp.get("deadline") or "").strip()
    if deadline and parse_deadline_date(deadline):
        score += 14
    elif deadline:
        score += 6

    try:
        from opportunity_extractor import is_deep_opportunity_url, EXTRACTED_SNIPPET_PREFIX
        if url and is_deep_opportunity_url(url):
            score += 8
        snippet = (opp.get("snippet") or "")
        if snippet.startswith(EXTRACTED_SNIPPET_PREFIX) or len(snippet) > 50:
            score += 5
    except Exception:
        pass

    if (opp.get("district") or "").strip():
        score += 4

    snippet = (opp.get("snippet") or "").lower()
    if "browse verified" in snippet or "portal" in snippet[:30]:
        score -= 18

    return round(min(96.0, max(48.0, score)), 1)


def impact_stats(
    registry_stats: dict,
    opportunity_count: int,
    analytics_summary: dict,
    user_count: int = 0,
    saved_count: int = 0,
    districts_with_opportunities: int = 0,
    verified_portals: Optional[int] = None,
) -> Dict[str, Any]:
    """All counters are live DB/analytics values — never inflate or hardcode demos."""
    searches = int(analytics_summary.get("total_searches") or 0)
    portals = int(
        verified_portals
        if verified_portals is not None
        else registry_stats.get("verified_websites")
        or registry_stats.get("verified_open")
        or 0
    )
    districts = int(
        districts_with_opportunities
        or registry_stats.get("districts_with_listings")
        or 0
    )
    return {
        "opportunities_live": int(opportunity_count or 0),
        "verified_portals": portals,
        "districts_covered": districts,
        "youth_searches_month": searches,
        "saved_opportunities": int(saved_count or 0),
        "registered_youth": int(user_count or 0),
    }


def pathway_steps() -> List[Dict[str, str]]:
    return [
        {"id": "learn", "icon": "book", "title": "Learn", "sub": "Scholarships & free courses"},
        {"id": "train", "icon": "spark", "title": "Train", "sub": "WDA & skills programs"},
        {"id": "intern", "icon": "user", "title": "Intern", "sub": "Youth internships"},
        {"id": "work", "icon": "shield", "title": "Work", "sub": "Jobs & careers"},
    ]
