# Build This Project From Scratch: A Beginner's Guide

> **Who is this for?** Total beginners. If you've never coded before, or you've done a little but never built a real project, this is for you. We explain everything like you're 12.

## What We're Building

We're going to build a website that answers: **"Which jobs will AI replace?"**

Here's what we'll do, step by step:

1. **Grab data** from a government website (web scraping)
2. **Clean it up** so a computer can understand it (parsing)
3. **Ask an AI** to score each job (LLM API calls)
4. **Show it** as a beautiful interactive chart (data visualization)

By the end, you'll have a working website with a giant colorful map of every job in America, colored by how much AI will affect it.

---

## Chapter 0: Setting Up Your Computer

### What you need

- A computer (Mac, Windows, or Linux all work)
- An internet connection
- About 2GB of free disk space

### Installing Python

Python is the programming language we'll use. Think of it like learning a language — except instead of talking to people, you're telling a computer what to do.

**Check if you already have it:**
```bash
python3 --version
```

If you see something like `Python 3.11.x` or higher, you're good! If not:

- **Mac**: Install [Homebrew](https://brew.sh) first (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`), then `brew install python`
- **Windows**: Download from [python.org](https://www.python.org/downloads/). **Check "Add Python to PATH"** during install!
- **Linux**: `sudo apt install python3 python3-pip`

### Installing uv (our project manager)

`uv` is a tool that manages Python projects. It keeps track of what extra tools (called "packages" or "libraries") your project needs, and installs them for you. Think of it like an app store for Python tools.

```bash
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Creating your project

```bash
mkdir jobs        # Create a folder called "jobs"
cd jobs           # Go into that folder
uv init           # Start a new Python project
```

This creates a few files. The important one is `pyproject.toml` — it's like a recipe card that lists everything your project needs.

### Installing the libraries we need

Libraries are code other people wrote that we can reuse. Instead of writing a web browser from scratch, we use one someone already built!

```bash
uv add playwright beautifulsoup4 httpx python-dotenv
uv run playwright install chromium
```

Here's what each one does:

| Library | What it does | Analogy |
|---------|-------------|---------|
| **Playwright** | Controls a real web browser from your code | A robot that clicks and reads web pages for you |
| **BeautifulSoup** | Reads HTML (web page code) and finds specific parts | Ctrl+F on steroids |
| **httpx** | Sends messages to APIs (other computers) over the internet | Sending a letter and getting a reply |
| **python-dotenv** | Keeps secret passwords safe | A locked diary for your API keys |

---

## Chapter 1: Getting the Data (Web Scraping)

### What is web scraping?

Every website is made of **HTML** — a language that tells your browser what to show. When you visit a page, your browser downloads the HTML and turns it into the pretty page you see.

**Web scraping** means: write a program that visits a website, downloads the HTML, and saves it. Instead of you reading 342 job pages one by one, your program reads them all in minutes.

### Our data source: The BLS Occupational Outlook Handbook

The Bureau of Labor Statistics (BLS) is a US government agency that tracks every job in America. Their [Occupational Outlook Handbook](https://www.bls.gov/ooh/) has detailed pages for 342 occupations — pay, education needed, job growth, what the job is like day-to-day.

This is **perfect** data for us because:
- It's free and public (your tax dollars paid for it!)
- It covers every major job in the US economy
- It has both numbers (pay, job count) and descriptions (duties, work environment)

### Step 1: Get the list of all occupations

First, we need a list of all 342 jobs and their URLs. The BLS has an [A-Z index page](https://www.bls.gov/ooh/a-z-index.htm) that lists them all.

Save that page's HTML to a file called `occupational_outlook_handbook.html`, then parse it:

```python
# parse_occupations.py — Extract all occupation names and URLs from the A-Z index

from bs4 import BeautifulSoup
import json

# Read the HTML file we saved
with open("occupational_outlook_handbook.html", "r") as f:
    soup = BeautifulSoup(f.read(), "html.parser")
```

**What's happening here?**
- `open(...)` reads a file from your computer
- `BeautifulSoup(...)` turns the raw HTML text into a "soup" — a structure you can search through
- Think of it like: you have a messy pile of LEGO instructions, and BeautifulSoup organizes them so you can find the piece you need

```python
# The occupation list lives inside a <div> with class "a-z-list"
az_list = soup.find("div", class_="a-z-list")

# Each occupation is in a <li> (list item) tag
occupations = {}
for li in az_list.find_all("li"):
    links = li.find_all("a")  # Find all clickable links
    text = li.get_text()

    # Some entries are aliases ("Therapists, see: Physical Therapists")
    # We skip those and only keep the real entries
    if ", see:" in text or ", see " in text:
        continue
    else:
        if links:
            name = links[0].get_text(strip=True)
            url = links[0]["href"]
            occupations[url] = name
```

**What's happening?**
- `soup.find("div", class_="a-z-list")` — Find the part of the page that has the list
- `find_all("li")` — Get every list item
- `find_all("a")` — Find all links (the `<a>` tag is HTML for a clickable link)
- `get_text()` — Get just the text, ignore all the HTML formatting
- `links[0]["href"]` — Get the URL that the link points to

```python
# Save to a JSON file (a structured data format)
output = []
for url, name in sorted(occupations.items(), key=lambda x: x[1].lower()):
    # Create a "slug" — a URL-friendly version of the name
    # "Software Developers" becomes "software-developers"
    slug = url.split("/")[-2]  # Get the last part of the URL path
    output.append({
        "title": name,
        "url": url,
        "slug": slug,
    })

with open("occupations.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Found {len(output)} occupations!")
```

**JSON** is a way to store structured data. It looks like this:
```json
[
  {
    "title": "Software Developers",
    "url": "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm",
    "slug": "software-developers"
  },
  ...
]
```

Think of JSON like a spreadsheet that computers can read really easily.

### Step 2: Download every occupation page

Now we visit each of those 342 URLs and save the HTML. This is where Playwright comes in — it runs a real Chrome browser that the BLS website thinks is a real person.

```python
# scrape.py — Download all 342 BLS occupation pages

import json
import os
import time
from playwright.sync_api import sync_playwright

with open("occupations.json") as f:
    occupations = json.load(f)

os.makedirs("html", exist_ok=True)  # Create an "html" folder if it doesn't exist

with sync_playwright() as p:
    # Launch a real Chrome browser (not hidden — BLS blocks hidden browsers!)
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for i, occ in enumerate(occupations):
        slug = occ["slug"]
        html_path = f"html/{slug}.html"

        # Skip if we already downloaded this one (caching!)
        if os.path.exists(html_path):
            print(f"  [{i}] CACHED {occ['title']}")
            continue

        print(f"  [{i}] {occ['title']}...", end=" ")

        # Visit the page
        page.goto(occ["url"], wait_until="domcontentloaded")

        # Save the HTML
        html = page.content()
        with open(html_path, "w") as f:
            f.write(html)

        print(f"OK ({len(html):,} bytes)")

        # Wait 1 second between requests — be polite to the server!
        time.sleep(1)

    browser.close()
```

**Key concepts:**
- **`headless=False`** — This means "show the browser window." Why? The BLS website detects and blocks invisible browsers (bots). By showing the window, we look like a real person.
- **Caching** — If we already downloaded a page, skip it. This means if the script crashes halfway, you don't have to start over!
- **`time.sleep(1)`** — Wait 1 second between requests. This is good internet citizenship — don't hammer the server.

> **Why Playwright instead of just downloading the URL?**
> Many modern websites load content with JavaScript *after* the page loads. A simple download would get an empty shell. Playwright runs a real browser that executes the JavaScript, so we get the full page.

---

## Chapter 2: Cleaning the Data (Parsing)

### The problem

We have 342 HTML files, but they're full of website formatting — navigation menus, ads, scripts, styling. We need to extract just the useful content.

### HTML → Markdown

We'll convert each HTML page into **Markdown** — a simple text format that's easy to read. Here's what Markdown looks like:

```markdown
# Software Developers

## Quick Facts

| Field | Value |
|-------|-------|
| Median Pay | $130,160 per year |
| Number of Jobs | 1,847,900 |
| Job Outlook | 17% (Much faster than average) |

## What They Do

Software developers design, build, and maintain software applications...
```

Much cleaner than raw HTML! And importantly, this is what we'll send to the AI later — clean, readable text.

### The parsing code

```python
# parse_detail.py — Convert one BLS HTML page to clean Markdown

from bs4 import BeautifulSoup
import re

def clean(text):
    """Remove extra whitespace."""
    return re.sub(r'\s+', ' ', text).strip()
```

**What's `re.sub(r'\s+', ' ', text)`?**
- `re` is Python's "regular expressions" library — a mini-language for finding patterns in text
- `\s+` means "one or more whitespace characters" (spaces, tabs, newlines)
- We replace them all with a single space
- This turns `"Hello     world\n\n  "` into `"Hello world"`

```python
def parse_ooh_page(html_path):
    with open(html_path, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    md = []  # We'll build our Markdown as a list of lines

    # Get the job title from the <h1> tag
    h1 = soup.find("h1")
    title = clean(h1.get_text()) if h1 else "Unknown"
    md.append(f"# {title}")

    # Extract the Quick Facts table
    qf_table = soup.find("table", id="quickfacts")
    if qf_table:
        md.append("## Quick Facts")
        md.append("| Field | Value |")
        md.append("|-------|-------|")
        for row in qf_table.find("tbody").find_all("tr"):
            field = clean(row.find("th").get_text())
            value = clean(row.find("td").get_text())
            md.append(f"| {field} | {value} |")

    # Extract each content section (duties, education, pay, outlook...)
    # The BLS page uses "tabs" — each section has an ID like tab-2, tab-3, etc.
    panes = soup.find("div", id="panes")
    if panes:
        for tab_id in ["tab-2", "tab-3", "tab-4", "tab-5", "tab-6"]:
            tab = panes.find("div", id=tab_id)
            if not tab:
                continue

            h2 = tab.find("h2")
            if h2:
                md.append(f"## {clean(h2.get_text())}")

            # Get all paragraphs, lists, and sub-headers
            for elem in tab.find_all(["p", "h3", "ul", "li"]):
                text = clean(elem.get_text())
                if text:
                    md.append(text)

    return "\n\n".join(md)
```

**The mental model:** Imagine the HTML page as a tree:
```
<html>
  <body>
    <h1>Software Developers</h1>
    <table id="quickfacts">
      <tr>
        <th>Median Pay</th>
        <td>$130,160</td>
      </tr>
    </table>
    <div id="panes">
      <div id="tab-2">
        <h2>What They Do</h2>
        <p>Software developers design...</p>
      </div>
    </div>
  </body>
</html>
```

BeautifulSoup lets us navigate this tree: "find the table called quickfacts, then get every row, then get the header and data from each row." Like giving directions through a building.

### Processing all 342 pages

```python
# process.py — Run the parser on every HTML file

import json, os
from parse_detail import parse_ooh_page

with open("occupations.json") as f:
    occupations = json.load(f)

os.makedirs("pages", exist_ok=True)

for occ in occupations:
    html_path = f"html/{occ['slug']}.html"
    md_path = f"pages/{occ['slug']}.md"

    if os.path.exists(md_path):
        continue  # Already done, skip

    md = parse_ooh_page(html_path)
    with open(md_path, "w") as f:
        f.write(md)
```

Now we have 342 clean Markdown files in `pages/`.

---

## Chapter 3: Extracting Numbers (Tabulation)

### Why we need this

The Markdown files are great for the AI to read, but we also need structured numbers for our chart — pay, job count, growth rate, education level. Time to build a CSV (spreadsheet).

### Parsing numbers from messy text

Government data is formatted for humans, not computers. "2024 median pay: $62,350 per year / $29.98 per hour" — we need to extract those dollar amounts.

```python
def parse_pay(value):
    """Turn '$62,350 per year / $29.98 per hour' into two numbers."""
    import re
    amounts = re.findall(r'\$([\d,]+(?:\.\d+)?)', value)
    # re.findall finds ALL dollar amounts in the text
    # \$           — a literal dollar sign
    # [\d,]+       — one or more digits or commas (like "62,350")
    # (?:\.\d+)?   — optionally followed by a decimal (like ".98")

    annual = ""
    hourly = ""
    if "per year" in value and amounts:
        annual = amounts[0].replace(",", "")   # "62,350" → "62350"
    if "per hour" in value and len(amounts) >= 2:
        hourly = amounts[-1].replace(",", "")  # "29.98"
    return annual, hourly
```

**Regular expressions** look scary but they're just patterns:
- `\d` = any digit (0-9)
- `+` = one or more of the previous thing
- `[]` = any character in this set
- `?` = optional

So `\$([\d,]+)` means: "find a $ sign, then capture the digits and commas after it."

### The full CSV extraction

`make_csv.py` reads each HTML file, extracts all the structured fields, and writes one row per occupation to `occupations.csv`. The output looks like:

```
title,category,slug,median_pay_annual,num_jobs_2024,outlook_pct,...
Software Developers,Computer,software-developers,130160,1847900,17,...
Registered Nurses,Healthcare,registered-nurses,86070,3175390,6,...
```

---

## Chapter 4: Scoring with AI (The Fun Part)

### What is an API?

An **API** (Application Programming Interface) is a way for programs to talk to each other over the internet. Instead of visiting a website with your browser, your code sends a message and gets a reply.

Think of it like texting:
- **You send:** "Hey AI, read this job description and tell me how exposed it is to AI, on a scale of 0-10"
- **AI replies:** `{"exposure": 8, "rationale": "This job is mostly done on a computer..."}`

### Getting an API key

We use **OpenRouter** — a service that lets you access many different AI models (like Gemini, Claude, GPT) through one API.

1. Go to [openrouter.ai](https://openrouter.ai)
2. Create an account
3. Go to "Keys" and create a new API key
4. Save it in a file called `.env`:

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

> **Why `.env`?** API keys are like passwords. You never want them in your code (which might end up on GitHub for everyone to see). The `.env` file stays on your computer, and `.gitignore` tells git to never upload it.

### The scoring prompt

This is the most important part of the project — the **prompt** tells the AI exactly what we want. A good prompt is like giving clear instructions to a very smart but very literal assistant.

```python
SYSTEM_PROMPT = """
You are an expert analyst evaluating how exposed different occupations are to AI.

Rate the occupation's overall AI Exposure on a scale from 0 to 10.

AI Exposure measures: how much will AI reshape this occupation?

A key signal is whether the job's work product is fundamentally digital.
If the job can be done entirely from a home office on a computer, AI exposure
is inherently high (7+).

Use these anchors to calibrate your score:
- 0-1: Minimal. Physical, hands-on work. Examples: roofer, landscaper.
- 2-3: Low. Mostly physical/interpersonal. Examples: electrician, firefighter.
- 4-5: Moderate. Mix of physical and knowledge work. Examples: nurse, vet.
- 6-7: High. Mostly knowledge work. Examples: teacher, accountant.
- 8-9: Very high. Almost entirely computer-based. Examples: developer, designer.
- 10: Maximum. Routine info processing. Examples: data entry clerk.

Respond with ONLY a JSON object:
{"exposure": <0-10>, "rationale": "<2-3 sentences>"}
"""
```

**Why this works well:**
- **Clear scale** with concrete examples at each level
- **One key heuristic** (digital vs. physical) that's easy to apply consistently
- **Anchoring** — by giving examples, we prevent the AI from clustering all scores in the middle
- **Structured output** — asking for JSON means we can parse it programmatically

### Making the API call

```python
import httpx  # HTTP client (sends messages over the internet)
import json
import os

def score_occupation(client, text, model):
    """Send one occupation to the LLM and get a score back."""

    response = client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},  # The occupation's Markdown
            ],
            "temperature": 0.2,  # Low = more consistent, less random
        },
    )

    # Parse the AI's response
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)  # Convert JSON string → Python dictionary
```

**Key concepts:**
- **`client.post(...)`** — Send a POST request (like submitting a form) to OpenRouter
- **`Authorization: Bearer ...`** — This is how we prove we're allowed to use the API (like showing your ID)
- **`messages`** — The conversation. "system" sets the AI's personality/rules, "user" is our input
- **`temperature: 0.2`** — Controls randomness. 0 = always the same answer. 1 = creative/random. We want consistency, so we use 0.2
- **`json.loads(content)`** — The AI replies with text that *looks like* JSON. This converts it into actual data Python can work with

### Incremental checkpointing

We're making 342 API calls. What if the internet drops after 200? We save after *every single one*:

```python
for i, occ in enumerate(occupations):
    # ... score the occupation ...

    # Save progress after each one
    with open("scores.json", "w") as f:
        json.dump(list(scores.values()), f, indent=2)
