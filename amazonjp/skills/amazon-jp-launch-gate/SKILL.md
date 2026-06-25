---
name: amazon-jp-launch-gate
description: Run SKU-level Amazon Japan launch readiness gates before listing, FBA shipment, or advertising. Use when Codex needs to decide whether an Amazon JP product can proceed based on category approval, JAN/GTIN, IP, Japan labeling or certification, import and FBA constraints, landed cost, gross margin, supplier/sample evidence, claim proof, or launch blocking issues.
---

# Amazon JP Launch Gate

## Overview

Use this skill after shortlist validation and before Listing/A+, FBA shipment, or ads. The goal is to prove a SKU can be legally, operationally, and economically launched on Amazon.co.jp.

This skill is a business/compliance checklist, not legal advice. For regulated products, current Seller Central policy and qualified local advice override this workflow.

## Intake

Collect:
- Product: `candidate_id`, SKU, category, product type, materials, use case, target buyer, variations.
- Platform: existing/new ASIN decision, JAN/GTIN or exemption, Brand Registry status, category approval status.
- Supplier: supplier quote, MOQ, lead time, sample result, test report, packaging and label specs.
- Costs: selling price, unit cost, inspection/packaging, first mile, international freight, duty/tax/brokerage, FBA fee, referral fee, storage/return allowance, ad allowance.
- Evidence: IP search, authorization, label images, certification, import docs, FBA restrictions, claim proof.

## Workflow

1. Read `references/launch-gate-schema.md`.
2. Classify controls:
   - category and restricted-product approval
   - JAN/GTIN/new ASIN/variation
   - IP and competitor-brand terms
   - Japan labeling and certifications
   - import/customs/FBA constraints
   - supplier/sample/QC readiness
   - landed cost, gross margin, break-even ACOS
   - claim ledger for Listing, A+, and Ads
3. Mark each control `pass`, `needs_proof`, `blocked`, or `not_applicable`.
4. Calculate unit economics. Use `scripts/evaluate_launch_gate.py` when evidence/cost CSVs are available.
5. Return one final decision:
   - `pass`: no blocked controls and margin clears the threshold.
   - `needs_proof`: no hard block, but launch evidence is incomplete.
   - `blocked`: do not create Listing, ship FBA, or launch ads.

## Hard Blocks

Block launch when any of these are unresolved:
- Category approval or restricted-product status unknown for the exact product type.
- JAN/GTIN ownership or exemption unavailable for a new ASIN.
- IP ownership, authorization, or compatibility wording is unclear.
- Required Japan label/certification evidence is missing for applicable product types.
- FBA restriction, dangerous goods, size, packaging, or import eligibility is unknown.
- Landed cost cannot be estimated or margin is below user threshold without an explicit override.
- A Listing/A+/Ads claim lacks proof and could mislead buyers.

## Output

Output:
- Final decision: `pass`, `needs_proof`, or `blocked`.
- Gate summary by control area.
- Landed-cost summary and break-even ACOS.
- Blocking issues with owner and next action.
- Allowed next step: `product_requirements`, `listing`, `fba_shipment`, `ads`, or `stop`.

For full launch work, produce or update:
- `evidence_matrix.csv`
- `landed_cost_model.csv`
- `launch_gate_report.md`
- `claim_ledger.csv`
