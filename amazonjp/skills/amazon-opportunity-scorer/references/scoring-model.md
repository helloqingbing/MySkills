# Amazon Japan Opportunity Scoring Model

## Score Dimensions

Final score is 0-100 before hard-risk exclusion.

| Dimension | Weight | Evidence |
|---|---:|---|
| Demand | 20 | 360-day search volume and units sold |
| Growth | 25 | YoY and QoQ search-volume growth |
| Competition | 15 | average reviews, brand concentration, Amazon Basics presence |
| Price and margin fit | 15 | JPY target band and ability to bundle up |
| Improvement headroom | 15 | rating gap, search-term modifiers, product variation signals |
| Supply and launch fit | 10 | lightweight inference, new ASIN count, category fit |

## Risk Penalties

Subtract penalties after dimension scoring:

- Amazon Basics in top products: `-8`
- Top 5 brand click share >= 65%: `-5`
- Top 20 brand click share >= 85%: `-4`
- Average review count >= 2,000: `-8`
- Average review count >= 5,000: additional `-6`
- Avoided category or keyword: hard reject
- Electric/battery, liquid, food, medical, baby/children: hard reject unless the user explicitly overrides

## Price Handling

Default target price is JPY 3,000-7,500. If a niche is below JPY 3,000 but is small, consumable-like, or naturally sold as a set, mark `bundle_needed` and score partial price fit instead of rejecting it.

## Output Labels

- `A`: final score >= 75 and no hard risk.
- `B`: final score 60-74, worth manual validation.
- `C`: final score 45-59, keep for watchlist.
- `Reject`: hard risk or final score below 45.

## Launch Handoff Fields

Every shortlisted row should preserve:

| Field | Purpose |
|---|---|
| `candidate_id` | Join key for risk, validation, launch gate, Listing, Ads |
| `niche_name` | Opportunity name |
| `top_search_term` | Primary keyword seed |
| `parent_asin_targets` | Top competitor ASINs for review mining and product targeting |
| `review_mining_needed` | yes/no |
| `supplier_quote_needed` | yes/no |
| `keepa_check_needed` | yes/no |
| `launch_gate_required` | yes |

## Required Evidence Standard

Every recommendation must cite at least two concrete metrics, such as search volume + YoY growth, or units sold + review count. If evidence is thin, mark `needs_more_data`.
