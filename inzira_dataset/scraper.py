import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import urllib3
from ddgs import DDGS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.makedirs("raw_pages", exist_ok=True)

queries = [
    # SCHOLARSHIPS
    ("scholarships for youth in Rwanda 2024", "scholarship"),
    ("scholarships for African students 2024", "scholarship"),
    ("fully funded scholarships Africa 2024", "scholarship"),
    ("Rwanda scholarships open applications", "scholarship"),
    ("mastercard foundation scholarships Africa", "scholarship"),
    ("chevening scholarships Africa 2024", "scholarship"),
    ("daad scholarships Africa 2024", "scholarship"),
    ("scholarships for East African students", "scholarship"),
    ("commonwealth scholarships Africa 2024", "scholarship"),
    ("scholarships open applications Rwanda students", "scholarship"),

    # INTERNSHIPS
    ("internships for youth in Rwanda 2024", "internship"),
    ("internship opportunities Rwanda open", "internship"),
    ("UN internships Africa 2024", "internship"),
    ("UNICEF internships Africa 2024", "internship"),
    ("UNDP internships Rwanda 2024", "internship"),
    ("NGO internships Rwanda 2024", "internship"),
    ("internships for African graduates 2024", "internship"),
    ("paid internships Africa 2024", "internship"),
    ("internship programs East Africa 2024", "internship"),
    ("internship opportunities Kigali Rwanda", "internship"),

    # JOBS
    ("job vacancies Rwanda 2024", "job"),
    ("jobs in Kigali Rwanda open applications", "job"),
    ("UN jobs Rwanda 2024", "job"),
    ("NGO jobs Rwanda 2024", "job"),
    ("tech jobs Rwanda Kigali 2024", "job"),
    ("job opportunities East Africa 2024", "job"),
    ("entry level jobs Rwanda graduates", "job"),
    ("jobs for young professionals Rwanda", "job"),
    ("Rwanda development board vacancies 2024", "job"),
    ("open job applications Rwanda 2024", "job"),

    # TRAINING
    ("free training programs for youth Rwanda 2024", "training"),
    ("ALX Africa training programs 2024", "training"),
    ("Google training programs Africa 2024", "training"),
    ("Microsoft training programs Africa 2024", "training"),
    ("coding bootcamps Africa 2024 free", "training"),
    ("digital skills training Rwanda 2024", "training"),
    ("leadership training programs Africa youth", "training"),
    ("vocational training programs Rwanda 2024", "training"),
    ("online training programs Africa free 2024", "training"),
    ("skills development programs Rwanda youth", "training"),

    # PROGRAMS
    ("youth programs open applications Rwanda 2024", "program"),
    ("fellowship programs Africa youth 2024", "program"),
    ("YouthConnekt Rwanda programs 2024", "program"),
    ("Igire Rwanda program applications", "program"),
    ("volunteer programs Africa youth 2024", "program"),
    ("exchange programs Africa youth 2024", "program"),
    ("youth development programs Rwanda 2024", "program"),
    ("mentorship programs Africa 2024", "program"),
    ("community programs youth Rwanda 2024", "program"),
    ("youth empowerment programs East Africa 2024", "program"),

    # COMPETITIONS
    ("competitions for youth Rwanda 2024", "competition"),
    ("business competitions Africa 2024", "competition"),
    ("innovation competitions Rwanda 2024", "competition"),
    ("hackathons Rwanda Africa 2024", "competition"),
    ("startup competitions Africa 2024", "competition"),
    ("Microsoft imagine cup 2024", "competition"),
    ("youth competitions East Africa 2024", "competition"),
    ("entrepreneurship competitions Africa 2024", "competition"),
    ("tech competitions Rwanda 2024", "competition"),
    ("prize competitions young Africans 2024", "competition"),

    # FREE COURSES
    ("free online courses Africa 2024", "free_course"),
    ("free online courses Rwanda youth 2024", "free_course"),
    ("Coursera free courses Africa 2024", "free_course"),
    ("edX free courses Africa 2024", "free_course"),
    ("Google free courses Africa 2024", "free_course"),
    ("ALX free courses Africa 2024", "free_course"),
    ("free coding courses Africa 2024", "free_course"),
    ("free digital skills courses Rwanda", "free_course"),
    ("Khan Academy free courses", "free_course"),
    ("free online learning platforms Africa", "free_course"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

results = []
collected_urls = set()

print("=" * 60)
print("INZIRA DATASET — DDGS METHOD")
print(f"Total queries: {len(queries)}")
print("=" * 60)

for q_index, (query, category) in enumerate(queries):
    print(f"\n[{q_index+1}/{len(queries)}] {category.upper()} — {query}")

    try:
        # Create fresh DDGS instance for each search
        ddgs = DDGS()
        search_results = list(ddgs.text(query, max_results=8))
        print(f"  Found {len(search_results)} URLs")

        for result in search_results:
            url = result.get("href", "")

            if not url or url in collected_urls:
                continue

            # Skip social media and irrelevant sites
            skip_domains = ["facebook.com", "twitter.com", "instagram.com",
                          "youtube.com", "tiktok.com", "linkedin.com/posts",
                          "reddit.com", "wikipedia.org"]
            if any(domain in url for domain in skip_domains):
                print(f"  Skipping social media: {url[:50]}")
                continue

            try:
                print(f"  Scraping: {url[:70]}")

                page = requests.get(
                    url,
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                if page.status_code == 200:
                    soup = BeautifulSoup(page.content, "html.parser")

                    for tag in soup(["script", "style", "nav", "footer"]):
                        tag.decompose()

                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    text = " ".join(line for line in lines if line)

                    if len(text) > 300:
                        results.append({
                            "url": url,
                            "category": category,
                            "text": text[:5000],
                            "bert_label": 1,
                            "roberta_label": category,
                        })
                        collected_urls.add(url)
                        print(f"  ✓ {len(text)} chars — total so far: {len(results)}")
                    else:
                        print(f"  ✗ Too short")
                else:
                    print(f"  ✗ Status {page.status_code}")

            except Exception as e:
                print(f"  ✗ {str(e)[:50]}")

            time.sleep(2)

    except Exception as e:
        print(f"  ✗ Search error: {str(e)[:50]}")

    # Save progress after every query
    if results:
        pd.DataFrame(results).to_csv("raw_pages/opportunity_pages.csv", index=False)

    # Wait between searches to avoid blocking
    print(f"  Waiting before next search...")
    time.sleep(5)

# Final save
print("\n" + "=" * 60)
print(f"DONE — Total collected: {len(results)} pages")
print("=" * 60)

df = pd.DataFrame(results)
df.to_csv("raw_pages/opportunity_pages.csv", index=False)
print("✓ Saved to raw_pages/opportunity_pages.csv")

if len(results) > 0:
    print("\n── SUMMARY BY CATEGORY ────────────────────────────")
    summary = df.groupby("category").size().reset_index(name="collected")
    print(summary.to_string(index=False))