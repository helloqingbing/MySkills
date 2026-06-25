# Amazon JP Launch Artifact Contracts

Use these contracts to connect the Amazon JP skills into one executable workflow.

## Directory Layout

```text
raw_exports/
live_data/
normalized/
analysis/
validation/
sourcing/
launch_gate/
product/
listing/
seller_central/
fba/
ads/
operations/
archive/
```

## Universal IDs

Every structured artifact should include as many of these as possible:

| Field | Meaning | Required from |
|---|---|---|
| `candidate_id` | Stable research opportunity ID | G0 onward |
| `niche_name` | Product opportunity or niche | G0-G4 |
| `top_search_term` | Primary demand term | G0-G4 |
| `sku` | Seller SKU | G4 onward |
| `parent_asin` | Parent ASIN when known | G6 onward |
| `child_asin` | Child ASIN when known | G6 onward |
| `launch_id` | One launch attempt | G4 onward |
| `decision` | pass/watch/reject/blocked/needs_proof | every gate |
| `blocking_reason` | Reason if not pass | every gate |
| `owner` | Human or team responsible | every gate |
| `next_action` | Next concrete action | every gate |

## Gate Artifacts

| Gate | Required input | Required output | Pass condition |
|---|---|---|---|
| G0 live data sync | Seller Central / Ads exports | `live_data/*.normalized.csv`, `live_data_quality_note.md` | date range and field gaps visible |
| G1 data quality | raw exports | `normalized/*.csv`, `data_quality_note.md` | IDs and join fields present |
| G2 opportunity | normalized data | `opportunities.csv`, `opportunities.md` | label A/B or override |
| G3 risk | opportunities | `risk_audit.csv` or risk table | no hard reject |
| G4 sourcing/QC | supplier quotes, review pain | `supplier_scorecard.csv`, `qc_checklist.csv`, `sample_review.md` | supplier/sample/QC proof is usable |
| G5 validation | shortlist | `validation_evidence.md`, supplier quote, Keepa/trend notes | supplier, sample, and economics can be tested |
| G6 launch gate | validation pack | `evidence_matrix.csv`, `landed_cost_model.csv`, `launch_gate_report.md` | no blocked controls, margin acceptable |
| G7 product definition | reviews, sample notes | `product_requirements.csv` | must-fix and claims proof defined |
| G8 listing | product requirements, keyword master | `listing_package.md`, `claim_ledger.csv` | copy and claims are proof-backed |
| G9 Seller Central | listing package, evidence | `seller_central.checklist.csv`, `seller_central.ops_log.csv` | required upload fields and proof ready |
| G10 FBA | package specs, inventory | `fba.shipment_plan.csv`, `fba.replenishment_alerts.csv` | labels, box specs, and inventory risk clear |
| G11 ads | economics, keyword master | `ads_campaigns.csv`, `ads_negatives.csv`, `30_day_plan.md` | break-even ACOS and budget visible |
| G12 performance | ad/search/order/inventory data | `performance.actions.csv`, `performance.alerts.csv`, `launch_metrics_weekly.csv` | actions feed back to ads/listing/product/FBA/QC |

## `amazon_keyword_master.csv`

| Field | Notes |
|---|---|
| `candidate_id` | Required |
| `sku` | Required once known |
| `keyword` | Japanese search term |
| `jp_variant` | kana/kanji/katakana/English variant |
| `priority` | primary/secondary/long_tail/backend_only/negative |
| `intent` | category/attribute/use_case/pain/spec/material/audience/season/info/competitor |
| `placement` | title/bullet/description/a_plus/backend/ads_only/negative |
| `source` | POE/SQP/review/ad_report/manual |
| `search_volume_360d` | numeric when available |
| `conversion_rate_pct` | numeric when available |
| `relevance` | high/medium/low or 0-1 |
| `evidence` | metric, review, or source note |
| `risk` | pass/needs_proof/blocked |
| `ads_match_type` | exact/broad/auto/product/negative |
| `listing_action` | add_to_title/add_to_bullet/add_to_backend/add_to_a_plus/remove/watch |

## `evidence_matrix.csv`

| Field | Notes |
|---|---|
| `candidate_id` | Required |
| `sku` | Required once known |
| `control_ref` | e.g. AMZ-JP-CAT-01 |
| `control_area` | category/ip/import/fba/label/claim/gtin/cost |
| `requirement` | What must be proven |
| `evidence` | File, URL, screenshot, report, or user confirmation |
| `status` | pass/needs_proof/blocked/not_applicable |
| `owner` | Responsible person/team |
| `due_date` | Optional |
| `blocking_reason` | Required when blocked |

