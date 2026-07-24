"""
OPTIONAL BOOTSTRAP ONLY — not the product list.

You do NOT need to know every Rwanda opportunity website. Inzira discovers them:
  1. Web search (any domain: .com, .org, .rw, …)
  2. AI models judge: does this WEBSITE host apply-able opportunities?
  3. Registry remembers AI-approved sites for faster future searches

This file only queues a few starting URLs for offline `build_registry.py verify`.
Nothing here appears in the app until AI verifies it.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

DEFAULT_HARVEST_BUDGETS: Dict[str, int] = {
    "max_pages": 150,
    "max_depth": 3,
    "max_detail_pages": 100,
}

# Conservative budgets for AI-discovered (non-configured) verified portals.
DISCOVERED_HARVEST_BUDGETS: Dict[str, int] = {
    "max_pages": 25,
    "max_depth": 2,
    "max_detail_pages": 12,
}

CATEGORY_CRAWL_PATHS: Dict[str, List[str]] = {
    "job": ["/jobs", "/careers", "/vacancies", "/recruitment", "/opportunities"],
    "scholarship": ["/scholarships", "/bursaries", "/funding", "/grants", "/admissions"],
    "internship": ["/internships", "/interns", "/attachments"],
    "training": ["/training", "/trainings", "/skills", "/tvet", "/courses"],
    "program": ["/programs", "/programmes", "/initiatives", "/youth"],
    "competition": ["/competitions", "/challenges", "/awards"],
    "free_course": ["/courses", "/learn", "/mooc"],
}

DEFAULT_LISTING_PATHS = ["/", "/announcements", "/news", "/opportunities"]

# Each source = one website card in the app (not random blog posts).
RWANDA_SOURCES: List[Dict] = [
    {
        "name": "Higher Education Council (HEC Rwanda)",
        "domain": "hec.gov.rw",
        "url": "https://www.hec.gov.rw",
        "categories": ["scholarship", "program"],
        "paths": ["/scholarships", "/announcements", "/"],
        # Known limitation: JS-rendered scholarship portal — static HTML has no listing
        # body (same class of issue as Kora). Needs Playwright/headless fetch.
        "known_limitation": "js_rendered",
    },
    {
        "name": "Ministry of Education Rwanda",
        "domain": "minedu.gov.rw",
        "url": "https://www.minedu.gov.rw",
        "categories": ["scholarship", "program", "training"],
        "paths": ["/scholarships", "/announcements", "/"],
    },
    {
        "name": "Workforce Development Authority (WDA)",
        "domain": "wda.gov.rw",
        "url": "https://www.wda.gov.rw",
        "categories": ["training", "program", "internship"],
        "paths": ["/training", "/programs", "/"],
    },
    {
        "name": "Rwanda Development Board (RDB)",
        "domain": "rdb.rw",
        "url": "https://rdb.rw",
        "categories": ["program", "job", "training"],
        "paths": ["/invest-in-rwanda", "/careers", "/"],
    },
    {
        "name": "Public Service Commission — Recruitment",
        "domain": "mifotra.gov.rw",
        "url": "https://www.mifotra.gov.rw",
        "categories": ["job", "program"],
        "paths": ["/recruitment", "/announcements", "/"],
    },
    {
        "name": "Job in Rwanda",
        "domain": "jobinrwanda.com",
        "url": "https://www.jobinrwanda.com",
        "categories": ["job", "internship"],
        "paths": ["/", "/jobs/all", "/jobs/internships", "/jobs/consultancy"],
        "listing_urls": ["/jobs/all", "/jobs/internships", "/jobs/consultancy"],
        "seed_strict": True,
        "harvest": {"max_pages": 200, "max_detail_pages": 120, "request_timeout": 30, "harvest_tier": "daily"},
    },
    {
        "name": "Free digital opportunities (FDO)",
        "domain": "fdo.net.rw",
        "url": "https://fdo.net.rw",
        "categories": ["job", "scholarship", "internship", "training"],
        "paths": ["/category/jobs/", "/"],
        "listing_urls": [
            "/category/jobs/",
            "/category/internships/",
            "/category/scholarships/",
            "/category/trainings/",
        ],
        "harvest": {"max_pages": 200, "max_detail_pages": 150, "harvest_tier": "daily"},
    },
    # International aggregators (Tier B expected) — conservative budgets
    {
        "name": "Opportunity Desk",
        "domain": "opportunitydesk.org",
        "url": "https://opportunitydesk.org",
        # Multi-category aggregator (scholarships, fellowships, grants, competitions,
        # programs). Category hints only — RoBERTa still classifies each page.
        "categories": [
            "scholarship", "program", "competition", "training", "free_course", "job",
        ],
        "paths": ["/", "/tag/rwanda/", "/category/fellowships/", "/category/scholarships/"],
        "listing_urls": [
            "/",
            "/tag/rwanda/",
            "/category/fellowships-and-scholarships/",
            "/category/fellowships-and-scholarships/undergraduate/",
            "/category/fellowships-and-scholarships/masters-postgraduate/",
            "/category/fellowships-and-scholarships/short-courses/",
            "/category/training-and-conference/",
            "/category/competitions/",
        ],
        "harvest": {"max_pages": 40, "max_depth": 2, "max_detail_pages": 25, "harvest_tier": "weekly", "request_timeout": 25},
    },
    {
        "name": "Opportunities for Africans",
        "domain": "opportunitiesforafricans.com",
        "url": "https://www.opportunitiesforafricans.com",
        "categories": ["scholarship", "program", "competition", "training", "free_course", "internship", "job"],
        "paths": ["/", "/category/fellowships/", "/category/scholarships/"],
        "listing_urls": ["/", "/category/fellowships/", "/category/scholarships/"],
        "harvest": {"max_pages": 25, "max_depth": 2, "max_detail_pages": 12, "harvest_tier": "weekly"},
    },
    {
        "name": "DAAD Scholarship Database",
        "domain": "daad.de",
        "url": "https://www2.daad.de",
        "categories": ["scholarship"],
        "paths": ["/en/study-and-research-in-germany/scholarships/"],
        "listing_urls": ["/en/study-and-research-in-germany/scholarships/"],
        "harvest": {"max_pages": 20, "max_depth": 2, "max_detail_pages": 10, "harvest_tier": "weekly"},
    },
    {
        "name": "Ngira Job Portal",
        "domain": "ngira.rw",
        "url": "https://ngira.rw",
        "categories": ["job", "internship"],
        "paths": ["/", "/jobs"],
    },
    {
        "name": "University of Rwanda",
        "domain": "ur.ac.rw",
        "url": "https://ur.ac.rw",
        "categories": ["scholarship", "program", "training"],
        "paths": ["/admissions", "/announcements", "/"],
    },
    {
        "name": "Rwanda Social Security Board",
        "domain": "rssb.rw",
        "url": "https://www.rssb.rw",
        "categories": ["job", "program"],
        "paths": ["/careers", "/announcements", "/"],
    },
    {
        "name": "National Industrial Research Agency (NIRDA)",
        "domain": "nirda.gov.rw",
        "url": "https://www.nirda.gov.rw",
        "categories": ["program", "training", "internship"],
        "paths": ["/", "/programs"],
    },
    {
        "name": "Rwanda Biomedical Centre",
        "domain": "rbc.gov.rw",
        "url": "https://www.rbc.gov.rw",
        "categories": ["job", "program", "training"],
        "paths": ["/careers", "/announcements", "/"],
    },
    {
        "name": "Rwanda ICT Chamber",
        "domain": "ictchamber.rw",
        "url": "https://ictchamber.rw",
        "categories": ["training", "program"],
        "paths": ["/", "/programs", "/training", "/opportunities"],
        "listing_urls": ["/", "/blog", "/programs", "/training", "/opportunities"],
        "harvest": {"max_pages": 60, "max_depth": 3, "max_detail_pages": 40, "harvest_tier": "weekly"},
        # Known limitation: programme/training routes trip js_rendered early-abort despite
        # a large homepage — treat like HEC/Kora until Playwright exists.
        "known_limitation": "js_rendered",
    },
    {
        "name": "Digital Opportunity Trust — Rwanda",
        "domain": "dotrust.org",
        "url": "https://www.dotrust.org",
        "categories": ["program", "training", "internship"],
        "paths": ["/", "/programs"],
    },
    {
        "name": "Mastercard Foundation Scholars",
        "domain": "mastercardfdn.org",
        "url": "https://mastercardfdn.org/scholars",
        "categories": ["scholarship", "program"],
        "paths": ["/scholars", "/"],
    },
    {
        "name": "DAAD — Rwanda & East Africa",
        "domain": "daad.de",
        "url": "https://www.daad.de/en/study-and-research-in-germany/scholarships",
        "categories": ["scholarship", "program"],
        "paths": ["/"],
    },
    {
        "name": "UN Rwanda — Careers",
        "domain": "un.org",
        "url": "https://careers.un.org",
        "categories": ["job", "internship", "program"],
        "paths": ["/"],
    },
    {
        "name": "UNDP Rwanda",
        "domain": "undp.org",
        "url": "https://www.undp.org/rwanda",
        "categories": ["job", "internship", "program"],
        "paths": ["/jobs", "/procurement", "/"],
    },
    {
        "name": "World Bank — Rwanda Opportunities",
        "domain": "worldbank.org",
        "url": "https://www.worldbank.org/en/country/rwanda",
        "categories": ["program", "job", "scholarship"],
        "paths": ["/"],
    },
    {
        "name": "African Development Bank — Careers",
        "domain": "afdb.org",
        "url": "https://www.afdb.org/en/about-us/careers",
        "categories": ["job", "internship", "program"],
        "paths": ["/"],
    },
    {
        "name": "Kigali Innovation City",
        "domain": "kic.rw",
        "url": "https://kic.rw",
        "categories": ["program", "internship", "training"],
        "paths": ["/", "/programs"],
    },
    {
        "name": "Rwanda Education Board (REB)",
        "domain": "reb.rw",
        "url": "https://www.reb.rw",
        "categories": ["scholarship", "program", "training"],
        "paths": ["/", "/announcements"],
    },
    {
        "name": "African Leadership University (Rwanda)",
        "domain": "alu.ac.rw",
        "url": "https://www.alu.ac.rw",
        "categories": ["scholarship", "program"],
        "paths": ["/admissions", "/"],
    },
    {
        "name": "CMU-Africa",
        "domain": "africa.engineering.cmu.edu",
        "url": "https://www.africa.engineering.cmu.edu",
        "categories": ["scholarship", "program", "training"],
        "paths": ["/admissions", "/"],
    },
    {
        "name": "Irembo — Government Services",
        "domain": "irembo.gov.rw",
        "url": "https://irembo.gov.rw",
        "categories": ["program", "job"],
        "paths": ["/"],
    },
    # ── PRIORITY: sites Rwandans actually use (.com / .org / .rw — not .rw only) ──
    {
        "name": "IGiRE Rwanda",
        "domain": "igirerwanda.org",
        "url": "https://www.igirerwanda.org",
        "categories": ["program", "training", "internship", "job"],
        "paths": ["/programs", "/careers", "/"],
    },
    {
        "name": "Kora — RDB Job Portal",
        "domain": "kora2.rdb.rw",
        "url": "https://www.kora2.rdb.rw",
        "categories": ["job", "internship", "training", "program"],
        "paths": ["/"],
        # Known limitation: JS-rendered job board — listings not in static HTML.
        "known_limitation": "js_rendered",
    },
    # ── NEW SEEDS (2026): under-crawled / missing Rwanda-relevant portals ──
    {
        "name": "National Internship Programme (RDB / MIFOTRA)",
        "domain": "internship.rw",
        "url": "https://internship.rw",
        "categories": ["internship"],
        "paths": ["/", "/opportunities", "/internships", "/positions"],
        "listing_urls": [
            "/",
            "/opportunities",
            "/internships",
            "/positions",
        ],
        "harvest": {"max_pages": 80, "max_depth": 3, "max_detail_pages": 50, "harvest_tier": "daily"},
        # Known limitation: React SPA shell (id=root, ~500B HTML, 0 links).
        # Same class as HEC / Kora — needs Playwright.
        "known_limitation": "js_rendered",
    },
    {
        "name": "National Internship Programme (legacy RDB host)",
        "domain": "internshipdev.rdb.rw",
        "url": "https://internshipdev.rdb.rw",
        "categories": ["internship"],
        "paths": ["/", "/opportunities", "/internships"],
        "listing_urls": ["/", "/opportunities", "/internships", "/positions"],
        "harvest": {"max_pages": 60, "max_depth": 3, "max_detail_pages": 40, "harvest_tier": "daily"},
        # Known limitation: listing routes are thin JS shells; homepage has content but
        # opportunity cards still need client rendering (same class as HEC / Kora).
        "known_limitation": "js_rendered",
    },
    {
        "name": "Ingazi — Digital Skills (GoR / UNICEF / RDB)",
        "domain": "ingazi.rw",
        "url": "https://ingazi.rw",
        "categories": ["free_course"],
        "paths": ["/", "/courses", "/learn", "/programs"],
        "listing_urls": ["/", "/courses", "/learn", "/programs", "/catalogue"],
        "harvest": {"max_pages": 60, "max_depth": 3, "max_detail_pages": 40, "harvest_tier": "weekly"},
        # Known limitation: marketing HTML exposes /courses hub only; individual course
        # catalogue appears to load client-side (no deep apply URLs in static HTML).
        "known_limitation": "js_catalog",
    },
    {
        "name": "Digital Skills Academy (MINICT)",
        "domain": "dsa.minict.gov.rw",
        "url": "https://dsa.minict.gov.rw",
        "categories": ["free_course", "training", "job"],
        "paths": ["/", "/courses", "/training", "/jobs", "/opportunities"],
        "listing_urls": ["/", "/courses", "/training", "/jobs", "/opportunities", "/programs"],
        "harvest": {"max_pages": 60, "max_depth": 3, "max_detail_pages": 40, "harvest_tier": "weekly"},
        # Known limitation: Next.js SPA — static HTML is a thin marketing shell.
        "known_limitation": "js_rendered",
    },
    {
        "name": "National Youth Council Rwanda",
        "domain": "nyc.gov.rw",
        "url": "https://www.nyc.gov.rw",
        "categories": ["program"],
        "paths": ["/", "/programs", "/opportunities", "/announcements"],
        "listing_urls": ["/", "/programs", "/opportunities", "/announcements", "/igire", "/youthconnekt"],
        "harvest": {"max_pages": 50, "max_depth": 3, "max_detail_pages": 30, "harvest_tier": "weekly"},
        # Known limitation: several programme routes return thin shells; crawler early-aborts
        # as js_rendered_suspect (same class as HEC / Kora).
        "known_limitation": "js_rendered",
    },
    {
        "name": "JobWeb Rwanda",
        "domain": "jobwebrwanda.com",
        "url": "https://www.jobwebrwanda.com",
        "categories": ["job"],
        "paths": ["/", "/jobs", "/vacancies"],
        "listing_urls": ["/", "/jobs", "/vacancies", "/find-jobs"],
        "harvest": {"max_pages": 60, "max_depth": 2, "max_detail_pages": 40, "harvest_tier": "daily"},
        # Known limitation: HTTP redirect loop (requests.TooManyRedirects) — site broken
        # or anti-bot; not crawlable with static HTTP client.
        "known_limitation": "redirect_loop",
    },
    {
        "name": "The New Times — Jobs & Tenders",
        "domain": "jobs.newtimes.co.rw",
        "url": "https://jobs.newtimes.co.rw",
        "categories": ["job"],
        "paths": ["/", "/jobs", "/vacancies", "/tenders"],
        "listing_urls": ["/", "/jobs", "/vacancies"],
        "harvest": {"max_pages": 60, "max_depth": 2, "max_detail_pages": 40, "harvest_tier": "daily"},
    },
    {
        "name": "KigaliJob",
        "domain": "kigalijob.com",
        "url": "https://www.kigalijob.com",
        "categories": ["job", "internship", "training"],
        "paths": ["/jobs", "/find-job", "/"],
        "listing_urls": ["/jobs", "/find-job"],
        "seed_strict": True,
        "harvest": {"max_pages": 60, "max_detail_pages": 40, "request_timeout": 30, "harvest_tier": "weekly"},
    },
    {
        "name": "RwandaJob.com",
        "domain": "rwandajob.com",
        "url": "https://www.rwandajob.com",
        "categories": ["job", "internship"],
        "paths": ["/", "/jobs", "/vacancies"],
        "listing_urls": ["/", "/jobs", "/vacancies"],
        "harvest": {"max_pages": 30, "max_detail_pages": 20, "harvest_tier": "weekly"},
    },
    {
        "name": "Great Rwanda Jobs",
        "domain": "greatrwandajobs.com",
        "url": "https://www.greatrwandajobs.com",
        "categories": ["job", "internship", "training"],
        "paths": ["/"],
    },
    {
        "name": "Mastercard Foundation Scholars (UR)",
        "domain": "mcfsp.ur.ac.rw",
        "url": "https://mcfsp.ur.ac.rw",
        "categories": ["scholarship", "program"],
        "paths": ["/"],
    },
    {
        "name": "UR Admissions (e-Filing)",
        "domain": "efiling.ur.ac.rw",
        "url": "https://efiling.ur.ac.rw",
        "categories": ["scholarship", "program"],
        "paths": ["/"],
    },
]

SKIP_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com", "youtube.com",
    "tiktok.com", "linkedin.com", "reddit.com", "wikipedia.org", "pinterest.com",
    "medium.com", "quora.com",
}

# Mirror hosts for the same portal — see listing_quality.DOMAIN_CANONICAL
DOMAIN_ALIASES = {
    "dev.internship.rw": "internship.rw",
    "internshipdev.rdb.rw": "internship.rw",
}


def get_sources_for_category(category: Optional[str]) -> List[Dict]:
    if not category:
        return RWANDA_SOURCES
    return [s for s in RWANDA_SOURCES if category in s["categories"]]


def source_config_for_domain(domain: str) -> Optional[Dict]:
    d = (domain or "").lower().replace("www.", "")
    for src in RWANDA_SOURCES:
        if src.get("domain", "").lower().replace("www.", "") == d:
            return dict(src)
    return None


def is_configured_source(domain: str) -> bool:
    return source_config_for_domain(domain) is not None


def harvest_config_for(domain: str, *, discovered: bool = False) -> Dict[str, int]:
    if discovered:
        return dict(DISCOVERED_HARVEST_BUDGETS)
    src = source_config_for_domain(domain)
    cfg = dict(DEFAULT_HARVEST_BUDGETS)
    if src and isinstance(src.get("harvest"), dict):
        for key in DEFAULT_HARVEST_BUDGETS:
            if key in src["harvest"]:
                cfg[key] = int(src["harvest"][key])
    return cfg


def listing_urls_for(site: Dict[str, Any], category_focus: Optional[str] = None) -> List[str]:
    """Absolute listing-page URLs to seed the deep crawler."""
    base = (site.get("url") or site.get("apply_link") or "").strip().rstrip("/")
    if not base:
        return []
    domain = (site.get("domain") or urlparse(base).netloc or "").replace("www.", "")

    raw_paths: List[str] = []
    if site.get("listing_urls"):
        raw_paths.extend(site["listing_urls"])
    elif site.get("paths"):
        raw_paths.extend(site["paths"])
    else:
        src = source_config_for_domain(domain)
        if src:
            raw_paths.extend(src.get("listing_urls") or src.get("paths") or [])
        raw_paths.extend(DEFAULT_LISTING_PATHS)

    explicit_listing = bool(site.get("listing_urls"))
    cats = site.get("categories") or []
    if isinstance(cats, str):
        import json
        try:
            cats = json.loads(cats)
        except Exception:
            cats = [cats]
    focus = (category_focus or "").strip().lower()
    if not explicit_listing:
        if focus:
            raw_paths.extend(CATEGORY_CRAWL_PATHS.get(focus, []))
        else:
            for cat in cats:
                raw_paths.extend(CATEGORY_CRAWL_PATHS.get(str(cat).lower(), []))

    seen: set[str] = set()
    urls: List[str] = []
    for raw in raw_paths:
        if not raw:
            continue
        if raw.startswith("http://") or raw.startswith("https://"):
            full = raw.rstrip("/")
        else:
            path = raw if raw.startswith("/") else f"/{raw}"
            full = base if path == "/" else f"{base}{path}"
        key = full.lower().rstrip("/")
        if key not in seen:
            seen.add(key)
            urls.append(full)
    return urls or [base]


def domain_of(url: str) -> str:
    from urllib.parse import urlparse
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""
