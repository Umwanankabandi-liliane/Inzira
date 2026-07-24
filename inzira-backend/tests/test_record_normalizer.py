"""Unit tests for presentation normalization."""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from detail_page_extractor import extract_detail_page
from record_normalizer import (
    is_generic_listing_title,
    normalize_extracted_record,
    normalize_title,
    parse_deadline_iso,
)

# --- Sample 1: JSON-LD (FDO-style) ---
JSON_LD_HTML = """
<html><body>
<script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "Senior Data Analyst job position at Raising The Village (RTV)",
  "description": "Raising The Village is hiring a Senior Data Analyst in Kigali, Rwanda. Apply before 30 June 2026.",
  "hiringOrganization": {"name": "Raising The Village (RTV)"},
  "validThrough": "2026-06-30T23:59:00",
  "jobLocation": {"name": "Kigali, Rwanda"}
}
</script>
</body></html>
"""

# --- Sample 2: h1-only (Job in Rwanda style) ---
JOBINRWANDA_HTML = """
<html><head><title>Head of Risk and Compliance | Job in Rwanda</title></head>
<body><article>
<h1>Head of Risk and Compliance</h1>
<p>The company seeks a Head of Risk and Compliance based in Kicukiro, Rwanda.
Candidates should apply online before 15 August 2026. Bachelor degree required.</p>
<p>Apply through the official Job in Rwanda portal today.</p>
</article></body></html>
"""

# --- Sample 3: messy entities / suffix noise ---
MESSY_HTML = """
<html><head><title>Digital Media &amp; Content Creation Trainer job position at KIGALIJOB &#8211; Free digital opportunities</title></head>
<body>
<h1>Digital Media &amp; Content Creation Trainer job position at KIGALIJOB</h1>
<p>KIGALIJOB   is hiring a Digital Media &amp; Content Creation Trainer in Gasabo, Rwanda.
Deadline: 19 May 2026. Send CV and cover letter.</p>
</body></html>
"""


def test_json_ld_clean_title_org_deadline():
    rec = extract_detail_page(JSON_LD_HTML, "https://fdo.net.rw/senior-data-analyst-rtv/")
    assert rec is not None
    assert "Senior Data Analyst" in rec["title"]
    assert "Raising The Village" in rec["organization"]
    assert rec["deadline"] == "2026-06-30"
    assert rec.get("district") == "Gasabo"
    assert len(rec["snippet"]) >= 40


def test_h1_only_jobinrwanda():
    rec = extract_detail_page(JOBINRWANDA_HTML, "https://www.jobinrwanda.com/job/head-risk-compliance/")
    assert rec is not None
    assert rec["title"] == "Head of Risk and Compliance"
    assert "Job in Rwanda" not in rec["title"]
    assert rec["organization"]  # fallback site name or domain
    assert rec["deadline"] == "2026-08-15"
    assert rec.get("district") == "Kicukiro"


def test_messy_html_cleaned():
    rec = extract_detail_page(MESSY_HTML, "https://fdo.net.rw/digital-media-trainer/")
    assert rec is not None
    assert "Digital Media" in rec["title"]
    assert "Free digital opportunities" not in rec["title"]
    assert "&amp;" not in rec["title"]
    assert rec["deadline"] == "2026-05-19"
    assert rec.get("district") == "Gasabo"


def test_reject_generic_listing_titles():
    assert is_generic_listing_title("Jobs")
    assert is_generic_listing_title("About us")
    assert normalize_title("Vacancies | Job in Rwanda", domain="jobinrwanda.com") == ""


def test_parse_deadline_iso():
    assert parse_deadline_iso("30 June 2026") == "2026-06-30"
    assert parse_deadline_iso("not a date") == ""
