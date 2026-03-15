"""
Extract BLS "Similar Occupations" from scraped HTML and patch site/data.json.

The BLS OOH pages have a "Similar Occupations" tab (tab-8) with a table of
related occupations. parse_detail.py skips this tab, so this data was never
extracted. This script reads it from the raw HTML and patches data.json.

Usage:
    uv run python extract_similar.py
"""

import json
import os
from bs4 import BeautifulSoup


def extract_similar_occupations():
    similar_map = {}
    html_dir = "html"

    for fname in sorted(os.listdir(html_dir)):
        if not fname.endswith(".html"):
            continue
        slug = fname.replace(".html", "")

        with open(os.path.join(html_dir, fname)) as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        table = soup.find("table", id="similar-occupations")
        if not table:
            continue

        slugs = []
        seen = set()
        for a in table.find_all("a"):
            href = a.get("href", "")
            if "/ooh/" in href and href.endswith(".htm"):
                s = href.rstrip("/").split("/")[-1].replace(".htm", "")
                if s not in seen:
                    seen.add(s)
                    slugs.append(s)

        similar_map[slug] = slugs

    return similar_map


def main():
    similar_map = extract_similar_occupations()
    print(f"Extracted similar occupations for {len(similar_map)} occupations")

    with open("site/data.json") as f:
        data = json.load(f)

    valid_slugs = {d["slug"] for d in data}

    patched = 0
    for d in data:
        similar = similar_map.get(d["slug"], [])
        d["similar"] = [s for s in similar if s in valid_slugs]
        if d["similar"]:
            patched += 1

    with open("site/data.json", "w") as f:
        json.dump(data, f)

    print(f"Patched {patched}/{len(data)} occupations with similar occupation data")

    counts = [len(d["similar"]) for d in data if d.get("similar")]
    if counts:
        print(f"Average similar occupations: {sum(counts)/len(counts):.1f}")
        print(f"Range: {min(counts)} to {max(counts)}")


if __name__ == "__main__":
    main()
