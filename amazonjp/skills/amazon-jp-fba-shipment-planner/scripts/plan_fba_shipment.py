#!/usr/bin/env python3
import argparse
import csv
from datetime import date, timedelta


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_number(value, default=0.0):
    text = str(value or "").replace(",", "").replace("￥", "").strip()
    if not text:
        return default
    try:
        return float(text)
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


def plan_row(inv, specs, sales):
    sku = get(inv, "sku", "SKU", "seller_sku")
    daily_sales = parse_number(get(sales, "daily_sales_estimate", "daily_sales", "Daily Sales Estimate"), 1.0)
    fulfillable = parse_number(get(inv, "fulfillable_qty", "afn-fulfillable-quantity", "Fulfillable Quantity"))
    inbound = parse_number(get(inv, "inbound_qty", "afn-inbound-working-quantity", "Inbound Quantity"))
    production_days = parse_number(get(specs, "production_lead_time_days", "Production Lead Time Days"), 20)
    freight_days = parse_number(get(specs, "freight_lead_time_days", "Freight Lead Time Days"), 14)
    fba_buffer_days = parse_number(get(specs, "fba_receiving_buffer_days", "FBA Receiving Buffer Days"), 7)
    safety_days = parse_number(get(specs, "safety_stock_days", "Safety Stock Days"), 14)
    target_days = parse_number(get(specs, "target_days_of_supply", "Target Days of Supply"), 60)
    total_lead_days = production_days + freight_days + fba_buffer_days
    days_of_supply = (fulfillable + inbound) / daily_sales if daily_sales else 0
    reorder_point_qty = daily_sales * (total_lead_days + safety_days)
    first_shipment_qty = max(0, daily_sales * target_days - inbound)
    stockout_date = date.today() + timedelta(days=int(days_of_supply)) if days_of_supply else ""
    status = "pass"
    if not get(specs, "package_weight_g", "Package Weight g") or not get(specs, "package_length_cm", "Package Length cm"):
        status = "needs_proof"
    if days_of_supply < total_lead_days:
        status = "blocked"
    return {
        "sku": sku,
        "asin": get(inv, "asin", "ASIN"),
        "daily_sales_estimate": round(daily_sales, 2),
        "fulfillable_qty": round(fulfillable),
        "inbound_qty": round(inbound),
        "days_of_supply": round(days_of_supply, 1),
        "total_replenishment_lead_days": round(total_lead_days),
        "reorder_point_qty": round(reorder_point_qty),
        "recommended_first_shipment_qty": round(first_shipment_qty),
        "estimated_stockout_date": str(stockout_date),
        "status": status,
        "next_action": next_action(status, days_of_supply, total_lead_days),
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
    parser.add_argument("--daily-sales")
    parser.add_argument("--output-prefix", default="fba")
    args = parser.parse_args()

    inventory = read_csv(args.inventory)
    specs_by_sku = index_by_sku(read_csv(args.package_specs))
    sales_by_sku = index_by_sku(read_csv(args.daily_sales))
    rows = []
    for inv in inventory:
        sku = get(inv, "sku", "SKU", "seller_sku")
        rows.append(plan_row(inv, specs_by_sku.get(sku, {}), sales_by_sku.get(sku, {})))

    fields = [
        "sku", "asin", "daily_sales_estimate", "fulfillable_qty", "inbound_qty",
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
