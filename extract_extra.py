"""
Extract additional BLS data from scraped HTML: annual openings, wage range,
important qualities, training requirements, and how-to-become-one text.

Patches site/data.json with new fields (keeps existing fields intact).

Usage:
    python3 extract_extra.py
"""

import json
import os
import re
from bs4 import BeautifulSoup


def extract_from_html(slug, soup):
    """Extract additional fields from one BLS occupation page."""
    extra = {}

    # Annual openings (tab-6)
    tab6 = soup.find("div", id="tab-6")
    if tab6:
        text = tab6.get_text()
        m = re.search(r"About ([\d,]+) openings", text)
        if m:
            extra["openings"] = int(m.group(1).replace(",", ""))

    # Wage range: 10th and 90th percentile (tab-5)
    tab5 = soup.find("div", id="tab-5")
    if tab5:
        text = tab5.get_text()
        p10 = re.search(r"lowest 10 percent earned less than \$([\d,]+)", text)
        p90 = re.search(r"highest 10 percent earned more than \$([\d,]+)", text)
        if p10:
            extra["pay_p10"] = int(p10.group(1).replace(",", ""))
        if p90:
            extra["pay_p90"] = int(p90.group(1).replace(",", ""))

    # Important qualities (tab-4)
    tab4 = soup.find("div", id="tab-4")
    if tab4:
        article = tab4.find("article")
        if article:
            h3 = article.find("h3", string=re.compile("Important Qualities"))
            if h3:
                qualities = []
                for sib in h3.next_siblings:
                    if getattr(sib, "name", None) == "h3":
                        break
                    if getattr(sib, "name", None) == "p":
                        strong = sib.find("strong")
                        if strong:
                            name = strong.get_text(strip=True).rstrip(". ")
                            qualities.append(name)
                if qualities:
                    extra["qualities"] = qualities

            # How to become one: collect section headings and key info
            education_h3 = article.find("h3", string=re.compile("Education"))
            if education_h3:
                parts = []
                for sib in education_h3.next_siblings:
                    if getattr(sib, "name", None) == "h3":
                        break
                    if hasattr(sib, "get_text"):
                        t = sib.get_text(strip=True)
                        if t:
                            parts.append(t)
                if parts:
                    extra["education_detail"] = " ".join(parts)

            # Licenses/certs
            cert_h3 = article.find("h3", string=re.compile("Licenses|Certifications"))
            if cert_h3:
                parts = []
                for sib in cert_h3.next_siblings:
                    if getattr(sib, "name", None) == "h3":
                        break
                    if hasattr(sib, "get_text"):
                        t = sib.get_text(strip=True)
                        if t:
                            parts.append(t)
                if parts:
                    extra["certifications"] = " ".join(parts)

    # Top industries (tab-3)
    tab3 = soup.find("div", id="tab-3")
    if tab3:
        table = tab3.find("table", class_="ooh-tab-table")
        if table:
            industries = []
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) == 2:
                    name = cells[0].get_text(strip=True)
                    pct_text = cells[1].get_text(strip=True).replace("%", "").strip()
                    try:
                        industries.append({"name": name, "pct": int(pct_text)})
                    except ValueError:
                        pass
            if industries:
                extra["industries"] = industries

    return extra


def main():
    html_dir = "html"
    all_extra = {}

    for fname in sorted(os.listdir(html_dir)):
        if not fname.endswith(".html"):
            continue
        slug = fname.replace(".html", "")
        with open(os.path.join(html_dir, fname)) as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        extra = extract_from_html(slug, soup)
        if extra:
            all_extra[slug] = extra

    print(f"Extracted extra data for {len(all_extra)} occupations")

    # Stats
    fields = ["openings", "pay_p10", "pay_p90", "qualities", "education_detail", "certifications", "industries"]
    for field in fields:
        count = sum(1 for v in all_extra.values() if field in v)
        print(f"  {field}: {count}")

    # Patch data.json
    with open("site/data.json") as f:
        data = json.load(f)

    patched = 0
    for d in data:
        extra = all_extra.get(d["slug"], {})
        if extra:
            d.update(extra)
            patched += 1

    with open("site/data.json", "w") as f:
        json.dump(data, f)

    print(f"Patched {patched}/{len(data)} occupations in data.json")


if __name__ == "__main__":
    main()
