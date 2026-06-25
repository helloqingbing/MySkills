#!/usr/bin/env python3
import argparse
import csv
import os


DIRECTORIES = [
    "raw_exports",
    "live_data",
    "normalized",
    "analysis",
    "validation",
    "sourcing",
    "launch_gate",
    "product",
    "listing",
    "seller_central",
    "fba",
    "ads",
    "operations",
    "archive",
]


TEMPLATES = {
    "analysis/candidates.csv": [
        "candidate_id", "niche_name", "top_search_term", "decision", "owner",
        "status", "next_action", "blocking_reason",
    ],
    "live_data/report_manifest.csv": [
        "report_name", "source_file", "date_range", "freshness", "rows",
        "blocking_gap", "next_import",
    ],
    "sourcing/supplier_scorecard.csv": [
        "candidate_id", "sku", "supplier_name", "unit_cost_jpy", "moq",
        "lead_time_days", "certifications", "sample_status", "supplier_score",
        "decision", "next_action",
    ],
    "sourcing/qc_checklist.csv": [
        "candidate_id", "sku", "qc_area", "inspection_item", "evidence_needed",
        "acceptance_rule", "status",
    ],
    "launch_gate/evidence_matrix.csv": [
        "candidate_id", "sku", "control_ref", "control_area", "requirement",
        "evidence", "status", "owner", "due_date", "blocking_reason",
    ],
    "launch_gate/landed_cost_model.csv": [
        "candidate_id", "sku", "selling_price_jpy", "unit_cost_jpy",
        "inspection_packaging_jpy", "first_mile_jpy", "international_freight_jpy",
        "duty_tax_jpy", "fba_fee_jpy", "referral_fee_jpy",
        "storage_return_allowance_jpy", "ad_allowance_jpy", "landed_cost_jpy",
        "gross_profit_jpy", "gross_margin_pct", "break_even_acos_pct", "decision",
    ],
    "listing/amazon_keyword_master.csv": [
        "candidate_id", "sku", "keyword", "jp_variant", "priority", "intent",
        "placement", "source", "search_volume_360d", "conversion_rate_pct",
        "relevance", "evidence", "risk", "ads_match_type", "listing_action",
    ],
    "product/product_requirements.csv": [
        "candidate_id", "sku", "complaint_cluster", "affected_asins",
        "evidence_count", "fixability", "product_action", "claim_caution",
        "aplus_module_candidate", "image_brief_hint",
    ],
    "listing/claim_ledger.csv": [
        "candidate_id", "sku", "claim", "allowed_placement", "proof_required",
        "proof_available", "status", "notes",
    ],
    "seller_central/seller_central.checklist.csv": [
        "area", "field", "label", "value_present", "status", "owner",
        "next_action",
    ],
    "seller_central/seller_central.ops_log.csv": [
        "owner", "action", "expected_proof", "status",
    ],
    "fba/fba.shipment_plan.csv": [
        "sku", "asin", "daily_sales_estimate", "fulfillable_qty",
        "inbound_qty", "days_of_supply", "total_replenishment_lead_days",
        "reorder_point_qty", "recommended_first_shipment_qty",
        "estimated_stockout_date", "status", "next_action",
    ],
    "fba/fba.replenishment_alerts.csv": [
        "sku", "asin", "daily_sales_estimate", "fulfillable_qty",
        "inbound_qty", "days_of_supply", "total_replenishment_lead_days",
        "reorder_point_qty", "recommended_first_shipment_qty",
        "estimated_stockout_date", "status", "next_action",
    ],
    "ads/ads_search_term_feedback.csv": [
        "launch_id", "sku", "search_term", "campaign", "match_type",
        "impressions", "clicks", "spend_jpy", "orders", "sales_jpy",
        "acos_pct", "ctr_pct", "cvr_pct", "action", "reason",
    ],
    "operations/launch_metrics_weekly.csv": [
        "launch_id", "sku", "week_start", "sessions", "unit_session_pct",
        "orders", "sales_jpy", "ad_spend_jpy", "acos_pct", "tacos_pct",
        "break_even_acos_pct", "days_of_supply", "organic_rank_notes",
        "reviews", "rating", "returns", "next_action",
    ],
    "operations/performance.actions.csv": [
        "launch_id", "sku", "area", "action", "reason", "owner", "status",
    ],
    "operations/performance.alerts.csv": [
        "launch_id", "sku", "search_term", "action", "reason", "sales_jpy",
    ],
}


README = """# Amazon JP Launch Workspace

Use this workspace with $amazon-jp-sop-orchestrator.

Advance candidates only when the current gate has a decision and blocking issues are visible.
"""


def write_csv(path, fields):
    if os.path.exists(path):
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    for directory in DIRECTORIES:
        os.makedirs(os.path.join(args.output_dir, directory), exist_ok=True)
    for rel_path, fields in TEMPLATES.items():
        write_csv(os.path.join(args.output_dir, rel_path), fields)
    readme_path = os.path.join(args.output_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(README)
    print(args.output_dir)


if __name__ == "__main__":
    main()
