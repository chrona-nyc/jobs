"""
Generate AI-powered career transition suggestions for stuck occupations.

For jobs where BLS similar occupations don't offer meaningful exposure drops,
ask an LLM to suggest realistic career transitions from our dataset.

Usage:
    python3 generate_paths.py
"""

import json
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

MODEL = "google/gemini-3-flash-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_occupation_index(data):
    """Build a compact index of all occupations for the LLM context."""
    lines = []
    for d in sorted(data, key=lambda x: x.get("exposure") or 0):
        if d.get("exposure") is None:
            continue
        lines.append(f"{d['slug']}|{d['exposure']}|{d['title']}|{d.get('category','')}|{d.get('education','')}")
    return "\n".join(lines)


def generate_transitions(client, job, occupation_index):
    """Ask LLM for career transition suggestions."""
    prompt = f"""You are a career transition advisor. Given a source occupation and a list of all occupations in our dataset, suggest 5-8 realistic career transitions where the person's skills would transfer.

SOURCE OCCUPATION:
- Title: {job['title']}
- AI Exposure: {job['exposure']}/10
- Category: {job.get('category', '')}
- Education: {job.get('education', '')}
- Median Pay: ${job.get('pay', 'unknown'):,}

RULES:
1. Only suggest occupations from the dataset below (use exact slugs)
2. Target occupations with LOWER AI exposure (at least 2 points lower)
3. Skills must realistically transfer — explain the connection in 5-10 words
4. Prefer occupations where education requirements are similar or lower
5. Consider both obvious lateral moves AND creative cross-domain pivots
6. A data scientist could become a postsecondary teacher, a management analyst could become a construction manager, etc.

ALL OCCUPATIONS (slug|exposure|title|category|education):
{occupation_index}

Respond with ONLY a JSON array, no other text:
[
  {{"slug": "exact-slug", "reason": "brief skill transfer explanation"}},
  ...
]"""

    response = client.post(
        API_URL,
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=120,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def main():
    with open("site/data.json") as f:
        data = json.load(f)
    by_slug = {d["slug"]: d for d in data}

    occupation_index = build_occupation_index(data)

    # Find stuck jobs: exposure >= 4, no BLS-similar with -2 gap,
    # and no same-category with -2 gap and high enough score
    stuck = []
    for d in data:
        if d.get("exposure") is None or d["exposure"] < 5:
            continue
        similar = set(d.get("similar", []))
        has_bls_path = any(
            by_slug[s]["exposure"] <= d["exposure"] - 2
            for s in similar
            if s in by_slug and by_slug[s].get("exposure") is not None
        )
        if not has_bls_path:
            stuck.append(d)

    print(f"Found {len(stuck)} stuck occupations (exposure >= 5, no BLS path with -2 gap)")

    # Load existing AI paths
    ai_paths = {}
    if os.path.exists("ai_paths.json"):
        with open("ai_paths.json") as f:
            ai_paths = json.load(f)
        print(f"Already have AI paths for {len(ai_paths)} occupations")

    client = httpx.Client()
    errors = []
    valid_slugs = set(by_slug.keys())

    for i, job in enumerate(stuck):
        if job["slug"] in ai_paths:
            continue

        print(f"  [{i+1}/{len(stuck)}] {job['title']} ({job['exposure']}/10)...", end=" ", flush=True)

        try:
            suggestions = generate_transitions(client, job, occupation_index)
            # Validate slugs and exposure requirement
            valid = []
            for s in suggestions:
                slug = s.get("slug", "")
                target = by_slug.get(slug)
                if target and target.get("exposure") is not None and target["exposure"] <= job["exposure"] - 2:
                    valid.append({"slug": slug, "reason": s.get("reason", "")})

            ai_paths[job["slug"]] = valid
            print(f"{len(valid)} paths")

        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(job["slug"])

        with open("ai_paths.json", "w") as f:
            json.dump(ai_paths, f, indent=2)

        time.sleep(0.3)

    client.close()

    print(f"\nDone. Generated paths for {len(ai_paths)} occupations, {len(errors)} errors.")

    # Summary
    counts = [len(v) for v in ai_paths.values()]
    if counts:
        print(f"Average paths per occupation: {sum(counts)/len(counts):.1f}")
        print(f"Occupations with 0 paths: {sum(1 for c in counts if c == 0)}")


if __name__ == "__main__":
    main()
