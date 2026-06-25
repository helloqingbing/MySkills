# Amazon Japan Product Radar Report Template

## Executive Summary

- Market:
- Data sources:
- Shortlist count:
- Best opportunity:
- Biggest risk:

## Top Opportunities

| Rank | Niche | Score | Why now | Competition | Price fit | Risk | Next action |
|---:|---|---:|---|---|---|---|---|

## Candidate Detail

For each candidate:

```text
Niche:
Score:
Evidence:
- Search volume:
- YoY / QoQ growth:
- Units sold:
- Avg review count:
- Brand concentration:
Differentiation:
- Material:
- Bundle:
- Accessory:
- Packaging:
Risk:
- ...
Next validation:
- ...
```

## Watchlist

Candidates with some evidence but missing data or borderline competition.

## Reject List

Rejected products with explicit reasons, especially hard user-preference violations.

## 7-Day Validation Plan

1. Pull Keepa history for top ASINs.
2. Export 1-3 star reviews for the top 5-10 ASINs.
3. Request supplier quotes and MOQ from 1688/Alibaba.
4. Estimate landed cost, FBA fee, and gross margin.
5. Check trademarks, design patents, and brand dependency.
6. Buy 2-3 competitor samples.
7. Decide: test order / watch / reject.

## Launch Handoff Package

Create this table for candidates that survive the radar review:

| candidate_id | niche_name | top_search_term | competitor_asins | risk_decision | supplier_quote_needed | keepa_needed | review_mining_needed | launch_gate_controls | next_action |
|---|---|---|---|---|---|---|---|---|---|

Also include:

- `claim_proof_needed`: claims that need test reports/specs before Listing/A+.
- `keyword_seed_list`: terms to start `amazon_keyword_master.csv`.
- `product_requirement_seed`: expected must-fix issues from reviews or competitor gaps.
- `ads_seed_targets`: exact keyword candidates and ASIN targeting candidates.
