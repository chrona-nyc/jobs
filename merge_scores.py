"""
Merge per-model score files into a single scores.json with averaged exposures.

Reads scores_*.json files, averages the exposure scores per occupation, and
picks the rationale from the model closest to the average.

Usage:
    python3 merge_scores.py
"""

import glob
import json


def main():
    files = sorted(glob.glob("scores_*.json"))
    if not files:
        print("No scores_*.json files found")
        return

    print(f"Merging {len(files)} score files:")
    for f in files:
        print(f"  {f}")

    # Load all scores keyed by slug
    by_model = {}
    for path in files:
        tag = path.replace("scores_", "").replace(".json", "")
        with open(path) as f:
            entries = json.load(f)
        by_model[tag] = {e["slug"]: e for e in entries}
        print(f"  {tag}: {len(entries)} occupations")

    # Get all slugs
    all_slugs = set()
    for model_scores in by_model.values():
        all_slugs.update(model_scores.keys())

    merged = []
    models = list(by_model.keys())

    for slug in sorted(all_slugs):
        scores_for_slug = []
        entries_for_slug = []
        for model in models:
            entry = by_model[model].get(slug)
            if entry and "exposure" in entry:
                scores_for_slug.append(entry["exposure"])
                entries_for_slug.append((model, entry))

        if not scores_for_slug:
            continue

        avg = sum(scores_for_slug) / len(scores_for_slug)
        avg_rounded = round(avg)

        # Pick rationale from model closest to the average
        best_entry = min(entries_for_slug, key=lambda x: abs(x[1]["exposure"] - avg))
        base = best_entry[1]

        merged.append({
            "slug": base["slug"],
            "title": base["title"],
            "exposure": avg_rounded,
            "exposure_raw": round(avg, 2),
            "exposure_by_model": {m: by_model[m][slug]["exposure"]
                                  for m in models if slug in by_model[m]},
            "rationale": base["rationale"],
        })

    with open("scores.json", "w") as f:
        json.dump(merged, f, indent=2)

    print(f"\nMerged {len(merged)} occupations into scores.json")

    # Summary
    vals = [e["exposure"] for e in merged]
    avg = sum(vals) / len(vals)
    print(f"Average exposure: {avg:.1f}")

    # Agreement stats
    agreements = 0
    total = 0
    for e in merged:
        by_m = e["exposure_by_model"]
        if len(by_m) >= 2:
            total += 1
            scores = list(by_m.values())
            if max(scores) - min(scores) <= 1:
                agreements += 1
    if total:
        print(f"Model agreement (within ±1): {agreements}/{total} ({agreements/total*100:.0f}%)")

    # Show biggest disagreements
    disagreements = [(e, max(e["exposure_by_model"].values()) - min(e["exposure_by_model"].values()))
                     for e in merged if len(e["exposure_by_model"]) >= 2]
    disagreements.sort(key=lambda x: -x[1])
    if disagreements and disagreements[0][1] > 1:
        print(f"\nBiggest disagreements:")
        for e, diff in disagreements[:10]:
            if diff <= 1:
                break
            scores_str = ", ".join(f"{m}={s}" for m, s in e["exposure_by_model"].items())
            print(f"  {e['title']}: {scores_str} (diff={diff})")


if __name__ == "__main__":
    main()
