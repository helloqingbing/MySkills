---
name: amazon-ads-planner
description: Plan Amazon Japan advertising launches from ASIN economics and keyword data. Use when Codex needs to create Sponsored Products campaign structures, daily budgets, CPC bids, keyword match types, product targeting, negative keyword rules, search-term harvesting rules, or a 30-day optimization plan for Amazon JP products.
---

# Amazon Ads Planner

Use this skill to turn ASIN economics and keyword tables into an executable Amazon Japan Sponsored Products launch plan. Prefer file inputs. Inline data can support a draft, but release requires the recorded approval contract.

For full launch workflows, consume `amazon_keyword_master.csv` from `amazon-jp-listing-aplus-designer` and feed search-term report actions back to `amazon-jp-sop-orchestrator`.

## Required Inputs

- ASIN or SKU.
- Approved G6 evidence matrix and landed cost model in the workspace.
- Approved G9 decision and G10 FBA plan.
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
python3 scripts/plan_amazon_ads.py --workspace /path/to/launch --launch-id L1 --products products.csv --keywords amazon_keyword_master.csv --competitors competitors.csv --search-term-report search_terms_report.csv --gate-decision launch_gate.decision.csv --seller-decision seller_central.decision.csv --fba-plan fba.shipment_plan.csv --output-prefix jp_ads
```

4. For inline data, label the result as a draft until approval checks can run.
5. Output:
   - `.campaigns.csv` with one row and one daily budget per campaign
   - `.targets.csv` with target bids and no repeated budget
   - `.negatives.csv` with negative keyword rules
   - campaign structure table
   - per-campaign daily budget
   - per-target starting bid
   - negative keyword rules
   - 30-day optimization plan
   - data gaps and assumptions
   - search-term feedback actions when a report is provided

## Guardrails

- Do not promise profitability. Advertising plans are hypotheses until search-term and order data arrive.
- Recompute price, profit and break-even ACOS from the approved G6 cost model; manual product economics are ignored.
- Separate discovery campaigns from profit/ranking campaigns.
- Keep branded competitor terms and restricted claims conservative.
- For Japan, use Japanese search terms and note localization issues when the keyword list is translated or mixed-language.
- Do not launch ads before `amazon-jp-launch-gate` clears category, claim, IP, economics, and FBA/import blockers.

## Bound approval contract

Install these skills together, preserving the sibling directory layout; scripts share
`amazon-jp-sop-orchestrator/scripts/approval_contract.py` and the Launch Gate validator.
The launch must currently be at `G11`. `--workspace` and `--launch-id` are required.
Downstream scripts verify the matching human-approved gate events and SHA-256 of the
approved files (including referenced local proof snapshots). A same-SKU pass CSV from
another launch or a changed evidence file cannot release this launch. Keep approved
snapshots immutable. Older workspaces without bound approvals require a new audited
launch; copying a historical pass CSV does not migrate approval.
The local workspace is the trust boundary; this is not a signed approval/auth service.

The script also writes `<prefix>.economics.csv`. Include it as G11 evidence when
recording approval. `target_acos_pct` must be positive and at most the approved
break-even ACOS; its default is min(80% of break-even, 35%). G12 reuses this approved
target. Negatives use only `negative exact` / `negative phrase` and reference actual
Auto and Broad discovery campaigns, including when a small budget collapses groups.

G8 approval must include the exact listing CSV and keyword master files consumed by
Seller Central and Ads. A different file, even for the same SKU, requires a new audit.
