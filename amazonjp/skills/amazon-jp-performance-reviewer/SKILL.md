---
name: amazon-jp-performance-reviewer
description: Run Amazon Japan post-launch operating reviews using live sales, traffic, ads, inventory, reviews, returns, and profit metrics. Use whenever Codex needs 7-day, 14-day, 30-day, or weekly Amazon JP launch reviews, action rules, ACOS/TACOS decisions, search-term feedback, listing change recommendations, inventory alerts, or continue/watch/optimize/kill decisions.
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
   - ACOS above break-even for 3+ days: reduce bids or add negatives
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
   - `kill`
4. Feed actions back to Listing/A+, Ads, FBA, Sourcing/QC, and Review Miner.

## Local Script

For CSV-based weekly review, run:

```bash
python3 scripts/review_performance.py \
  --metrics launch_metrics_weekly.csv \
  --search-terms ads_search_term_feedback.csv \
  --inventory inventory.normalized.csv \
  --returns returns.normalized.csv \
  --output-prefix performance
```

The script writes:

- `performance.actions.csv`
- `performance.alerts.csv`
- `performance.weekly_review.md`

## Output

Return:

- launch health summary
- decision and reason
- metric-driven actions by owner
- search-term promote/negate actions
- listing, A+, inventory, QC, or ad feedback loops
- next 7-day review plan
