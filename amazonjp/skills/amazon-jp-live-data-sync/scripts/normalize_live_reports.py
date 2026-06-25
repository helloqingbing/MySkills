#!/usr/bin/env python3
import argparse
import csv
import os
import re


REPORTS = {
    "business_metrics": {
        "args": "business",
        "fields": [
            "launch_id", "sku", "parent_asin", "child_asin", "date_range",
            "sessions", "unit_session_pct", "orders", "sales_jpy",
            "buy_box_pct", "source_report",
        ],
        "aliases": {
            "launch_id": ["launch_id", "Launch ID"],
            "sku": ["sku", "SKU", "Seller SKU"],
            "parent_asin": ["parent_asin", "Parent ASIN"],
            "child_asin": ["child_asin", "Child ASIN", "ASIN"],
            "date_range": ["date_range", "Date Range", "期間"],
            "sessions": ["sessions", "Sessions", "セッション"],
            "unit_session_pct": ["unit_session_pct", "Unit Session Percentage", "Unit Session %"],
            "orders": ["orders", "Ordered Product Sales Units", "Units Ordered"],
            "sales_jpy": ["sales_jpy", "Ordered Product Sales", "Sales", "売上"],
            "buy_box_pct": ["buy_box_pct", "Featured Offer Buy Box Percentage", "Buy Box %"],
        },
    },
    "ads_search_terms": {
        "args": "search_terms",
        "fields": [
            "launch_id", "sku", "search_term", "campaign", "match_type",
            "impressions", "clicks", "spend_jpy", "orders", "sales_jpy",
            "acos_pct", "ctr_pct", "cvr_pct", "source_report",
        ],
        "aliases": {
            "launch_id": ["launch_id", "Launch ID"],
            "sku": ["sku", "SKU", "Advertised SKU"],
            "search_term": ["search_term", "Customer Search Term", "Search Term"],
            "campaign": ["campaign", "Campaign Name", "Campaign"],
            "match_type": ["match_type", "Match Type"],
            "impressions": ["impressions", "Impressions"],
            "clicks": ["clicks", "Clicks"],
            "spend_jpy": ["spend_jpy", "Spend", "Cost"],
            "orders": ["orders", "7 Day Total Orders (#)", "Orders"],
            "sales_jpy": ["sales_jpy", "7 Day Total Sales", "Sales"],
            "acos_pct": ["acos_pct", "ACOS", "Advertising Cost of Sales"],
        },
    },
    "inventory": {
        "args": "inventory",
        "fields": [
            "launch_id", "sku", "asin", "fulfillable_qty", "reserved_qty",
            "inbound_qty", "daily_sales_estimate", "days_of_supply",
            "reorder_point_qty", "source_report",
        ],
        "aliases": {
            "launch_id": ["launch_id", "Launch ID"],
            "sku": ["sku", "SKU", "Merchant SKU"],
            "asin": ["asin", "ASIN"],
            "fulfillable_qty": ["fulfillable_qty", "afn-fulfillable-quantity", "Fulfillable Quantity"],
            "reserved_qty": ["reserved_qty", "afn-reserved-quantity", "Reserved Quantity"],
            "inbound_qty": ["inbound_qty", "afn-inbound-working-quantity", "Inbound Quantity"],
            "daily_sales_estimate": ["daily_sales_estimate", "Daily Sales Estimate", "daily_sales"],
            "reorder_point_qty": ["reorder_point_qty", "Reorder Point"],
        },
    },
    "returns": {
        "args": "returns",
        "fields": [
            "launch_id", "sku", "asin", "return_date", "return_qty",
            "return_reason", "refund_jpy", "source_report",
        ],
        "aliases": {
            "launch_id": ["launch_id", "Launch ID"],
            "sku": ["sku", "SKU"],
            "asin": ["asin", "ASIN"],
            "return_date": ["return_date", "Return Date", "Date"],
            "return_qty": ["return_qty", "Quantity", "Return Quantity"],
            "return_reason": ["return_reason", "Reason", "Return Reason"],
            "refund_jpy": ["refund_jpy", "Refund", "Refund Amount"],
        },
    },
    "reviews": {
        "args": "reviews",
        "fields": [
            "launch_id", "sku", "asin", "review_date", "rating",
            "review_title", "review_text", "source_report",
        ],
        "aliases": {
            "launch_id": ["launch_id", "Launch ID"],
            "sku": ["sku", "SKU"],
            "asin": ["asin", "ASIN"],
            "review_date": ["review_date", "Review Date", "Date"],
            "rating": ["rating", "Rating", "Stars"],
            "review_title": ["review_title", "Review Title", "Title"],
            "review_text": ["review_text", "Review Text", "Body", "Review"],
        },
    },
}


