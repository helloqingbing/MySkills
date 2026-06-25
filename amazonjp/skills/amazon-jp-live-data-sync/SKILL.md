---
name: amazon-jp-live-data-sync
description: Normalize live Amazon Japan operating reports into canonical launch artifacts. Use whenever Codex needs to ingest Seller Central exports, Brand Analytics, Search Query Performance, Business Reports, Search Term Reports, inventory, FBA fee, return, review, or policy-change notes so Amazon JP launch skills can work from fresh weekly or daily data instead of static research snapshots.
---

# Amazon JP Live Data Sync

## Overview

Use this skill to turn fresh Amazon.co.jp operating exports into stable CSV artifacts that the Amazon JP workflow can reuse. This skill does not scrape Seller Central or bypass platform access. It expects user-provided exports, screenshots summarized as tables, or pasted CSV snippets.

For full workflows, feed outputs to `amazon-jp-sop-orchestrator`, `amazon-ads-planner`, `amazon-jp-performance-reviewer`, and `amazon-jp-launch-gate`.

## Accepted Inputs

- Brand Analytics / Search Query Performance reports.
- Business Reports with sessions, unit session percentage, orders, and sales.
- Sponsored Products Search Term Reports.
- Manage Inventory or FBA Inventory reports.
- FBA fee, referral fee, return, refund, and customer review exports.
- Seller Central policy or category-change notes, when provided by the user.

## Workflow

1. Identify the report type and date range.
2. Preserve `launch_id`, `sku`, `parent_asin`, `child_asin`, and `candidate_id` when present.
3. Normalize money to JPY numeric fields and percentages to numeric percent fields.
4. Do not invent missing operating metrics. Leave blanks and record the gap in `live_data_quality_note.md`.
5. Classify each output row as one of:
   - `keyword_signal`
   - `traffic_conversion`
   - `ad_search_term`
   - `inventory_signal`
   - `fee_margin_signal`
   - `review_return_signal`
   - `policy_signal`
6. Surface alerts when data suggests immediate action:
   - inventory under 21 days of supply
   - ACOS above break-even
   - CVR down materially versus prior period
   - rating below 4.2
   - returns or refund reasons rising
   - required policy evidence missing

## Local Script

For CSV exports, run:

```bash
python3 scripts/normalize_live_reports.py \
  --business business_report.csv \
  --search-terms search_term_report.csv \
  --inventory inventory_report.csv \
  --returns returns.csv \
  --reviews reviews.csv \
  --output-dir live_data
```

The script writes:

- `business_metrics.normalized.csv`
- `ads_search_terms.normalized.csv`
- `inventory.normalized.csv`
- `returns.normalized.csv`
- `reviews.normalized.csv`
- `live_data_quality_note.md`

## Output

Return:

- normalized artifact table with paths
- date range and freshness note
- missing fields that block decision-making
- alerts that should feed `amazon-jp-performance-reviewer`
- next import action
