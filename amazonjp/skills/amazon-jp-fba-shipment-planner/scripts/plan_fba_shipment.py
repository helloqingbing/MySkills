#!/usr/bin/env python3
import argparse
import csv
import math
from datetime import date, timedelta
from pathlib import Path

PROOF_FIELDS = ("fnsku_label_file", "carton_label_file", "box_content_file", "shipment_plan_file")


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def has_pass(path, sku):
    return sum(row.get("sku") == sku and row.get("decision") == "pass" for row in read_csv(path)) == 1


def parse_number(value, default=None):
    text = str(value or "").replace(",", "").replace("￥", "").strip()
    if not text:
        return default
    try:
        number = float(text)
        return number if math.isfinite(number) else default
    except ValueError:
        return default


def get(row, *names):
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    return ""


def index_by_sku(rows):
    indexed = {}
    for row in rows:
        sku = get(row, "sku", "SKU", "seller_sku")
        if sku:
            indexed[sku] = row
    return indexed


def plan_row(inv, specs, sales, proof=None):
    proof = proof or {}
    sku = get(inv, "sku", "SKU", "seller_sku")
    launch_phase = get(inv, "launch_phase", "Launch Phase").lower() or "live"
    daily_sales = parse_number(get(sales, "daily_sales_estimate", "daily_sales", "Daily Sales Estimate"))
    fulfillable = parse_number(get(inv, "fulfillable_qty", "afn-fulfillable-quantity", "Fulfillable Quantity"))
    inbound = parse_number(get(inv, "inbound_qty", "afn-inbound-working-quantity", "Inbound Quantity"))
    production_days = parse_number(get(specs, "production_lead_time_days", "Production Lead Time Days"))
    freight_days = parse_number(get(specs, "freight_lead_time_days", "Freight Lead Time Days"))
    fba_buffer_days = parse_number(get(specs, "fba_receiving_buffer_days", "FBA Receiving Buffer Days"))
    safety_days = parse_number(get(specs, "safety_stock_days", "Safety Stock Days"))
    target_days = parse_number(get(specs, "target_days_of_supply", "Target Days of Supply"))
    required = {"sku": sku, "daily_sales_estimate": daily_sales,
                "fulfillable_qty": fulfillable, "inbound_qty": inbound,
                "package_weight_g": parse_number(get(specs, "package_weight_g", "Package Weight g")),
                "package_length_cm": parse_number(get(specs, "package_length_cm", "Package Length cm")),
                "package_width_cm": parse_number(get(specs, "package_width_cm", "Package Width cm")),
                "package_height_cm": parse_number(get(specs, "package_height_cm", "Package Height cm")),
                "carton_qty": parse_number(get(specs, "carton_qty", "Carton Qty")),
                "carton_weight_g": parse_number(get(specs, "carton_weight_g", "Carton Weight g")),
                "production_lead_time_days": production_days,
                "freight_lead_time_days": freight_days,
                "fba_receiving_buffer_days": fba_buffer_days,
                "safety_stock_days": safety_days,
                "target_days_of_supply": target_days}
    missing = [key for key, value in required.items() if value is None or value == ""]
    if launch_phase not in {"prelaunch", "live"}:
        missing.append("launch_phase must be prelaunch or live")
    invalid = [key for key, value in required.items() if isinstance(value, (int, float)) and
               (value < 0 or (key in {"daily_sales_estimate", "package_weight_g", "package_length_cm",
                                   "package_width_cm", "package_height_cm", "carton_qty", "carton_weight_g",
                                   "target_days_of_supply"}
                                and value == 0))]
    lead_values = (production_days, freight_days, fba_buffer_days, safety_days, target_days)
    if any(value is None or value < 0 for value in lead_values):
        invalid.append("lead/target days")
    total_lead_days = sum(lead_values[:3]) if not invalid else None
    if missing or invalid:
        days_of_supply = reorder_point_qty = first_shipment_qty = stockout_date = None
        status = "needs_proof"
        action = "provide or correct: " + ", ".join(sorted(set(missing + invalid)))
    else:
        days_of_supply = fulfillable / daily_sales
        reorder_point_qty = daily_sales * (total_lead_days + safety_days)
        first_shipment_qty = max(0, daily_sales * target_days - fulfillable - inbound)
        stockout_date = date.today() + timedelta(days=int(days_of_supply)) if launch_phase == "live" else None
        status = "blocked" if launch_phase == "live" and days_of_supply < total_lead_days else "pass"
        action = next_action(status, days_of_supply, total_lead_days)
        proof_paths = [str(Path(get(proof, field)).resolve()) for field in PROOF_FIELDS if get(proof, field)]
        missing_proof = [field for field in PROOF_FIELDS if not get(proof, field) or
                         Path(get(proof, field)).suffix.lower() not in {".png", ".jpg", ".jpeg", ".pdf", ".csv"} or
                         proof_paths.count(str(Path(get(proof, field)).resolve())) > 1 or
                         not Path(get(proof, field)).is_file() or Path(get(proof, field)).stat().st_size == 0]
        if status == "pass" and missing_proof:
            status = "needs_proof"
            action = "provide FBA proof: " + ", ".join(missing_proof)
    return {
        "sku": sku,
        "launch_phase": launch_phase,
        "asin": get(inv, "asin", "ASIN"),
        "daily_sales_estimate": round(daily_sales, 2) if daily_sales is not None else "",
        "fulfillable_qty": round(fulfillable) if fulfillable is not None else "",
        "inbound_qty": round(inbound) if inbound is not None else "",
        "days_of_supply": round(days_of_supply, 1) if days_of_supply is not None else "",
        "total_replenishment_lead_days": round(total_lead_days) if total_lead_days is not None else "",
        "reorder_point_qty": round(reorder_point_qty) if reorder_point_qty is not None else "",
        "recommended_first_shipment_qty": round(first_shipment_qty) if first_shipment_qty is not None else "",
        "estimated_stockout_date": str(stockout_date) if stockout_date else "",
        "status": status,
        "next_action": action,
    }