NUMERIC_SUFFIXES = ("_jpy", "_qty", "_pct")
NUMERIC_FIELDS = {
    "sessions", "orders", "impressions", "clicks", "sales_jpy", "spend_jpy",
    "fulfillable_qty", "reserved_qty", "inbound_qty", "daily_sales_estimate",
    "days_of_supply", "reorder_point_qty", "return_qty", "refund_jpy", "rating",
}


def parse_number(value):
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-"}:
        return ""
    return text


def first_value(row, aliases):
    for name in aliases:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return ""


def normalize_row(row, spec, source_path):
    normalized = {}
    for field in spec["fields"]:
        if field == "source_report":
            normalized[field] = os.path.basename(source_path)
            continue
        value = first_value(row, spec["aliases"].get(field, [field]))
        if field in NUMERIC_FIELDS or field.endswith(NUMERIC_SUFFIXES):
            value = parse_number(value)
        normalized[field] = str(value or "").strip()

    if "ctr_pct" in normalized and not normalized["ctr_pct"]:
        clicks = float(normalized.get("clicks") or 0)
        impressions = float(normalized.get("impressions") or 0)
        normalized["ctr_pct"] = f"{clicks / impressions * 100:.2f}" if impressions else ""
    if "cvr_pct" in normalized and not normalized["cvr_pct"]:
        orders = float(normalized.get("orders") or 0)
        clicks = float(normalized.get("clicks") or 0)
        normalized["cvr_pct"] = f"{orders / clicks * 100:.2f}" if clicks else ""
    if "days_of_supply" in normalized and not normalized["days_of_supply"]:
        qty = float(normalized.get("fulfillable_qty") or 0)
        daily = float(normalized.get("daily_sales_estimate") or 0)
        normalized["days_of_supply"] = f"{qty / daily:.1f}" if daily else ""
    return normalized


def normalize_file(kind, path, output_dir, notes):
    spec = REPORTS[kind]
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as src:
        reader = csv.DictReader(src)
        missing_headers = []
        for field, aliases in spec["aliases"].items():
            if not any(alias in (reader.fieldnames or []) for alias in aliases):
                missing_headers.append(field)
        if missing_headers:
            notes.append(f"- {kind}: missing headers for {', '.join(missing_headers)}")
        for row in reader:
            rows.append(normalize_row(row, spec, path))

    out_path = os.path.join(output_dir, f"{kind}.normalized.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=spec["fields"])
        writer.writeheader()
        writer.writerows(rows)
    return out_path, len(rows)


def write_quality_note(path, notes):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Live Data Quality Note\n\n")
        if notes:
            f.write("\n".join(notes))
            f.write("\n")
        else:
            f.write("- All provided reports were normalized without header gaps.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--business")
    parser.add_argument("--search-terms")
    parser.add_argument("--inventory")
    parser.add_argument("--returns")
    parser.add_argument("--reviews")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    notes = []
    for kind, spec in REPORTS.items():
        path = getattr(args, spec["args"])
        if path:
            out_path, count = normalize_file(kind, path, args.output_dir, notes)
            print(f"{kind}: {count} rows -> {out_path}")
    write_quality_note(os.path.join(args.output_dir, "live_data_quality_note.md"), notes)


if __name__ == "__main__":
    main()
