# Amazon JP Launch Gate Schema

## Evidence Matrix

Use `evidence_matrix.csv` to decide whether a SKU can continue.

| Field | Required | Notes |
|---|---|---|
| `candidate_id` | yes | Research opportunity ID |
| `sku` | no | Required before FBA/listing |
| `control_ref` | yes | e.g. AMZ-JP-CAT-01 |
| `control_area` | yes | category/gtin/ip/label/import/fba/supplier/cost/claim |
| `requirement` | yes | What must be true |
| `evidence` | no | File, URL, screenshot, report, or user confirmation |
| `status` | yes | pass/needs_proof/blocked/not_applicable |
| `owner` | no | Responsible person/team |
| `due_date` | no | Optional |
| `blocking_reason` | no | Required for blocked |

## Required Controls

| Control ref | Area | Requirement | Blocks when |
|---|---|---|---|
| `AMZ-JP-CAT-01` | category | Seller Central category and restricted-product status checked | unknown or rejected |
| `GTIN-ASIN-01` | gtin | JAN/GTIN ownership, exemption, existing-ASIN match, and variation plan checked | unknown for new ASIN |
| `IP-JP-01` | ip | Trademark/design/patent/FTO and image authorization checked | brand/IP dependency unresolved |
| `JP-LABEL-CERT-01` | label | Japan label/certification obligations checked | applicable proof missing |
| `JP-IMPORT-FBA-01` | import/fba | HS code, IOR, customs docs, dangerous goods, FBA prep/size restrictions checked | import or FBA eligibility unknown |
| `SUPPLIER-QC-01` | supplier | Supplier quote, sample, QC, packaging, and lead time checked | no quote or sample/QC blockers |
| `CLAIMS-JP-01` | claim | Listing/A+/Ads claims mapped to evidence | claim lacks proof |
| `ECON-JP-01` | cost | Landed cost and margin meet threshold | cost unknown or margin below threshold |

## Landed Cost Model

Use `landed_cost_model.csv`.

| Field | Required | Notes |
|---|---|---|
| `candidate_id` | yes | Stable ID |
| `sku` | no | Required before launch |
| `selling_price_jpy` | yes | Listing price |
| `unit_cost_jpy` | yes | Supplier product cost |
| `inspection_packaging_jpy` | no | QC, inserts, labels, cartons |
| `first_mile_jpy` | no | Origin domestic freight |
| `international_freight_jpy` | yes | Air/sea/courier allocated per unit |
| `duty_tax_jpy` | yes | Duty, import tax estimate, brokerage |
| `fba_fee_jpy` | yes | Amazon FBA fulfillment fee |
| `referral_fee_jpy` | yes | Referral fee |
| `storage_return_allowance_jpy` | no | Storage, return, disposal reserve |
| `ad_allowance_jpy` | no | Launch ad allowance per unit |
| `landed_cost_jpy` | no | Computed if blank |
| `gross_profit_jpy` | no | Computed if blank |
| `gross_margin_pct` | no | Computed if blank |
| `break_even_acos_pct` | no | Computed if blank |
| `decision` | no | pass/needs_proof/blocked |

## Decision Rules

- `blocked` if any evidence control is `blocked`.
- `needs_proof` if any required evidence control is missing or `needs_proof`.
- `blocked` if price or major cost fields are absent.
- `blocked` if `gross_margin_pct` is below the threshold and no override is stated.
- `pass` only when no hard blocks remain and economics meet the target.