def next_action(status, days_of_supply, lead_days):
    if status == "blocked":
        return f"expedite replenishment; supply {days_of_supply:.1f} days is below {lead_days:.0f}-day lead time"
    if status == "needs_proof":
        return "add package dimensions, weight, carton, and label proof"
    return "create or confirm FBA shipment plan"


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_checklist(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# FBA Execution Checklist\n\n")
        f.write("- Confirm FNSKU/item labels for every sellable unit.\n")
        f.write("- Confirm carton labels and box content information.\n")
        f.write("- Confirm package dimensions, weight, carton quantity, and carton weight.\n")
        f.write("- Confirm bundle/set labels, suffocation warnings, or fragile handling when relevant.\n")
        f.write("- Save shipment plan proof before handoff to forwarder.\n\n")
        f.write("## SKU Actions\n\n")
        for row in rows:
            f.write(f"- `{row['sku']}` {row['status']}: {row['next_action']}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--package-specs", required=True)
    parser.add_argument("--daily-sales", required=True)
    parser.add_argument("--shipment-proof", help="CSV with sku and four proof file paths")
    parser.add_argument("--gate-decision", required=True)
    parser.add_argument("--seller-decision", required=True)
    parser.add_argument("--output-prefix", default="fba")
    args = parser.parse_args()

    inventory = read_csv(args.inventory)
    if not inventory:
        parser.error("inventory report has no rows")
    specs_by_sku = index_by_sku(read_csv(args.package_specs))
    sales_by_sku = index_by_sku(read_csv(args.daily_sales))
    proof_by_sku = index_by_sku(read_csv(args.shipment_proof))
    if args.shipment_proof:
        proof_dir = Path(args.shipment_proof).resolve().parent
        for proof in proof_by_sku.values():
            for field in PROOF_FIELDS:
                value = get(proof, field)
                if value and not Path(value).is_absolute():
                    proof[field] = str(proof_dir / value)
    rows = []
    for inv in inventory:
        sku = get(inv, "sku", "SKU", "seller_sku")
        if not has_pass(args.gate_decision, sku) or not has_pass(args.seller_decision, sku):
            parser.error(f"Launch Gate and Seller Central must pass for SKU {sku}")
        rows.append(plan_row(inv, specs_by_sku.get(sku, {}), sales_by_sku.get(sku, {}), proof_by_sku.get(sku, {})))

    fields = [
        "sku", "launch_phase", "asin", "daily_sales_estimate", "fulfillable_qty", "inbound_qty",
        "days_of_supply", "total_replenishment_lead_days", "reorder_point_qty",
        "recommended_first_shipment_qty", "estimated_stockout_date", "status", "next_action",
    ]
    write_csv(f"{args.output_prefix}.shipment_plan.csv", rows, fields)
    alerts = [row for row in rows if row["status"] != "pass"]
    write_csv(f"{args.output_prefix}.replenishment_alerts.csv", alerts, fields)
    write_checklist(f"{args.output_prefix}.execution_checklist.md", rows)
    print(f"{args.output_prefix}.shipment_plan.csv")
    print(f"{args.output_prefix}.replenishment_alerts.csv")
    print(f"{args.output_prefix}.execution_checklist.md")


if __name__ == "__main__":
    main()