```

Next time you run the script, it checks what's already in `scores.json` and skips those. This is called **idempotency** — you can run the script as many times as you want and it'll pick up where it left off.

---

## Chapter 5: Building the Visualization

### What is a treemap?

A **treemap** shows data as nested rectangles. Each rectangle's:
- **Size** = some number (for us: how many people have this job)
- **Color** = another number (for us: AI exposure score)

So big green rectangles = lots of jobs that are safe from AI. Big red rectangles = lots of jobs that are highly exposed.

### Why canvas?

We use the HTML `<canvas>` element — it's like a blank sheet of paper that JavaScript can draw on. We chose canvas over a charting library because:
1. We need custom rendering for 342+ rectangles with labels
2. It's fast (the browser's GPU helps)
3. Zero dependencies — just one HTML file

### The squarified treemap algorithm

This is the trickiest part. We need to pack 342 rectangles into a space so that:
- Each rectangle's area is proportional to its job count
- Rectangles are as close to square as possible (not long thin slivers)

The algorithm works like this:

```
1. Sort items by size (biggest first)
2. Pick a direction (horizontal or vertical — whichever makes the remaining space more square)
3. Lay items in a row along one edge
4. Keep adding items to the row as long as the aspect ratios improve
5. When adding another item would make things worse, start a new row
6. Repeat with the remaining space
```

It's a **greedy** algorithm — at each step it makes the locally best choice. This produces surprisingly good results.

```javascript
function squarify(items, x, y, w, h) {
    // Base case: if only one item, it fills the whole space
    if (items.length === 1) {
        return [{ ...items[0], rx: x, ry: y, rw: w, rh: h }];
    }

    const total = items.reduce((s, d) => s + d.value, 0);
    let remaining = [...items];
    let cx = x, cy = y, cw = w, ch = h;

    while (remaining.length > 0) {
        const vertical = cw >= ch;  // Which direction is longer?

        // Keep adding items to a row while aspect ratios improve
        let row = [remaining[0]];
        for (let i = 1; i < remaining.length; i++) {
            const withNew = [...row, remaining[i]];
            if (worstAspect(withNew) < worstAspect(row)) {
                row = withNew;  // Adding this item improved things
            } else {
                break;  // It got worse — stop here
            }
        }

        // Lay out this row, shrink remaining space, continue
        // ... (position each rectangle in the row)

        remaining = remaining.slice(row.length);
    }
}
```

### Two-level grouping

We actually run the algorithm **twice**:
1. First, group occupations by BLS category (Healthcare, Tech, Education, etc.) and lay those out
2. Then, within each category rectangle, lay out the individual occupations

This gives natural visual grouping without needing borders or labels for categories.

### The color scale

```javascript
function exposureColor(score) {
    const t = score / 10;  // Normalize to 0-1

    // Green (safe) → Orange (moderate) → Red (exposed)
    if (t < 0.5) {
        // Green → Orange
        r = 50 + t * 2 * 180;   // 50 → 230
        g = 160 - t * 2 * 10;   // 160 → 150
        b = 50 - t * 2 * 20;    // 50 → 30
    } else {
        // Orange → Red
        r = 230 + (t - 0.5) * 2 * 25;  // 230 → 255
        g = 150 - (t - 0.5) * 2 * 110; // 150 → 40
        b = 30 - (t - 0.5) * 2 * 10;   // 30 → 20
    }
    return [r, g, b];
}
```

This creates a smooth gradient: 🟢 green → 🟠 orange → 🔴 red.

### Mouse interaction

When the user moves their mouse, we check which rectangle it's over:

```javascript
canvas.addEventListener("mousemove", (e) => {
    // Check every rectangle — is the mouse inside it?
    for (const r of rects) {
        if (mouseX >= r.x && mouseX < r.x + r.width &&
            mouseY >= r.y && mouseY < r.y + r.height) {
            // Found it! Show the tooltip
            showTooltip(r);
            return;
        }
    }
    hideTooltip();
});
```

This is called **hit testing** — checking if a point is inside a rectangle.

### The sidebar

The left sidebar shows aggregate statistics computed from the data:
- Total jobs across all occupations
- Job-weighted average exposure score
- Histogram of jobs by exposure level
- Breakdown by tier (minimal, low, moderate, high, very high)
- Average exposure by pay band and education level
- Total wages in high-exposure jobs

All of this is computed client-side from the same `data.json` file.

---

## Chapter 6: Putting It All Together

### The full pipeline

```bash
# 1. Parse the BLS index to get all occupation URLs
uv run python parse_occupations.py

