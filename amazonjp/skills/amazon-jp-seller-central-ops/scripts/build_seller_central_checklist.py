#!/usr/bin/env python3
import argparse
import csv


REQUIRED_FIELDS = [
    ("identity", "sku", "Seller SKU"),
    ("identity", "brand", "Brand name"),
    ("identity", "product_type", "Product type"),
    ("identity", "category", "Category or browse node"),
    ("identity", "jan_gtin_status", "JAN/GTIN or exemption status"),
    ("variation", "variation_theme", "Variation theme when parent/child is used"),
    ("content", "title", "Japanese title"),
    ("content", "bullet_1", "Bullet 1"),
    ("content", "bullet_2", "Bullet 2"),
    ("content", "bullet_3", "Bullet 3"),
    ("content", "bullet_4", "Bullet 4"),
    ("content", "bullet_5", "Bullet 5"),
    ("content", "backend_search_terms", "Backend search terms"),
    ("media", "main_image", "Main image"),
    ("media", "image_set", "Image set"),
    ("offer", "price_jpy", "Offer price"),
    ("offer", "fulfillment_channel", "FBA or FBM"),
    ("compliance", "country_of_origin", "Country of origin"),
    ("compliance", "claim_ledger_status", "Claim ledger status"),
]


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get(row, field):
    return str(row.get(field) or "").strip()


def evidence_status(evidence_rows, area):
    relevant = [
        row for row in evidence_rows
        if area in str(row.get("control_area", "")).lower()
        or area in str(row.get("requirement", "")).lower()
    ]
    if not relevant:
        return "needs_proof"
    if any(str(row.get("status", "")).lower() == "blocked" for row in relevant):
        return "blocked"
    if any(str(row.get("status", "")).lower() in {"", "needs_proof", "pending"} for row in relevant):
        return "needs_proof"
    return "pass"


def build_rows(listing_rows, evidence_rows):
    source = listing_rows[0] if listing_rows else {}
    rows = []
    for area, field, label in REQUIRED_FIELDS:
        value = get(source, field)
        status = "pass" if value else "needs_proof"
        if area == "compliance":
            status = evidence_status(evidence_rows, field.replace("_status", ""))
        rows.append({
            "area": area,
            "field": field,
            "label": label,
            "value_present": "yes" if value else "no",
            "status": status,
            "owner": get(source, "owner") or "operator",
            "next_action": "ready" if status == "pass" else f"provide {label}",
        })
    return rows


def decision(rows):
    if any(row["status"] == "blocked" for row in rows):
        return "blocked"
    if any(row["status"] == "needs_proof" for row in rows):
        return "needs_proof"
    return "pass"


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path, rows, final_decision):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Seller Central Readiness\n\n")
        f.write(f"Decision: `{final_decision}`\n\n")
        for row in rows:
            if row["status"] != "pass":
                f.write(f"- {row['area']} / {row['field']}: {row['next_action']}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listing", required=True)
    parser.add_argument("--evidence")
    parser.add_argument("--output-prefix", default="seller_central")
    args = parser.parse_args()

    listing_rows = read_csv(args.listing)
    evidence_rows = read_csv(args.evidence)
    rows = build_rows(listing_rows, evidence_rows)
    final_decision = decision(rows)

    write_csv(f"{args.output_prefix}.checklist.csv", rows, [
        "area", "field", "label", "value_present", "status", "owner", "next_action",
    ])
    ops_rows = [
        {
            "owner": row["owner"],
            "action": row["next_action"],
            "expected_proof": "Seller Central screenshot or uploaded flat-file row",
            "status": "todo" if row["status"] != "pass" else "ready",
        }
        for row in rows
    ]
    write_csv(f"{args.output_prefix}.ops_log.csv", ops_rows, [
        "owner", "action", "expected_proof", "status",
    ])
    write_report(f"{args.output_prefix}.readiness.md", rows, final_decision)
    print(f"{args.output_prefix}.checklist.csv")
    print(f"{args.output_prefix}.ops_log.csv")
    print(f"{args.output_prefix}.readiness.md")


if __name__ == "__main__":
    main()
