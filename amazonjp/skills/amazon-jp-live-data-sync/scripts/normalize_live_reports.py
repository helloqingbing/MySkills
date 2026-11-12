#!/usr/bin/env python3
import argparse
import csv
import os
import re
import hashlib
import math
from datetime import date, datetime


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
REQUIRED_HEADERS = {
    "business_metrics": ("sku", "sessions", "orders", "sales_jpy"),
    "ads_search_terms": ("sku", "search_term", "spend_jpy", "orders", "sales_jpy"),
    "inventory": ("sku", "fulfillable_qty"),
    "returns": ("sku", "return_date", "return_qty"),
    "reviews": ("asin", "review_date", "rating"),
}


def parse_number(value):
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-"}:
        return ""
    try:
        number = float(text)
    except ValueError:
        raise ValueError(f"invalid numeric value: {value}")
    if not math.isfinite(number):
        raise ValueError(f"invalid numeric value: {value}")
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


def normalize_file(kind, path, output_dir, notes, declared_scope=()):
    spec = REPORTS[kind]
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as src:
        reader = csv.DictReader(src)
        missing_headers = []
        for field, aliases in spec["aliases"].items():
            if not any(alias in (reader.fieldnames or []) for alias in aliases):
                missing_headers.append(field)
        critical = set(missing_headers) & set(REQUIRED_HEADERS[kind])
        if critical:
            raise ValueError(f"{kind}: missing required headers {', '.join(sorted(critical))}")
        if missing_headers:
            notes.append(f"- {kind}: optional headers missing: {', '.join(missing_headers)}")
        for row in reader:
            normalized = normalize_row(row, spec, path)
            if any(not normalized[field] for field in REQUIRED_HEADERS[kind]):
                raise ValueError(f"{kind}: required field blank in row {reader.line_num}")
            rows.append(normalized)
    if not rows and kind not in {"returns", "reviews"}:
        raise ValueError(f"{kind}: report has no rows")
    observed_scope = {row["sku"] for row in rows if row.get("sku")}
    declared_scope = set(declared_scope)
    if declared_scope and not observed_scope <= declared_scope:
        raise ValueError(f"{kind}: report contains SKUs outside --sku-scope")
    if kind in {"business_metrics", "inventory"} and declared_scope and not declared_scope <= observed_scope:
        raise ValueError(f"{kind}: report lacks rows for declared SKUs")
    scope = declared_scope or observed_scope
    if not scope:
        raise ValueError(f"{kind}: --sku-scope is required when SKU coverage cannot be inferred")

    out_path = os.path.join(output_dir, f"{kind}.normalized.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=spec["fields"])
        writer.writeheader()
        writer.writerows(rows)
    return out_path, len(rows), scope


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
    parser.add_argument("--report-end", required=True, help="ISO date of latest data covered by this batch")
    parser.add_argument("--period-start", required=True, help="ISO first date covered by this batch")
    parser.add_argument("--exported-at", required=True, help="ISO timestamp when reports were exported")
    parser.add_argument("--max-age-days", type=int, default=14)
    parser.add_argument("--sku-scope", default="", help="comma-separated SKUs covered by every supplied report; required for zero-row returns/reviews and ASIN-only reviews")
    args = parser.parse_args()

    try:
        report_end = date.fromisoformat(args.report_end)
        period_start = date.fromisoformat(args.period_start)
        exported_at = datetime.fromisoformat(args.exported_at)
    except ValueError:
        parser.error("dates must be ISO dates and --exported-at an ISO timestamp")
    if period_start > report_end or exported_at.date() < report_end or exported_at.date() > date.today():
        parser.error("report period or export timestamp is inconsistent")
    age = (date.today() - report_end).days
    if args.max_age_days < 0 or age < 0 or age > args.max_age_days:
        parser.error("report is future-dated or stale; provide a recent report-end date")
    if not any(getattr(args, spec["args"]) for spec in REPORTS.values()):
        parser.error("provide at least one report")

    os.makedirs(args.output_dir, exist_ok=True)
    notes = []
    manifest = []
    declared_scope = {sku.strip() for sku in args.sku_scope.split(",") if sku.strip()}
    for kind, spec in REPORTS.items():
        path = getattr(args, spec["args"])
        if path:
            try:
                out_path, count, scope = normalize_file(kind, path, args.output_dir, notes, declared_scope)
            except ValueError as error:
                parser.error(str(error))
            with open(path, "rb") as src:
                checksum = hashlib.file_digest(src, "sha256").hexdigest()
            with open(out_path, "rb") as normalized:
                normalized_checksum = hashlib.file_digest(normalized, "sha256").hexdigest()
            manifest.append({"report_name": kind, "source_file": os.path.abspath(path),
                             "period_start": args.period_start, "period_end": args.report_end,
                             "exported_at": args.exported_at,
                             "generated_at": datetime.now().isoformat(timespec="seconds"),
                             "freshness": "fresh", "rows": count, "sha256": checksum,
                             "normalized_sha256": normalized_checksum, "sku_scope": ";".join(sorted(scope)),
                             "blocking_gap": "", "normalized_file": os.path.abspath(out_path)})
            print(f"{kind}: {count} rows -> {out_path}")
    manifest_path = os.path.join(args.output_dir, "report_manifest.csv")
    previous = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, newline="", encoding="utf-8") as src:
            previous = {row["report_name"]: row for row in csv.DictReader(src)}
    for row in previous.values():
        try:
            row_age = (date.today() - date.fromisoformat(row["period_end"])).days
            row["freshness"] = "fresh" if 0 <= row_age <= args.max_age_days else "stale"
        except (ValueError, KeyError):
            row["freshness"] = "unknown"
    previous.update({row["report_name"]: row for row in manifest})
    with open(manifest_path, "w", newline="", encoding="utf-8") as dst:
        fields = ["report_name", "source_file", "period_start", "period_end", "exported_at",
                  "generated_at", "freshness", "rows", "sha256", "normalized_sha256",
                  "sku_scope", "blocking_gap", "normalized_file"]
        writer = csv.DictWriter(dst, fieldnames=fields)
        writer.writeheader()
        writer.writerows(previous.values())
    write_quality_note(os.path.join(args.output_dir, "live_data_quality_note.md"), notes)


if __name__ == "__main__":
    main()
