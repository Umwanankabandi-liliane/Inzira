from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("scholarships Rwanda 2025", max_results=5))
    print(f"Found {len(results)} results")
    for r in results:
        print(r['href'])
        print(r['title'])
        print()