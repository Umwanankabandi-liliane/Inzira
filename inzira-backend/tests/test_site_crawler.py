"""Unit tests for deep crawler heuristics (no network)."""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from detail_page_extractor import extract_detail_page, is_js_shell_page
from site_crawler import (
    classify_page,
    content_hash,
    extract_internal_links,
    extract_pagination_links,
    normalize_url,
    opportunity_like_url,
)


LISTING_HTML = """
<html><body>
<h1>Jobs in Rwanda</h1>
<ul>
  <li><a href="/job/software-engineer-kigali">Software Engineer Kigali</a></li>
  <li><a href="/job/data-analyst-rwanda">Data Analyst Rwanda</a></li>
  <li><a href="/job/nurse-gasabo">Nurse Gasabo District</a></li>
  <li><a href="/job/teacher-bugesera">Teacher Bugesera</a></li>
  <li><a href="/job/driver-kicukiro">Driver Kicukiro</a></li>
  <li><a href="/job/accountant-rdb">Accountant RDB</a></li>
  <li><a href="/job/marketing-officer">Marketing Officer Rwanda</a></li>
  <li><a href="/job/hr-intern-hec">HR Intern HEC Rwanda</a></li>
  <li><a href="/job/project-manager">Project Manager Apply Now</a></li>
  <li><a href="/job/logistics-coordinator">Logistics Coordinator Kigali</a></li>
  <li><a href="/job/security-guard">Security Guard Rwanda</a></li>
</ul>
<a rel="next" href="/jobs?page=2">Next</a>
</body></html>
"""

DETAIL_HTML = """
<html><head><title>Senior Data Analyst at RTV | Job in Rwanda</title></head>
<body><article>
<h1>Senior Data Analyst at Raising The Village (RTV)</h1>
<p>Raising The Village is hiring a Senior Data Analyst in Kigali, Rwanda.
Candidates with a Bachelor's degree in Statistics may apply before 30 June 2026.
Send your CV and cover letter through the official application portal.</p>
<p>Apply online today — open to Rwandan youth.</p>
</article></body></html>
"""

JSON_LD_HTML = """
<html><body>
<script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "ICT Help Desk Officer at RISA Rwanda",
  "description": "Apply for ICT Help Desk Officer at RISA in Kigali Rwanda before May 19 2026.",
  "hiringOrganization": {"name": "RISA"},
  "validThrough": "2026-05-19",
  "jobLocation": {"name": "Kigali, Rwanda"}
}
</script>
<h1>ICT Help Desk Officer</h1>
</body></html>
"""


def test_normalize_url_strips_tracking():
    url = normalize_url("https://example.com/job/1?utm_source=x&fbclid=abc#section")
    assert url == "https://example.com/job/1"


def test_opportunity_like_url():
    assert opportunity_like_url("https://jobinrwanda.com/job/analyst-kigali")
    assert not opportunity_like_url("https://jobinrwanda.com/about")


def test_classify_listing_vs_detail():
    assert classify_page(LISTING_HTML, "https://jobinrwanda.com/jobs") == "listing"
    assert classify_page(DETAIL_HTML, "https://jobinrwanda.com/job/senior-data-analyst-rtv") == "detail"


def test_pagination_links():
    links = extract_pagination_links(LISTING_HTML, "https://jobinrwanda.com/jobs", "jobinrwanda.com")
    assert any("page=2" in u for u in links)


def test_internal_links():
    links = extract_internal_links(LISTING_HTML, "https://jobinrwanda.com/jobs", "jobinrwanda.com")
    assert len(links) >= 10


def test_json_ld_extraction():
    rec = extract_detail_page(JSON_LD_HTML, "https://fdo.net.rw/job/risa-ict")
    assert rec is not None
    assert "ICT Help Desk" in rec["title"]
    assert rec.get("organization") == "RISA"


def test_content_hash_stable():
    assert content_hash("Hello  Rwanda") == content_hash("Hello Rwanda")


def test_js_shell_detection():
    shell = "<html><head>" + "<script></script>" * 12 + "</head><body><div id=root></div></body></html>"
    assert is_js_shell_page(shell) is True
    assert is_js_shell_page(DETAIL_HTML) is False
    tiny_react = (
        '<html><head><script src="/main.js"></script></head>'
        '<body><div id="root"></div><title>Internship</title></body></html>'
    )
    assert is_js_shell_page(tiny_react) is True
