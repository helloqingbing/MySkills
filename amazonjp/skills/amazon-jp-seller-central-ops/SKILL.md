---
name: amazon-jp-seller-central-ops
description: Prepare Amazon Japan Seller Central execution packages for listing creation, variation setup, flat files, A+ submission, suppressed listing checks, and manual operation logs. Use whenever Codex needs to convert an approved Amazon JP launch package into concrete Seller Central steps, required fields, upload checklists, human-owner tasks, or issue triage for ASIN creation and listing operations.
---

# Amazon JP Seller Central Ops

## Overview

Use this skill after `amazon-jp-launch-gate` is not blocked and before FBA shipment or advertising. The goal is to turn approved product, content, and evidence artifacts into a Seller Central operations checklist that a human operator can execute.

This skill does not log into Seller Central. It creates field checklists, flat-file readiness checks, manual operation plans, and issue triage.

## Intake

Collect:

- SKU, parent/child ASIN decision, variation theme, JAN/GTIN or exemption status.
- Category, product type, browse node, brand name, manufacturer, country of origin.
- Listing package, image brief, A+ module map, claim ledger, keyword master.
- Evidence matrix, Japan label/certification files, warranty or instruction notes.
- FBA readiness status, package dimensions, and launch target date.

## Workflow

1. Confirm launch gate status. If `blocked`, do not prepare upload steps; list blockers.
2. Build Seller Central field coverage:
   - identity and variation fields
   - title, bullets, description, backend search terms
   - category attributes and compliance fields
   - images and A+ assets
   - offer, price, tax, fulfillment, and inventory fields
3. Create a manual operation log with owner, action, evidence file, and expected screenshot/proof.
4. Flag issues that often stop launches:
   - missing JAN/GTIN or exemption
   - incomplete variation parent/child mapping
   - claim without proof
   - image or A+ text mismatch
   - missing required category attribute
   - listing suppressed or stranded inventory follow-up
5. Return `pass`, `needs_proof`, or `blocked` for Seller Central readiness.

## Local Script

For file-based checks, run:

```bash
python3 scripts/build_seller_central_checklist.py --workspace /path/to/launch --launch-id L1 \
  --listing listing_package.csv \
  --evidence evidence_matrix.csv \
  --gate-decision launch_gate.decision.csv \
  --ops-proof seller_central_upload_proof.csv \
  --output-prefix seller_central
```

The script writes:

- `seller_central.checklist.csv`
- `seller_central.ops_log.csv`
- `seller_central.readiness.md`
- `seller_central.decision.csv`

The proof CSV uses `sku,field,evidence_file,owner,status`. Each field requires a nonempty
local screenshot or uploaded flat-file proof with `status=done` before readiness can pass.

## Output

Return:

- Seller Central readiness decision
- field checklist grouped by upload area
- flat-file or manual upload actions
- owner-facing operation log
- evidence still needed before ASIN/FBA/ads

## Bound approval contract

Install these skills together, preserving the sibling directory layout; scripts share
`amazon-jp-sop-orchestrator/scripts/approval_contract.py` and the Launch Gate validator.
The launch must currently be at `G9`. `--workspace` and `--launch-id` are required.
Downstream scripts verify the matching human-approved gate events and SHA-256 of the
approved files (including referenced local proof snapshots). A same-SKU pass CSV from
another launch or a changed evidence file cannot release this launch. Keep approved
snapshots immutable. Older workspaces without bound approvals require a new audited
launch; copying a historical pass CSV does not migrate approval.
The local workspace is the trust boundary; this is not a signed approval/auth service.

Compliance uses `control_ref`, not free-text control names. Valid CLAIMS-JP-01
`not_applicable` evidence carries through from G6 with a reason, owner, source, date
and nonempty local snapshot. JP-IMPORT-FBA-01 cannot be not_applicable.

G8 approval must include the exact listing CSV and keyword master files consumed by
Seller Central and Ads. A different file, even for the same SKU, requires a new audit.
