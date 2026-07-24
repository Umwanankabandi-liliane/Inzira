import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import json
import urllib3
from ddgs import DDGS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.makedirs("raw_pages", exist_ok=True)

queries = [
    # News articles
    ("Rwanda news today 2024", "not_opportunity"),
    ("Africa news today 2024", "not_opportunity"),
    ("Kigali city news 2024", "not_opportunity"),
    ("Rwanda economy news 2024", "not_opportunity"),
    ("East Africa politics news 2024", "not_opportunity"),

    # General information
    ("history of Rwanda", "not_opportunity"),
    ("Rwanda tourism places to visit", "not_opportunity"),
    ("African culture traditions", "not_opportunity"),
    ("Rwanda geography climate", "not_opportunity"),
    ("Kigali city information", "not_opportunity"),

    # Technology general
    ("what is artificial intelligence", "not_opportunity"),
    ("how does machine learning work", "not_opportunity"),
    ("what is python programming", "not_opportunity"),
    ("history of the internet", "not_opportunity"),
    ("what is a mobile application", "not_opportunity"),

    # Health and lifestyle
    ("healthy eating tips Africa", "not_opportunity"),
    ("mental health awareness Rwanda", "not_opportunity"),
    ("sports news Africa 2024", "not_opportunity"),
    ("music culture Rwanda", "not_opportunity"),
    ("fashion trends Africa 2024", "not_opportunity"),

    # Business general
    ("how to start a business Rwanda", "not_opportunity"),
    ("Rwanda GDP economic growth", "not_opportunity"),
    ("African startups success stories", "not_opportunity"),
    ("investing in Africa 2024", "not_opportunity"),
    ("Rwanda banking services", "not_opportunity"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

results = []
collected_urls = set()

print("=" * 60)
print("INZIRA — NON OPPORTUNITY PAGES COLLECTION")
print(f"Total queries: {len(queries)}")
print("=" * 60)

def save_progress(data):
    # Save as JSON — handles all special characters
    with open("raw_pages/non_opportunity_pages.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

for q_index, (query, category) in enumerate(queries):
    print(f"\n[{q_index+1}/{len(queries)}] {query}")

    try:
        ddgs = DDGS()
        search_results = list(ddgs.text(query, max_results=8))
        print(f"  Found {len(search_results)} URLs")

        for result in search_results:
            url = result.get("href", "")

            if not url or url in collected_urls:
                continue

            skip_domains = ["facebook.com", "twitter.com", "instagram.com",
                          "youtube.com", "tiktok.com", "reddit.com"]
            if any(domain in url for domain in skip_domains):
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

                    # Clean text
                    text = text.encode("utf-8", errors="ignore").decode("utf-8")
                    text = text[:5000]

                    if len(text) > 300:
                        results.append({
                            "url": url,
                            "category": "not_opportunity",
                            "text": text,
                            "bert_label": 0,
                            "roberta_label": "not_opportunity",
                        })
                        collected_urls.add(url)
                        print(f"  ✓ {len(text)} chars — total: {len(results)}")
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
        save_progress(results)
        print(f"  Progress saved — {len(results)} pages so far")

    time.sleep(5)

# Final save as JSON
print("\n" + "=" * 60)
print(f"DONE — Total collected: {len(results)} non-opportunity pages")
print("=" * 60)

save_progress(results)
print("✓ Saved to raw_pages/non_opportunity_pages.json")
print(f"Total: {len(results)} pages")