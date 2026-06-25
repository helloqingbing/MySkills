---
name: amazon-jp-fba-shipment-planner
description: Plan Amazon Japan FBA shipment execution, carton rules, label checks, replenishment quantities, inventory risk, and shipment handoff tasks. Use whenever Codex needs to prepare FBA labels, box specs, shipment plans, replenishment alerts, first shipment quantities, days-of-supply calculations, or operational checks before sending inventory into Amazon.co.jp fulfillment centers.
---

# Amazon JP FBA Shipment Planner

## Overview

Use this skill after Seller Central listing readiness and before inventory is shipped. It converts product dimensions, demand assumptions, current inventory, and launch plans into an FBA execution package.

This skill provides operational planning, not freight brokerage or customs advice. User-provided forwarder, customs, and FBA policy evidence overrides assumptions.

## Intake

Collect:

- SKU, ASIN, variation set, marketplace, fulfillment method.
- Package dimensions, weight, carton quantity, carton dimensions, carton weight.
- Current inventory, inbound inventory, reserved inventory, daily sales estimate.
- Supplier lead time, production lead time, freight lead time, FBA receiving buffer.
- Label requirements, packaging requirements, expiration/lot rules if applicable.
- Target launch date and initial ad budget.

## Workflow

1. Verify listing and launch gate are not blocked.
2. Calculate:
   - first shipment quantity
   - days of supply
   - reorder point
   - reorder date
   - stockout risk
3. Build FBA execution checklist:
   - FNSKU / item label
   - carton labels
   - box content information
   - polybag, suffocation warning, bundle, set, fragile, or liquid checks if relevant
   - shipment plan proof
4. Flag blockers:
   - dimensions or weight missing
   - carton exceeds acceptable handling assumptions
   - expected stockout before replenishment can arrive
   - label or packaging proof missing
5. Feed inventory alerts to `amazon-jp-performance-reviewer`.

## Local Script

For CSV-based planning, run:

```bash
python3 scripts/plan_fba_shipment.py \
  --inventory inventory.csv \
  --package-specs package_specs.csv \
  --daily-sales daily_sales.csv \
  --output-prefix fba
```

The script writes:

- `fba.shipment_plan.csv`
- `fba.replenishment_alerts.csv`
- `fba.execution_checklist.md`

## Output

Return:

- shipment readiness decision
- initial shipment quantity and reorder point
- label/box/content checklist
- stockout and overstock risks
- owner actions before inventory leaves the supplier
