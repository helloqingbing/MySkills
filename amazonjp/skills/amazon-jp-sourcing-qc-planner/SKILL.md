---
name: amazon-jp-sourcing-qc-planner
description: Build supplier sourcing, sample evaluation, QC inspection, packaging, and claim-proof plans for Amazon Japan launches. Use whenever Codex needs to compare supplier quotes, define must-pass QC checks, convert review-mined defects into inspection criteria, prepare sample scorecards, or make supplier evidence usable by Amazon JP launch gates.
---

# Amazon JP Sourcing QC Planner

## Overview

Use this skill between opportunity validation and launch gate. It turns supplier quotes, samples, review-mined defects, and product requirements into a sourcing and QC execution package.

The goal is to prevent a common launch failure: the product looks promising in research but lacks supplier proof, sample consistency, packaging quality, or inspection criteria.

## Intake

Collect:

- Candidate ID, SKU, target price, target margin, MOQ, lead time.
- Supplier quotes, supplier URLs, sample costs, certifications, and production notes.
- Review-mined product requirements and must-fix defects.
- Packaging requirements, Japanese label requirements, instruction sheet needs.
- Claim ledger and proof requirements.

## Workflow

1. Compare suppliers by cost, MOQ, lead time, evidence, sample status, and risk.
2. Convert review pain into QC checks:
   - material and durability
   - size and fit
   - odor, cleaning, leakage, waterproofing
   - accessory completeness
   - packaging and shipping damage
   - instruction/localization clarity
3. Build a sample scorecard:
   - pass/fail checks
   - measured specs
   - photo/video evidence needed
   - accepted tolerances
   - supplier remediation request
4. Mark readiness:
   - `pass`: supplier and QC proof are enough for launch gate
   - `needs_proof`: promising but evidence is missing
   - `blocked`: sample/QC/supplier economics do not support launch

## Local Script

For CSV-based supplier and requirement checks, run:

```bash
python3 scripts/build_qc_plan.py \
  --suppliers supplier_quotes.csv \
  --requirements product_requirements.csv \
  --output-prefix sourcing_qc
```

The script writes:

- `sourcing_qc.supplier_scorecard.csv`
- `sourcing_qc.qc_checklist.csv`
- `sourcing_qc.sample_review.md`

## Output

Return:

- recommended supplier or supplier short list
- QC checklist mapped to review pain and claims
- sample scorecard
- packaging and Japanese label evidence needed
- launch gate handoff fields
