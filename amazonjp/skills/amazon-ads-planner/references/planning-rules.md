# Amazon Japan Sponsored Products Planning Rules

## Campaign Structure

Create four campaign groups for each ASIN:

| Group | Targeting | Purpose | Default budget share |
|---|---|---|---:|
| Discovery Auto | Auto | Mine search terms and ASIN placements | 30% |
| Discovery Broad | Manual keyword broad | Expand long-tail keyword coverage | 20% |
| Profit Exact | Manual keyword exact | Bid on high-relevance purchase-intent terms | 35% |
| Product Targeting | Manual product targeting | Attack competitor detail pages | 15% |

For very small budgets below JPY 2,000/day, collapse into Auto + Exact only.

## Bid Formula

Use target CPC:

```text
target_cpc = price_jpy * target_acos * expected_conversion_rate
```

Where:

- `target_acos` is decimal, e.g. `0.28`.
- `expected_conversion_rate` is decimal, e.g. `0.07`.
- Use keyword conversion rate when present.
- Defaults: exact `7%`, broad `4.5%`, auto `5%`, product targeting `5.5%`.

Apply bid guardrails:

- Minimum bid: JPY 25.
- Maximum starting bid: JPY 150 unless user provides category CPC data.
- Broad bid should usually be 70-85% of exact bid.
- Auto bid should usually be 75-90% of exact bid.
- Product targeting bid should be 70-100% of exact bid depending on competitor weakness.

## Keyword Selection

Exact:

- high relevance
- direct product terms
- clear use case terms
- conversion rate present or inferred high

Broad:

- medium/high relevance
- modifier terms
- discovery terms with enough search volume

Negative candidates:

- competitor brand names unless intentionally targeting competitor brands
- irrelevant use cases
- forbidden product attributes: food, baby/children, medical, electric/battery, liquids
- materials/features the product does not have
- low-intent informational terms

Use keyword intent when available:

| Intent | Default action |
|---|---|
| `category` | exact if high relevance; broad if medium |
| `attribute` | broad or exact depending on relevance |
| `use_case` | broad discovery, promote to exact after conversion |
| `pain` | broad discovery and A+ objection module candidate |
| `spec` | exact when product exactly matches |
| `info` | watch or negative if low purchase intent |
| `competitor` | product targeting or blocked unless approved |

## Optimization Thresholds

Review every 3-5 days during launch.

Promote to exact:

- search term has at least 1 order and ACOS is acceptable, or
- search term has strong CTR/CVR signal and is strategically important.

Reduce bid:

- spend exceeds 0.7x gross profit with no order.
- ACOS is above target after at least 2 orders.

Pause or negate:

- spend exceeds 1.0x gross profit with no order.
- 15+ clicks and no order, unless ranking campaign deliberately allows it.
- clearly irrelevant term.

Scale:

- 2+ orders and ACOS below target: raise bid 10-20%.
- exact keyword has stable ACOS below target for 7 days: increase campaign budget 20-30%.

## 30-Day Launch Phases

Days 1-7:

- Launch Auto, Broad, Exact, and Product campaigns.
- Keep bids controlled; avoid overreacting before clicks accumulate.
- Fix listing if CTR is weak.

Days 8-14:

- Pull search-term report.
- Promote converting queries to Exact.
- Add obvious irrelevant negatives.
- Lower bids on spend-without-order targets.

Days 15-21:

- Split winners into profit campaign.
- Increase exact bids on high-converting terms.
- Add product targets where competitor listings have weaker price, rating, image, or bundle.

Days 22-30:

- Separate discovery budget from profit budget.
- Add ranking campaign only for 3-5 strategic terms.
- Evaluate TACOS, organic rank movement, and whether launch spend is creating natural sales.

## Search-Term Feedback Actions

For each search-term report row:

| Condition | Action |
|---|---|
| 1+ orders and ACOS at or below target | `promote_exact` |
| 2+ orders and ACOS below target for 7 days | `increase_bid` |
| spend > 1.0x gross profit and 0 orders | `negate` |
| 15+ clicks and 0 orders | `negate` or `reduce_bid` |
| high CTR but low CVR | `listing_action` for image/title/price/offer check |
| repeated buyer objection term | `add_a_plus` FAQ or proof module |
| relevant term not in visible copy | `add_backend` or Listing revision candidate |
