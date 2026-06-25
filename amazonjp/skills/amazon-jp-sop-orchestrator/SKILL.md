---
name: amazon-jp-sop-orchestrator
description: Orchestrate an end-to-end Amazon Japan cross-border ecommerce launch workflow across the local amazon-* skills. Use when Codex needs to turn product research or live Seller Central data into an executable SOP with candidate IDs, stage gates, artifact contracts, sourcing and QC plans, Seller Central upload tasks, FBA shipment checkpoints, keyword master data, ad feedback loops, weekly metrics, alerts, or a full Amazon JP launch runbook from research through post-launch optimization.
---

# Amazon JP SOP Orchestrator

## Overview

Use this skill as the control plane for Amazon Japan cross-border product launches. It does not replace the specialist skills; it defines the state machine, artifact contracts, gate order, and feedback loops that let the other `amazon-*` skills work as one executable system.

Use the specialist skills in this order unless the user asks for a narrower slice:

1. `amazon-jp-live-data-sync`
2. `amazon-data-ingestor`
3. `amazon-opportunity-scorer`
4. `amazon-risk-auditor`
5. `amazon-radar-report`
6. `amazon-jp-sourcing-qc-planner`
7. `amazon-jp-launch-gate`
8. `amazon-review-miner`
9. `amazon-jp-listing-aplus-designer`
10. `amazon-jp-seller-central-ops`
11. `amazon-jp-fba-shipment-planner`
12. `amazon-ads-planner`
13. `amazon-jp-performance-reviewer`

## Operating Rule

Do not advance a candidate to the next stage unless the current gate has an explicit status and blocking evidence is visible. If data is missing, label the candidate `needs_proof` or `blocked` rather than filling gaps optimistically.

Use stable IDs throughout:
- `candidate_id`: research-stage product opportunity.
- `sku`: seller-controlled sellable SKU.
- `parent_asin`: Amazon parent ASIN when known.
- `launch_id`: one go-to-market attempt for one SKU or variation set.

## State Machine

Read `references/artifact-contracts.md` before creating a full runbook, project workspace, or cross-skill handoff.

Use this lifecycle:

```text
raw_data
-> live_data_synced
-> normalized
-> scored
-> risk_screened
-> validation_planned
-> sourcing_qc_ready
-> commercially_validated
-> launch_gate_reviewed
-> product_requirements_ready
-> listing_ready
-> seller_central_ready
-> fba_ready
-> ads_ready
-> launched
-> performance_reviewed
-> optimizing
```

Required gates:
- `G0 live_data_sync`: fresh reports are normalized when available, with data-quality gaps visible.
- `G1 data_quality`: normalized data has stable IDs and joinable ASIN/search-term fields.
- `G2 opportunity`: score label is `A` or `B`, or a documented override exists.
- `G3 risk`: risk decision is not `reject` and hard-risk notes are resolved.
- `G4 sourcing_qc`: supplier quote, sample status, QC checks, packaging, and claim proof are usable.
- `G5 commercial_validation`: landed cost, Keepa/trend, FBA fee, and margin are checked.
- `G6 launch_gate`: compliance, IP, category, import/FBA, and evidence matrix are passable.
- `G7 product_definition`: review pain becomes requirements, proof, and allowed claims.
- `G8 listing`: Japanese copy, A+, images, keyword master, and claim ledger are ready.
- `G9 seller_central`: required flat-file/manual fields and upload proof are ready.
- `G10 fba`: FBA labels, box specs, shipment plan, and inventory risk are checked.
- `G11 ads`: keyword master, economics, campaign CSV, negatives, and launch budget are ready.
- `G12 performance`: weekly metrics, inventory, returns, reviews, and ad search terms feed back to actions.

## Workflow

1. Create or verify workspace structure.
   Run `scripts/create_launch_workspace.py` when the user wants a project folder or reusable templates.

2. Sync live data when the user provides fresh reports.
   Use `amazon-jp-live-data-sync` for Seller Central, Amazon Ads, inventory, returns, reviews, or weekly operating exports.

3. Normalize source data.
   Use `amazon-data-ingestor` and preserve `candidate_id` where present. If missing, create deterministic IDs from niche/search term/product name.

4. Score and screen.
   Use `amazon-opportunity-scorer` and `amazon-risk-auditor`. Keep rejected products in the audit trail.

5. Build the validation pack.
   Use `amazon-radar-report` to produce the shortlist, then create `validation_evidence.md` and `launch_handoff.csv`.

6. Build sourcing and QC evidence.
   Use `amazon-jp-sourcing-qc-planner` to compare suppliers, turn review pain into QC checks, and prepare sample proof.

7. Run launch gate before Listing, FBA, Seller Central upload, or Ads.
   Use `amazon-jp-launch-gate` for compliance, landed cost, FBA/import, IP, and evidence readiness.

8. Define product and content.
   Use `amazon-review-miner` to generate structured product requirements, then `amazon-jp-listing-aplus-designer` for Listing/A+, keyword master, and claim ledger.

9. Prepare Seller Central and FBA execution.
   Use `amazon-jp-seller-central-ops` for upload fields and manual proof, then `amazon-jp-fba-shipment-planner` for shipment quantities, labels, and replenishment risk.

10. Plan advertising and feedback.
   Use `amazon-ads-planner` with `amazon_keyword_master.csv`.

11. Review performance after launch.
   Use `amazon-jp-performance-reviewer` with live metrics, ad search terms, inventory, returns, and reviews.

12. End every run with next actions.
   Return one of: `continue`, `watch`, `needs_proof`, `blocked`, `launch_ready`, `scale`, `optimize`, `pause`, `kill`.

## Output

For an orchestration request, output:
- Current stage and gate status.
- Artifact table with present/missing files.
- Blocking issues with owner and next action.
- Candidate decision table.
- Next 7 days of work.

For a mature launch, maintain:
- `amazon_keyword_master.csv`
- `evidence_matrix.csv`
- `landed_cost_model.csv`
- `product_requirements.csv`
- `listing_package.md`
- `seller_central.checklist.csv`
- `fba.shipment_plan.csv`
- `ads_campaigns.csv`
- `ads_search_term_feedback.csv`
- `launch_metrics_weekly.csv`
- `performance.actions.csv`
