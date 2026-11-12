---
name: amazon-jp-performance-reviewer
description: Run Amazon Japan post-launch operating reviews using live sales, traffic, ads, inventory, reviews, returns, and profit metrics. Use whenever Codex needs 7-day, 14-day, 30-day, or weekly Amazon JP launch reviews, action rules, ACOS/TACOS decisions, search-term feedback, listing change recommendations, inventory alerts, or scale/watch/optimize/pause decisions.
---

# Amazon JP Performance Reviewer

## Overview

Use this skill after launch and then weekly. It converts live metrics from `amazon-jp-live-data-sync`, ad outputs from `amazon-ads-planner`, and inventory data from `amazon-jp-fba-shipment-planner` into concrete operating decisions.

The reviewer should not produce vague advice. Every recommendation needs a metric, threshold, owner action, and next review date.

## Intake

Collect:

- Launch ID, SKU, ASIN, launch date, week start.
- Sessions, unit session percentage, orders, sales, price, Buy Box notes.
- Ad spend, ACOS, TACOS, impressions, clicks, CPC, CTR, CVR.
- Search term report with customer search term, spend, orders, sales.
- Inventory days of supply, inbound quantity, stockout date, replenishment plan.
- Rating, reviews, return/refund count, return reasons.
- Break-even ACOS and gross margin from `landed_cost_model.csv`.

## Workflow

1. Compute metric health by period:
   - traffic
   - conversion
   - ad efficiency
   - profit
   - inventory
   - review/return quality
2. Apply operating rules:
   - Weekly ACOS above approved target or break-even: reduce bids or add negatives
   - spend with no orders after threshold: negate or reduce bid
   - high CTR and low CVR: review price, image, reviews, or offer
   - low CTR and high impressions: update main image/title angle
   - inventory under 21 days: trigger replenishment
   - rating below 4.2: pause scale and run review mining
   - TACOS improving with stable inventory: scale carefully
3. Return one decision:
   - `scale`
   - `optimize`
   - `watch`
   - `needs_proof`
   - `pause`
4. Feed actions back to Listing/A+, Ads, FBA, Sourcing/QC, and Review Miner.

## Local Script

For CSV-based weekly review, run:

```bash
python3 scripts/review_performance.py --workspace /path/to/launch --launch-id L1 \
  --metrics launch_metrics_weekly.csv \
  --report-manifest report_manifest.csv \
  --output-prefix performance
```

The script writes:

- `performance.actions.csv`
- `performance.decisions.csv` (one decision per SKU)
- `performance.alerts.csv`
- `performance.weekly_review.md`
- `performance.verified_metrics.csv` (values recomputed from verified report files)

`--metrics` supplies one row per SKU with `launch_id`, `sku`, `week_start`.
Economics are recomputed from approved G6 costs and the approved G11
`<prefix>.economics.csv` target. Manual margin/target and operating values are ignored: sessions, orders, sales, ad spend, ACOS/TACOS, conversion, returns, review
rating and inventory coverage are recomputed from the manifest's normalized files.
Business metrics require one aggregate row per SKU. Days of supply uses sellable
inventory divided by average daily units ordered during the seven-day review.
Rating is the mean of ratings in the review report for the matching SKU or ASIN;
ASIN-only reviews require an ASIN association in business or inventory data.
Zero reviews leave rating unverified and prevent scale.

Business, ad search-term, returns and reviews reports must cover exactly
`week_start` through `week_start + 6 days`; inventory must be a snapshot ending on
that last day, before today. Review and return event dates must fall within the
declared period. Future export dates and incomplete or mismatched periods prevent
scale. The optional `--search-terms`, `--inventory` and `--returns` arguments, when
used, must identify the exact normalized files in the manifest.

## Output

Return:

- launch health summary
- decision and reason
- metric-driven actions by owner
- search-term promote/negate actions
- listing, A+, inventory, QC, or ad feedback loops
- next 7-day review plan

## Bound approval contract

Install these skills together, preserving the sibling directory layout; scripts share
`amazon-jp-sop-orchestrator/scripts/approval_contract.py` and the Launch Gate validator.
The launch must currently be at `G12`. `--workspace` and `--launch-id` are required.
Downstream scripts verify the matching human-approved gate events and SHA-256 of the
approved files (including referenced local proof snapshots). A same-SKU pass CSV from
another launch or a changed evidence file cannot release this launch. Keep approved
snapshots immutable. Older workspaces without bound approvals require a new audited
launch; copying a historical pass CSV does not migrate approval.
The local workspace is the trust boundary; this is not a signed approval/auth service.

`decisions.csv` separates the business `decision` (scale/optimize/watch/pause/needs_proof)
from `gate_decision` (pass/needs_proof), and includes `gate=G12`, `week_start` and
`review_id=launch_id:sku:week_start`. A complete pause review can pass G12 without
permitting growth. `promote_exact` uses the approved target and is emitted only for a
SKU whose overall decision is scale. Record the decisions CSV directly for G12.
A passed review retains `current_gate=G12`, `lifecycle_state=optimizing`; subsequent
approved weeks must be later and non-overlapping. Identical immediate retries are
idempotent. Archive each week's files in its own directory before starting the next.