# 2. Scrape all 342 pages (takes ~10 minutes, runs once)
uv run python scrape.py

# 3. Convert HTML to clean Markdown
uv run python process.py

# 4. Extract structured data to CSV
uv run python make_csv.py

# 5. Score each occupation with AI (~5 minutes, costs ~$0.50)
uv run python score.py

# 6. Build the website data
uv run python build_site_data.py

# 7. View the website!
cd site && python -m http.server 8000
# Open http://localhost:8000 in your browser
```

### How the pieces connect

```
BLS Website
    ↓ scrape.py (Playwright)
html/*.html (342 raw HTML files)
    ↓ process.py + parse_detail.py (BeautifulSoup)
pages/*.md (342 clean Markdown files)
    ↓ make_csv.py (BeautifulSoup + regex)
occupations.csv (structured numbers)

pages/*.md
    ↓ score.py (OpenRouter API → Gemini Flash)
scores.json (342 AI exposure scores + rationales)

occupations.csv + scores.json
    ↓ build_site_data.py
site/data.json (compact merged data)
    ↓
site/index.html (reads data.json, draws treemap)
```

---

## Chapter 7: Key Concepts Glossary

| Concept | What it means | Used where |
|---------|--------------|-----------|
| **Web scraping** | Downloading web pages with code | `scrape.py` |
| **HTML parsing** | Extracting data from web page code | `parse_detail.py` |
| **Markdown** | A simple text format with headers, bold, lists | `pages/*.md` |
| **JSON** | A structured data format (like a spreadsheet for computers) | `occupations.json`, `scores.json` |
| **CSV** | Comma-separated values (literally a spreadsheet) | `occupations.csv` |
| **API** | A way for programs to talk to each other over the internet | `score.py` |
| **LLM** | Large Language Model — AI that understands text (like ChatGPT) | `score.py` |
| **Prompt engineering** | Writing good instructions for an AI | The scoring rubric |
| **Caching** | Saving results so you don't redo work | Every script checks before re-running |
| **Idempotency** | Running something twice gives the same result | `scores.json` checkpointing |
| **Canvas** | An HTML element you can draw on with JavaScript | `site/index.html` |
| **Treemap** | A chart where area = value and color = another value | The main visualization |
| **Hit testing** | Checking if a mouse click/hover is inside a shape | Tooltip on hover |

---

## What's Next?

Now that you understand how the project works, here are features we're building next:

### Feature: "What's Your Job?" Search
Add a search box where someone types their job title, fuzzy-matches to the closest BLS occupation, and sees a personalized breakdown. Shareable via URL.

### Feature: Career Escape Routes
For high-exposure jobs, show the nearest low-exposure occupations with similar education and pay. Help people plan ahead.

### Additional Data Sources to Explore
See `DATA_SOURCES.md` for a curated list of datasets that can enrich this project — skills/tasks data from O*NET, geographic data from BLS, historical automation predictions, and more.
