---
name: amazon-ads-planner
description: Plan Amazon Japan advertising launches from ASIN economics and keyword data. Use when Codex needs to create Sponsored Products campaign structures, daily budgets, CPC bids, keyword match types, product targeting, negative keyword rules, search-term harvesting rules, or a 30-day optimization plan for Amazon JP products.
---

# Amazon Ads Planner

Use this skill to turn ASIN economics and keyword tables into an executable Amazon Japan Sponsored Products launch plan. Prefer file inputs. If the user pastes ASIN, price, margin, and keyword tables inline, produce the same outputs manually.

For full launch workflows, consume `amazon_keyword_master.csv` from `amazon-jp-listing-aplus-designer` and feed search-term report actions back to `amazon-jp-sop-orchestrator`.

## Required Inputs

- ASIN or SKU.
- Selling price in JPY.
- Gross profit JPY or gross margin percent.
- Keyword table with Japanese search terms.

Optional inputs:

- daily budget
- target ACOS
- competitor ASINs
- search volume
- search conversion rate
- keyword relevance
- existing search-term report
- `amazon_keyword_master.csv`

## Workflow

1. Read `references/input-schema.md` for accepted columns.
2. Read `references/planning-rules.md` for budget, bid, campaign, and negative rules.
3. If CSV files are available, run:

```bash
python3 scripts/plan_amazon_ads.py --products products.csv --keywords amazon_keyword_master.csv --competitors competitors.csv --search-term-report search_terms_report.csv --output-prefix jp_ads
```

4. If only inline data is available, apply the same formulas manually.
5. Output:
   - campaign structure table
   - per-campaign daily budget
   - per-target starting bid
   - negative keyword rules
   - 30-day optimization plan
   - data gaps and assumptions
   - search-term feedback actions when a report is provided

## Guardrails

- Do not promise profitability. Advertising plans are hypotheses until search-term and order data arrive.
- Always compute or estimate break-even ACOS from product economics.
- Separate discovery campaigns from profit/ranking campaigns.
- Keep branded competitor terms and restricted claims conservative.
- For Japan, use Japanese search terms and note localization issues when the keyword list is translated or mixed-language.
- Do not launch ads before `amazon-jp-launch-gate` clears category, claim, IP, economics, and FBA/import blockers.
