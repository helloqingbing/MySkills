#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


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


def has_gate_pass(path, sku):
    rows = read_csv(path)
    return sum(row.get("sku") == sku and row.get("decision") == "pass" for row in rows) == 1


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
    if any(str(row.get("status", "")).lower() != "pass" for row in relevant):
        return "needs_proof"
    return "pass"


def build_rows(listing_rows, evidence_rows):
    source = listing_rows[0] if listing_rows else {}
    rows = []
    for area, field, label in REQUIRED_FIELDS:
        value = get(source, field)
        status = "pass" if value or (field == "variation_theme" and not get(source, "parent_asin")) else "needs_proof"
        if area == "compliance":
            control_area = "import" if field == "country_of_origin" else "claim"
            status = evidence_status(evidence_rows, control_area)
            if not value and status == "pass":
                status = "needs_proof"
        rows.append({
            "sku": get(source, "sku"),
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


def build_ops_rows(checklist_rows, proof_rows):
    proof_by_field = {(get(row, "sku"), get(row, "field")): row for row in proof_rows}
    proof_paths = [str(Path(get(row, "evidence_file")).resolve()) for row in proof_rows if get(row, "evidence_file")]
    repeated_paths = {path for path in proof_paths if proof_paths.count(path) > 1}
    ops_rows = []
    for row in checklist_rows:
        proof = proof_by_field.get((row["sku"], row["field"]), {})
        proof_path = get(proof, "evidence_file")
        proof_valid = (get(proof, "status").lower() == "done" and bool(get(proof, "owner"))
                       and bool(proof_path) and Path(proof_path).suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".csv"}
                       and str(Path(proof_path).resolve()) not in repeated_paths
                       and Path(proof_path).is_file() and Path(proof_path).stat().st_size > 0)
        ops_rows.append({"sku": row["sku"], "field": row["field"],
                         "owner": get(proof, "owner") or row["owner"],
                         "action": row["next_action"],
                         "expected_proof": "Seller Central screenshot or uploaded flat-file row",
                         "evidence_file": proof_path,
                         "status": "blocked" if row["status"] == "blocked" else
                         "needs_proof" if row["status"] != "pass" or not proof_valid else "done"})
    return ops_rows


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
    parser.add_argument("--gate-decision", required=True, help="Launch Gate decision CSV")
    parser.add_argument("--ops-proof", help="CSV with sku,field,evidence_file,owner,status=done")
    parser.add_argument("--output-prefix", default="seller_central")
    args = parser.parse_args()

    listing_rows = read_csv(args.listing)
    if len(listing_rows) != 1 or not get(listing_rows[0], "sku"):
        parser.error("listing must contain exactly one row with SKU")
    if not has_gate_pass(args.gate_decision, get(listing_rows[0], "sku")):
        parser.error("Launch Gate must pass for this SKU")
    evidence_rows = read_csv(args.evidence)
    evidence_rows = [row for row in evidence_rows if get(row, "sku") == get(listing_rows[0], "sku")]
    rows = build_rows(listing_rows, evidence_rows)
    proof_rows = read_csv(args.ops_proof)
    if args.ops_proof:
        proof_dir = Path(args.ops_proof).resolve().parent
        for proof in proof_rows:
            value = get(proof, "evidence_file")
            if value and not Path(value).is_absolute():
                proof["evidence_file"] = str(proof_dir / value)

    write_csv(f"{args.output_prefix}.checklist.csv", rows, [
        "sku", "area", "field", "label", "value_present", "status", "owner", "next_action",
    ])
    ops_rows = build_ops_rows(rows, proof_rows)
    final_decision = decision(rows)
    if final_decision == "pass" and any(row["status"] != "done" for row in ops_rows):
        final_decision = "needs_proof"
    write_csv(f"{args.output_prefix}.ops_log.csv", ops_rows, [
        "sku", "field", "owner", "action", "expected_proof", "evidence_file", "status",
    ])
    write_report(f"{args.output_prefix}.readiness.md", rows, final_decision)
    write_csv(f"{args.output_prefix}.decision.csv", [{"sku": get(listing_rows[0], "sku"),
                                                  "decision": final_decision}], ["sku", "decision"])
    print(f"{args.output_prefix}.checklist.csv")
    print(f"{args.output_prefix}.ops_log.csv")
    print(f"{args.output_prefix}.readiness.md")
    print(f"{args.output_prefix}.decision.csv")


if __name__ == "__main__":
    main()
