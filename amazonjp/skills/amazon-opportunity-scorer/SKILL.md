---
name: amazon-opportunity-scorer
description: Score Amazon Japan breakout product opportunities from niche, product, search-term, supplier, and Keepa-style data. Use when Codex needs to rank Amazon JP home, pet, or outdoor niches, find low-competition high-growth products, apply price and margin preferences, or produce a Top N opportunity shortlist with evidence and penalties.
---

# Amazon Opportunity Scorer

Use this skill to rank Amazon Japan product opportunities with a repeatable score. Keep the scoring evidence-based; do not claim a product is "hot" without demand, growth, and competition evidence.

For full launch workflows, preserve `candidate_id` and output enough handoff data for `amazon-risk-auditor`, `amazon-radar-report`, `amazon-jp-launch-gate`, Listing/A+, and Ads.

## Default User Profile

- Market: Amazon Japan.
- Categories: home, pet, outdoor.
- Preference: lightweight and compact.
- Target listing price: USD 20-50 equivalent, default JPY 3,000-7,500.
- Minimum gross margin: 35%.
- Avoid: food, children/baby, medical, electric/battery-powered, liquids.
- Competition preference: Top 10 average review count below 2,000.
- Differentiation preference: material, bundle, accessory, and packaging improvements.

## Workflow

1. Load `references/scoring-model.md`.
2. If CSV files are available, run `scripts/score_opportunities.py`.
3. If data was pasted inline, compute the score manually with the same model.
4. Rank opportunities by `final_score`, then filter out hard-risk categories.
5. For each shortlisted niche, report:
   - `candidate_id`
   - demand and growth evidence
   - competition and concentration
   - price-band fit or bundle-needed note
   - improvement angle
   - risk penalties
   - next validation action
   - launch handoff needs: supplier quote, Keepa/trend check, top competitor ASINs, review-mining target, and candidate keyword seeds

Do not advance directly to Listing/A+ or Ads from scoring. Run `amazon-risk-auditor` and then `amazon-jp-launch-gate` first.

## Script

```bash
python3 scripts/score_opportunities.py --niches niches.csv --products products.csv --search-terms search_terms.csv --output-prefix amazon_jp
```

The script writes:

- `<prefix>.opportunities.csv`
- `<prefix>.opportunities.md`

The CSV includes `candidate_id` when present; otherwise the script generates a deterministic candidate ID from the niche name and top search term.

Use `--target-min-jpy` and `--target-max-jpy` to override the default price band.
