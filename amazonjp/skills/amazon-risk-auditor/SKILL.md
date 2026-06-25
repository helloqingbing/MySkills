---
name: amazon-risk-auditor
description: Audit Amazon Japan product-launch risks for product research. Use when Codex needs to screen Amazon JP home, pet, or outdoor product ideas for compliance, IP, brand dominance, Amazon Basics risk, seasonality, logistics, returns, FBA constraints, prohibited user preferences, or operational launch hazards before shortlisting.
---

# Amazon Risk Auditor

Use this skill before recommending a product candidate. It is a screening tool, not legal advice.

For full launch workflows, output structured fields that can be consumed by `amazon-jp-sop-orchestrator` and `amazon-jp-launch-gate`.

## Workflow

1. Read `references/risk-rules.md`.
2. Check hard rejects first:
   - food, supplements, medical, child/baby, electric/battery, liquids
   - obvious IP/character/brand dependency
   - claims requiring regulated proof
3. Check commercial risks:
   - Amazon Basics or dominant national brand in top ASINs
   - top 5 brand click share >= 65%
   - top 20 brand click share >= 85%
   - average review count >= 2,000
4. Check logistics:
   - bulky, fragile, high return, difficult packaging
   - temperature-sensitive or leakage-prone
5. Return a decision:
   - `pass`
   - `watch`
   - `reject`
   - `blocked_pending_approval`
   - `needs_proof`

Always include the specific reason and what data would reduce uncertainty.

## Structured Output

When auditing one or more candidates, include a table with:

| Field | Meaning |
|---|---|
| `candidate_id` | Stable opportunity ID |
| `risk_decision` | pass/watch/reject/needs_proof/blocked_pending_approval |
| `risk_level` | low/medium/high |
| `control_area` | category/ip/claim/logistics/fba/competition/seasonality |
| `reason` | Specific evidence |
| `data_needed` | Evidence to reduce uncertainty |
| `mitigation` | Action before next gate |

Do not allow `blocked_pending_approval`, `needs_proof`, or `reject` candidates to proceed to Listing/A+ or Ads without an explicit override.
