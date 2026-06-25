---
name: amazon-radar-report
description: Create Amazon Japan product-opportunity radar reports from scored niches, ASIN details, search-term data, review insights, and risk audits. Use when Codex needs to produce a concise weekly or monthly Amazon JP breakout-product report with rankings, evidence, risks, differentiation ideas, and next validation actions.
---

# Amazon Radar Report

Use this skill after scoring and risk screening. The report should be concise, evidence-first, and action-oriented.

## Workflow

1. Read `references/report-template.md`.
2. Group candidates into:
   - immediate validation
   - watchlist
   - reject / do not touch
3. For each candidate, include metrics and the reason it survived filters.
4. Call out underpriced-but-bundleable products separately.
5. End with a 7-day validation plan:
   - supplier quote
   - review mining
   - Keepa trend check
   - sample purchase
   - FBA fee and landed-cost estimate
   - launch gate evidence collection

6. For full launch workflows, also output a launch handoff package with:
   - `candidate_id`
   - target niche and top search terms
   - competitor ASINs for reviews and product targeting
   - risk decision and unresolved controls
   - required supplier quote and sample tests
   - claim proof list
   - keyword seeds for `amazon_keyword_master.csv`

Do not fill the report with generic Amazon advice. Every recommendation needs evidence from the input data.
