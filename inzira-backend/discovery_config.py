"""
Discovery queries — ALL opportunity websites Rwanda-wide.
Focus: job boards, aggregators, NGOs, startups (.com / .org / .rw / any TLD).
NOT limited to government domains.
"""

INZIRA_CATEGORIES = [
    "scholarship",
    "job",
    "internship",
    "training",
    "competition",
    "program",
    "free_course",
]

# Extra broad portal searches (cross-category)
PORTAL_SEED_QUERIES = [
    "Rwanda job portal website apply",
    "Rwanda careers website hiring apply",
    "Rwanda scholarship website apply online",
    "Rwanda internship portal students apply",
    "Rwanda youth opportunities website",
    "Opportunity Desk Africa apply",
    "Igire Rwanda apply programs",
    "African jobs portal Rwanda",
    "NGO jobs Rwanda website",
    "Kigali startup jobs careers website",
    "remote jobs Rwanda website apply",
    "graduate opportunities Rwanda portal",
]

DISCOVERY_QUERIES = {
    "scholarship": [
        "scholarships Rwanda apply website 2025 2026",
        "fully funded scholarship Rwanda .com OR .org apply",
        "university scholarship Rwanda portal apply",
        "Mastercard Foundation Rwanda scholarship apply",
        "DAAD Rwanda scholarship portal",
        "bursary Rwanda students apply online",
        "African scholarship portal Rwanda",
        "Opportunity Desk scholarship apply",
        "HEC Rwanda scholarship apply",
        "private scholarship Rwanda apply",
    ],
    "job": [
        "Job in Rwanda website careers apply",
        "Rwanda job board .com hiring apply",
        "KigaliJob Rwanda vacancies apply",
        "RwandaJob careers portal apply",
        "Great Rwanda Jobs website apply",
        "Ngira Rwanda job portal apply",
        "Kora Rwanda jobs RDB apply",
        "Rwanda NGO recruitment website apply",
        "UN jobs Rwanda portal apply",
        "private sector jobs Rwanda website hiring",
        "remote work Rwanda jobs portal",
        "tech jobs Kigali website apply",
    ],
    "internship": [
        "internships Rwanda apply website",
        "paid internship Kigali portal apply",
        "graduate internship Rwanda .com apply",
        "UN internship Rwanda apply website",
        "NGO internship Rwanda students apply",
        "Igire Rwanda internship apply",
        "corporate internship Rwanda portal",
        "tech internship Rwanda apply online",
    ],
    "training": [
        "free training Rwanda apply website",
        "skills training Rwanda youth portal apply",
        "digital skills bootcamp Rwanda apply",
        "vocational training Rwanda website apply",
        "professional certification Rwanda apply online",
        "WDA Rwanda training apply",
        "coding bootcamp Kigali apply website",
        "women tech training Rwanda apply",
    ],
    "competition": [
        "competitions Rwanda apply website 2025",
        "hackathon Kigali register apply website",
        "innovation challenge Rwanda youth apply",
        "startup pitch competition Rwanda apply",
        "essay competition Rwanda students apply",
        "STEM competition Rwanda apply online",
        "business plan competition Rwanda portal",
    ],
    "program": [
        "youth programs Rwanda apply website",
        "fellowship Rwanda apply portal",
        "Igire Rwanda programs apply website",
        "entrepreneurship program Rwanda apply",
        "RDB youth program Rwanda apply",
        "development fellowship Rwanda apply",
        "leadership program Rwanda youth apply",
        "incubator program Kigali apply website",
    ],
    "free_course": [
        "free online courses Rwanda apply website",
        "MOOC free certification Rwanda apply",
        "free IT courses Rwanda youth apply",
        "e-learning Rwanda free programs apply",
        "Coursera free courses Rwanda apply",
        "digital literacy free course Rwanda apply",
    ],
}

DISCOVERY_DELAY_SECONDS = 1.2
DISCOVERY_MAX_PER_QUERY = 12