## `landed_cost_model.csv`

| Field | Notes |
|---|---|
| `candidate_id` | Required |
| `sku` | Required once known |
| `selling_price_jpy` | Required |
| `unit_cost_jpy` | Product unit cost |
| `inspection_packaging_jpy` | QC, packaging, labels |
| `first_mile_jpy` | Domestic origin freight |
| `international_freight_jpy` | Air/sea/courier |
| `duty_tax_jpy` | Duty, import consumption tax estimate, brokerage |
| `fba_fee_jpy` | Fulfillment fee |
| `referral_fee_jpy` | Amazon referral fee |
| `storage_return_allowance_jpy` | Storage, returns, disposal allowance |
| `ad_allowance_jpy` | Launch ad allowance per unit |
| `landed_cost_jpy` | Sum of cost fields |
| `gross_profit_jpy` | selling price - landed cost |
| `gross_margin_pct` | gross profit / selling price |
| `break_even_acos_pct` | gross profit / selling price |
| `decision` | pass/needs_proof/blocked |

## `ads_search_term_feedback.csv`

| Field | Notes |
|---|---|
| `launch_id` | Required |
| `sku` | Required |
| `search_term` | Customer search term |
| `campaign` | Campaign name |
| `match_type` | auto/broad/exact/product |
| `impressions` | numeric |
| `clicks` | numeric |
| `spend_jpy` | numeric |
| `orders` | numeric |
| `sales_jpy` | numeric |
| `acos_pct` | numeric |
| `ctr_pct` | numeric |
| `cvr_pct` | numeric |
| `action` | promote_exact/negate/reduce_bid/increase_bid/add_backend/add_a_plus/watch |
| `reason` | Why this action |

## `live_data/report_manifest.csv`

| Field | Notes |
|---|---|
| `report_name` | Seller Central, Amazon Ads, BA, SQP, inventory, returns, reviews |
| `source_file` | Original export path or filename |
| `date_range` | Data period |
| `freshness` | fresh/stale/unknown |
| `rows` | Row count |
| `blocking_gap` | Missing field or permission issue |
| `next_import` | Next expected update |

## `sourcing/qc_checklist.csv`

| Field | Notes |
|---|---|
| `candidate_id` | Required |
| `sku` | Required when known |
| `qc_area` | material_durability/size_fit/packaging/label/claim/etc. |
| `inspection_item` | What the inspector or sample reviewer checks |
| `evidence_needed` | Photo, video, measurement, test report, or supplier statement |
| `acceptance_rule` | Pass/fail threshold |
| `status` | pass/needs_proof/blocked |

## `seller_central/seller_central.checklist.csv`

| Field | Notes |
|---|---|
| `area` | identity/variation/content/media/offer/compliance |
| `field` | Seller Central or flat-file field |
| `value_present` | yes/no |
| `status` | pass/needs_proof/blocked |
| `owner` | Responsible operator |
| `next_action` | Concrete upload or evidence task |

## `fba/fba.shipment_plan.csv`

| Field | Notes |
|---|---|
| `sku` | Required |
| `asin` | Required when known |
| `daily_sales_estimate` | Used for replenishment |
| `fulfillable_qty` | Current sellable FBA inventory |
| `inbound_qty` | Already inbound quantity |
| `days_of_supply` | Inventory coverage |
| `reorder_point_qty` | Quantity threshold to reorder |
| `recommended_first_shipment_qty` | Initial or next shipment quantity |
| `estimated_stockout_date` | Computed from sales rate |
| `status` | pass/needs_proof/blocked |

## `operations/performance.actions.csv`

| Field | Notes |
|---|---|
| `launch_id` | Required |
| `sku` | Required |
| `area` | ads/listing/fba/qc/product/profit/growth |
| `action` | promote_exact/negate/reduce_bid/replenish/review_listing/etc. |
| `reason` | Metric and threshold |
| `owner` | Responsible operator |
| `status` | todo/doing/done/blocked |

## Candidate Status Values

- `pass`: can advance.
- `watch`: can advance only with explicit owner and next action.
- `needs_proof`: plausible, but cannot launch until evidence is supplied.
- `blocked`: do not continue.
- `reject`: removed from pipeline.
- `launch_ready`: all launch gates passed.
- `scale`: metrics support controlled spend or inventory expansion.
- `optimizing`: live and under weekly iteration.
- `pause`: stop scaling until a quality, inventory, or economics issue is resolved.
- `kill`: stop spend or discontinue.
