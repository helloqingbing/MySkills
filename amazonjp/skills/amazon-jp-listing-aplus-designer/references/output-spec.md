# Amazon JP Listing + A+ Output Spec

Use this reference for full Amazon.co.jp listing packages, A+ design briefs, audits, and revision passes.

## Full Package

1. Assumptions and missing inputs
2. Buyer and positioning summary
3. Keyword map
4. Listing copy
5. Backend Search Terms
6. Image set recommendations
7. A+ module map
8. A+ copy deck
9. Image production brief
10. Compliance and quality checklist
11. Seller Central field mapping when the user needs copy-paste readiness
12. Keyword master and Ads export when the package will feed launch ads

## Keyword Map

Create a table with:
- Priority: primary, secondary, long-tail, backend-only
- Japanese term
- Reading or variant if useful
- English or katakana variant
- Intent: category, attribute, use case, pain, spec, material, audience, season/gift
- Placement: title, bullet, description, A+, backend
- Notes: evidence source, ambiguity, risk

For launch workflows, also create or update `amazon_keyword_master.csv` with:

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

Map primary purchase-intent terms to `exact`, secondary and long-tail terms to `broad` or `exact` depending on relevance, backend-only variants to `backend` or `ads_only`, and risky terms to `negative`.

## Listing Copy

Provide:

```markdown
## Title
[Japanese title]

## Bullet Points
1. [Japanese bullet]
2. [Japanese bullet]
3. [Japanese bullet]
4. [Japanese bullet]
5. [Japanese bullet]

## Product Description
[Japanese description]

## Backend Search Terms
[space-separated terms]

## Image Text Suggestions
1. Main image: no overlay text unless marketplace rules allow for non-main images.
2. Sub image 1:
3. Sub image 2:
4. Sub image 3:
5. Sub image 4:
6. Sub image 5:
7. Sub image 6:
```

Keep Japanese concise and natural. Include Chinese or English rationale after each section only when useful for the user.

## A+ Module Map

Create a table with:
- Order
- Module name
- Goal
- Buyer question answered
- Visual concept
- Japanese headline
- Japanese body copy
- Asset needs
- Compliance note

Recommended sequence:
1. Hero value proposition
2. Top 3 benefits
3. Use scene
4. Detail/material/size proof
5. Comparison or variant table
6. FAQ/care/compatibility
7. Brand trust

Use fewer modules for simple products. Add modules only when each one adds new information.

## Image Brief

For each image or A+ module, specify:
- File purpose
- Composition and crop
- Product angle or scene
- Props/background
- Human hand/body inclusion if needed for scale
- Text overlay
- Japanese copy
- Required proof assets
- Mobile readability check

For listing image planning, draft 1 main image plus up to 8 supporting image concepts when useful: dimensions, feature close-up, usage scene, material proof, package contents, comparison, care/use instructions, and trust cue. Do not imply accessories, colors, or use cases that are not included or supported.

## Compliance Checklist

Flag and revise:
- Duplicate-ASIN risk: unclear existing listing vs new listing decision.
- Missing or questionable JAN/GTIN ownership or exemption basis.
- Category, FBA, battery, food, cosmetic, medical, child/pet, chemical, electrical, or safety restrictions that need current official verification.
- Japan-specific proof needs such as PSE for applicable electrical goods, food labeling, cosmetic/quasi-drug/medical-device constraints, or importer/labeling obligations.
- Unsupported medical, health, safety, durability, eco, certification, origin, or performance claims.
- Price, discount, shipping, review, rating, ranking, limited-time, or "No.1" style claims.
- Competitor brand names, trademarks, ASINs, or misleading compatibility language.
- Keywords for colors, sizes, functions, accessories, or materials not actually sold.
- Keyword stuffing, hidden repetition, unnatural Japanese, excessive punctuation, and irrelevant traffic terms.
- A+ image text too small for mobile or dependent on desktop-only details.
- Missing proof for regulated categories or product safety claims.

Use risk labels:
- `Pass`: safe enough based on provided evidence and current task scope.
- `Needs Proof`: plausible but requires documentation, official policy check, or user confirmation.
- `Blocked`: should not publish until changed or approved by a qualified owner.

## Seller Central Field Mapping

When requested, provide a table with:
- Field
- Japanese value
- Source section
- Copy-paste ready: yes/no
- Notes or proof required

## Ads Export

When the listing package will feed Sponsored Products planning, add:

| keyword | match_type | relevance | intent | source | target_campaign | reason |
|---|---|---|---|---|---|---|

Rules:
- Use `exact` for high-relevance category and purchase-intent terms.
- Use `broad` for discovery modifiers and pain/use-case terms.
- Use `negative phrase` or `negative exact` for unsupported attributes, irrelevant use cases, food/baby/medical/electric/liquid terms, and competitor brands unless explicitly approved.
- Use `product target` only for competitor ASINs with weaker price, reviews, images, bundle, or rating.

## Quality Bar

The package is ready when:
- A Japanese shopper can understand the product and main benefit within 3 seconds on mobile.
- The title remains understandable if truncated after the first half.
- Every bullet contains one buyer benefit and one concrete proof point.
- Backend Search Terms mostly add new indexable coverage instead of repeating visible copy.
- A+ modules progress from persuasion to proof to objection handling.
- All assumptions and unresolved compliance questions are visible.
