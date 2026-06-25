# Amazon Ads Planner Input Schema

## Product Economics CSV

Accepted columns:

| Canonical field | Source aliases | Required |
|---|---|---|
| `asin` | `ASIN`, `Parent ASIN`, `parent_asin`, `sku` | yes |
| `title` | `Product Title`, `title`, `product_title` | no |
| `price_jpy` | `Price`, `Selling Price`, `Avg Selling Price (360d)`, `price_jpy` | yes |
| `gross_profit_jpy` | `Gross Profit`, `gross_profit_jpy`, `profit_jpy` | one of profit or margin |
| `gross_margin_pct` | `Gross Margin`, `gross_margin_pct`, `margin_pct` | one of profit or margin |
| `daily_budget_jpy` | `Daily Budget`, `daily_budget_jpy`, `budget_jpy` | no |
| `target_acos_pct` | `Target ACOS`, `target_acos_pct` | no |
| `reviews` | `Total Reviews`, `reviews` | no |
| `rating` | `Average Star Rating`, `rating` | no |

## Keyword CSV

Accepted columns:

| Canonical field | Source aliases |
|---|---|
| `keyword` | `Search Term`, `Keyword`, `keyword`, `search_term` |
| `search_volume` | `Search Volume (360d)`, `Search Volume`, `search_volume` |
| `conversion_rate_pct` | `Search Conversion Rate`, `CVR`, `conversion_rate_pct` |
| `relevance` | `Relevance`, `relevance`, `score` |
| `intent` | `Intent`, `intent` |
| `source` | `Source`, `source` |
| `ads_match_type` | `Ads Match Type`, `ads_match_type`, `match_type` |
| `risk` | `Risk`, `risk` |
| `listing_action` | `Listing Action`, `listing_action` |

Relevance can be `high`, `medium`, `low`, or a numeric score from 0-1 or 0-100.

`amazon_keyword_master.csv` from `amazon-jp-listing-aplus-designer` is accepted as the keyword file. Treat `risk=blocked` as an exclusion signal unless the user explicitly overrides it.

## Search-Term Report CSV

Accepted columns:

| Canonical field | Source aliases |
|---|---|
| `launch_id` | `Launch ID`, `launch_id` |
| `sku` | `SKU`, `Advertised SKU`, `sku` |
| `search_term` | `Customer Search Term`, `Search Term`, `search_term` |
| `campaign` | `Campaign Name`, `Campaign`, `campaign` |
| `match_type` | `Match Type`, `match_type` |
| `impressions` | `Impressions`, `impressions` |
| `clicks` | `Clicks`, `clicks` |
| `spend_jpy` | `Spend`, `Cost`, `Spend JPY`, `spend_jpy` |
| `orders` | `Orders`, `7 Day Total Orders (#)`, `orders` |
| `sales_jpy` | `Sales`, `7 Day Total Sales`, `sales_jpy` |
| `acos_pct` | `ACOS`, `Advertising Cost of Sales`, `acos_pct` |

Convert this report into `ads_search_term_feedback.csv` actions for Exact promotion, negatives, bid changes, backend terms, and A+ objection modules.

## Competitor CSV

Accepted columns:

| Canonical field | Source aliases |
|---|---|
| `competitor_asin` | `ASIN`, `Parent ASIN`, `competitor_asin` |
| `title` | `Product Title`, `title` |
| `price_jpy` | `Price`, `Avg Selling Price (360d)`, `price_jpy` |
| `reviews` | `Total Reviews`, `reviews` |
| `rating` | `Average Star Rating`, `rating` |
| `brand` | `Brand`, `brand` |

## Defaults

- Market: Amazon Japan.
- Main ad type: Sponsored Products.
- Minimum daily budget guardrail: JPY 1,000 per active campaign group when possible.
- Default launch daily budget per ASIN: JPY 3,000 if no budget is provided.
- Default target ACOS: `min(0.8 * break_even_acos, 35%)`.
- Launch ranking ACOS can temporarily exceed target, but mark it explicitly as launch spend.
