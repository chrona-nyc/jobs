# Roadmap

## In Progress

### "What's Your Job?" Search Mode
Add a search box where users type their job title, fuzzy-match to the closest BLS occupation, and show a personalized exposure breakdown card. Shareable as a URL (`?job=software-developers`).

### Career Escape Routes
For high-exposure jobs (7+), show the nearest low-exposure occupations that share similar education/pay levels. "You're a paralegal (8/10)? Consider: compliance officer (6/10), same education, +12% pay."

## Future Ideas

- **Search/filter bar** — Type to highlight matching occupations in the treemap
- **Click-to-zoom** — Click a category to zoom in
- **Multi-model consensus** — Score with Claude, GPT-4o, Gemini; show agreement
- **Task-level decomposition** — Score individual duties, not just whole jobs (needs O*NET)
- **Geographic heat map** — AI exposure by state/metro area (needs BLS OEWS data)
- **Wage impact simulator** — "What if AI replaces X% of high-exposure work?"
- **Historical comparison** — Compare with Frey & Osborne 2013 predictions
- **Embedding space** — UMAP scatter plot showing occupation similarity clusters
