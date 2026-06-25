---
name: amazon-data-ingestor
description: Normalize Amazon Japan product research exports for niche discovery. Use when Codex needs to parse Product Opportunity Explorer-style niche tables, product ASIN detail tables, search-term tables, supplier quotes, or pasted CSV snippets into stable canonical fields before scoring Amazon JP home, pet, or outdoor opportunities.
---

# Amazon Data Ingestor

Use this skill to clean Amazon Japan product research data before analysis. Prefer provided CSV files. If the user pastes table snippets inline, parse them as CSV-like source data and preserve original evidence.

When this is part of a full launch workflow, preserve or create a stable `candidate_id` so outputs can join to `amazon-jp-sop-orchestrator`, `amazon-jp-launch-gate`, Listing/A+, and Ads artifacts.

## Workflow

1. Identify input table types:
   - niche overview: `Niche Name`, search volume, growth, units sold, brand share, review count
   - product detail: `Parent ASIN`, title, brand, category path, price, reviews, BSR, click share
   - search terms: `Search Term`, search volume, conversion rate, top clicked ASINs
   - supplier quotes: supplier price, MOQ, shipping, package size, lead time
   - Keepa/trend notes: ASIN, price history, BSR trend, stockout/seasonality notes
   - ad search-term reports: search term, clicks, spend, orders, sales, ACOS
2. Read `references/schema.md` before mapping unfamiliar columns.
3. Normalize values:
   - JPY prices like `￥1689` to integer yen.
   - Percent strings like `18.6%` to decimal percent numbers such as `18.6`.
   - Japanese text as UTF-8, preserving ASINs and search terms exactly.
4. Preserve identifiers:
   - Keep provided `candidate_id`, `sku`, `parent_asin`, and `launch_id`.
   - If `candidate_id` is missing, create a deterministic ID from niche/search term/product name.
5. Do not invent missing metrics. Leave unknown values blank and mark assumptions.
6. Output normalized tables plus a short data-quality note:
   - missing columns
   - suspicious units or malformed percentages
   - whether price is in JPY or another currency
   - whether product rows can be joined to niches through top search terms or clicked ASINs
   - whether supplier/cost data is sufficient for `amazon-jp-launch-gate`

## Local Script

For file-based CSV normalization, run:

```bash
python3 scripts/normalize_amazon_jp.py --niches "Niche List 细分市场概览.csv" --products "Products 商品 ASIN 明细表.csv" --search-terms "Search Terms 关键词搜索词表.csv" --supplier-quotes suppliers.csv --output-dir normalized
```

Use the script when paths are available. For inline pasted snippets, normalize manually using the same schema.
