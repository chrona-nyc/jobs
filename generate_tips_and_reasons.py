"""
Generate personalized prepare tips and BLS path skill-transfer reasons.

For each occupation with exposure >= 4:
1. Role-specific "how to prepare" tips (not generic tier advice)
2. Skill-transfer reasons for each BLS-similar path (replacing "Related role")

Uses Gemini Flash for speed/cost.

Usage:
    python3 generate_tips_and_reasons.py
"""

import json
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

MODEL = "google/gemini-3-flash-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_for_occupation(client, job, bls_targets):
    """Generate tips and BLS path reasons for one occupation."""
    targets_block = ""
    if bls_targets:
        lines = []
        for t in bls_targets:
            lines.append(f"- {t['title']} (slug: {t['slug']}, exposure: {t['exposure']}/10, pay: ${t.get('pay','?'):,})")
        targets_block = f"""
BLS-SIMILAR OCCUPATIONS WITH LOWER AI EXPOSURE (need skill-transfer reasons):
{chr(10).join(lines)}

For each BLS-similar occupation above, write a brief skill-transfer reason (5-10 words)
explaining WHY someone in {job['title']} could transition to that role.
Focus on the specific transferable skill, NOT generic phrases like "related role" or "skills transfer".
Good: "Applies financial analysis to insurance risk assessment"
Bad: "Related role" or "Similar skills transfer"
"""

    prompt = f"""You are a career advisor. Given this occupation, generate two things.

OCCUPATION:
- Title: {job['title']}
- AI Exposure: {job['exposure']}/10
- Category: {job.get('category', '')}
- Education: {job.get('education', '')}
- Median Pay: {('$' + f"{job['pay']:,}") if job.get('pay') else 'unknown'}

TASK 1: Write 3-4 specific, actionable "how to prepare for AI" tips for someone in THIS role.
- Be specific to the occupation (mention tools, skills, or strategies relevant to THIS job)
- Don't be generic ("learn AI tools") — say WHICH tools or WHAT specifically
- Each tip should be 1 sentence, practical, and immediately actionable
- Consider the exposure level: higher exposure = more urgent/pivotal advice
{targets_block}
Respond with ONLY JSON, no other text:
{{
  "tips": ["tip1", "tip2", "tip3"],
  "bls_reasons": {{"slug": "5-10 word reason", ...}}
}}

If there are no BLS targets, omit bls_reasons or use empty object."""

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

    # Find all occupations needing tips (exposure >= 4)
    needs_work = []
    for d in data:
        if d.get("exposure") is None or d["exposure"] < 4:
            continue

        # Find BLS-similar targets with -2 gap
        bls_targets = []
        for s in d.get("similar", []):
            t = by_slug.get(s)
            if t and t.get("exposure") is not None and t["exposure"] <= d["exposure"] - 2:
                bls_targets.append(t)

        needs_work.append((d, bls_targets))

    print(f"Found {len(needs_work)} occupations needing tips/reasons")

    # Load existing results
    results = {}
    if os.path.exists("tips_and_reasons.json"):
        with open("tips_and_reasons.json") as f:
            results = json.load(f)
        print(f"Already have results for {len(results)} occupations")

    client = httpx.Client()
    errors = []

    for i, (job, bls_targets) in enumerate(needs_work):
        if job["slug"] in results:
            continue

        print(f"  [{i+1}/{len(needs_work)}] {job['title']} ({job['exposure']}/10, {len(bls_targets)} BLS targets)...", end=" ", flush=True)

        try:
            result = generate_for_occupation(client, job, bls_targets)

            # Validate
            tips = result.get("tips", [])
            bls_reasons = result.get("bls_reasons", {})

            # Only keep reasons for valid slugs
            valid_reasons = {}
            for slug, reason in bls_reasons.items():
                if slug in by_slug:
                    valid_reasons[slug] = reason

            results[job["slug"]] = {
                "tips": tips[:4],
                "bls_reasons": valid_reasons,
            }
            print(f"{len(tips)} tips, {len(valid_reasons)} reasons")

        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(job["slug"])

        with open("tips_and_reasons.json", "w") as f:
            json.dump(results, f, indent=2)

        time.sleep(0.3)

    client.close()

    print(f"\nDone. {len(results)} occupations, {len(errors)} errors.")
    tip_counts = [len(v["tips"]) for v in results.values()]
    reason_counts = [len(v["bls_reasons"]) for v in results.values()]
    if tip_counts:
        print(f"Avg tips: {sum(tip_counts)/len(tip_counts):.1f}")
        print(f"Avg BLS reasons: {sum(reason_counts)/len(reason_counts):.1f}")


if __name__ == "__main__":
    main()
