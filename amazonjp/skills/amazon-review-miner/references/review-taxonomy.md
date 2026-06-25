# Review Mining Taxonomy

## Fixable Complaint Groups

| Group | Japanese cues | Product actions |
|---|---|---|
| Leakage / waterproofing | 漏れ, 水漏れ, 防水, 密閉 | better seal, thicker material, leak-test claim |
| Durability | 破れ, 壊れ, 耐久, 薄い, すぐ | thicker material, reinforced seam, better QA |
| Size / usability | 小さい, 大きい, 使いにくい, サイズ | clearer size set, visual guide, ergonomic redesign |
| Cleaning / odor | 洗いにくい, 臭い, 匂い, カビ | easier-clean shape, odorless material, drying accessory |
| Bundle gap | 足りない, セット, 予備, 付属 | more pieces, replacement parts, accessory bundle |
| Packaging | 箱, 梱包, 破損, 届いた | stronger packaging, gift-ready box, lower damage rate |
| Japanese localization | 説明書, 日本語, わかりにくい | Japanese manual, QR video, better listing images |

## Non-Fixable or Risky Signals

- Complaints requiring medical, food-safety, child-safety, or regulated claims.
- Requests for electric/battery functionality when the user avoids powered products.
- Price-only complaints without clear product improvement.

## Output Standard

For each opportunity, include:

- complaint cluster
- affected ASINs
- evidence count
- fixability: high / medium / low
- proposed product change
- listing claim caution

## Structured Product Requirements CSV

Use these columns when review output must feed Listing/A+, sourcing, or launch gates:

| Field | Meaning |
|---|---|
| `candidate_id` | Opportunity ID when known |
| `sku` | SKU when known |
| `complaint_cluster` | taxonomy group |
| `affected_asins` | ASIN list |
| `evidence_count` | number of matching low-star reviews |
| `fixability` | high/medium/low |
| `product_action` | concrete product/supplier requirement |
| `claim_caution` | proof needed before using as a Listing/A+ claim |
| `aplus_module_candidate` | module idea |
| `image_brief_hint` | image or diagram needed |
