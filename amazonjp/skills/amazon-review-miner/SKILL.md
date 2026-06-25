---
name: amazon-review-miner
description: Mine Amazon Japan reviews for product-improvement opportunities. Use when Codex needs to analyze Japanese or English Amazon review exports, cluster 1-3 star complaints, identify fixable product defects, extract bundle/accessory/material/packaging ideas, or turn ASIN reviews into differentiated product requirements.
---

# Amazon Review Miner

Use this skill after a niche or ASIN shortlist exists. Focus on fixable pain, not general sentiment. For full Amazon JP launch workflows, produce both human-readable review insights and structured product requirements that can feed Listing/A+, claim proof, image briefs, and supplier QC.

## Workflow

1. Prefer 1-3 star reviews from competing ASINs.
2. Read `references/review-taxonomy.md`.
3. Cluster complaints into:
   - material and durability
   - size and fit
   - leakage, waterproofing, odor, cleaning
   - missing accessories or bundle gaps
   - packaging and shipping damage
   - unclear instructions or Japanese localization issues
4. Separate fixable issues from non-fixable market expectations.
5. Produce product requirements:
   - `candidate_id` and SKU/ASIN context when available
   - must-fix defects
   - candidate differentiators
   - listing copy claims that need evidence
   - review quotes or paraphrased evidence
   - A+ module candidates and image brief hints

## Script

If a review CSV is available with columns such as `asin`, `rating`, `review_title`, `review_text`, run:

```bash
python3 scripts/mine_reviews.py --reviews reviews.csv --output review_opportunities.md --csv-output product_requirements.csv
```

The CSV should include: `candidate_id`, `sku`, `complaint_cluster`, `affected_asins`, `evidence_count`, `fixability`, `product_action`, `claim_caution`, `aplus_module_candidate`, and `image_brief_hint`.
