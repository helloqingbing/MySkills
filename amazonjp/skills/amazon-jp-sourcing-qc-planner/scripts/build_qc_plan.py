#!/usr/bin/env python3
import argparse
import csv


DEFAULT_QC_CHECKS = [
    ("material_durability", "Material and durability match approved sample"),
    ("size_fit", "Size, fit, dimensions, and weight are within tolerance"),
    ("odor_cleaning", "No unacceptable odor, stain, or cleaning issue"),
    ("accessory_completeness", "All bundle/accessory parts are present"),
    ("packaging_damage", "Packaging protects product through FBA handling"),
    ("instruction_localization", "Japanese instruction or label is clear and accurate"),
    ("claim_proof", "Any listing claim has supplier or test proof"),
]


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_number(value):
    text = str(value or "").replace(",", "").replace("￥", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def get(row, *names):
    for name in names:
        if row.get(name) not in (None, ""):
            return str(row[name]).strip()
    return ""


def supplier_score(row):
    cost = parse_number(get(row, "unit_cost_jpy", "Unit Cost JPY"))
    moq = parse_number(get(row, "moq", "MOQ"))
    lead = parse_number(get(row, "lead_time_days", "Lead Time Days"))
    certs = get(row, "certifications", "Certifications")
    sample = get(row, "sample_status", "Sample Status")
    score = 100
    if cost <= 0:
        score -= 25
    if moq > 1000:
        score -= 10
    if lead > 45:
        score -= 10
    if not certs:
        score -= 15
    if sample.lower() not in {"pass", "approved", "ok"}:
        score -= 20
    decision = "pass" if score >= 75 else "needs_proof" if score >= 50 else "blocked"
    return {
        "candidate_id": get(row, "candidate_id", "Candidate ID"),
        "sku": get(row, "sku", "SKU"),
        "supplier_name": get(row, "supplier_name", "Supplier"),
        "unit_cost_jpy": cost,
        "moq": moq,
        "lead_time_days": lead,
        "certifications": certs,
        "sample_status": sample or "missing",
        "supplier_score": score,
        "decision": decision,
        "next_action": next_supplier_action(decision),
    }


def next_supplier_action(decision):
    if decision == "pass":
        return "request pre-production sample and QC proof pack"
    if decision == "needs_proof":
        return "collect missing sample, certification, MOQ, lead time, or cost proof"
    return "do not advance supplier until economics and sample issues are resolved"


def build_qc_rows(requirements):
    rows = []
    if requirements:
        for req in requirements:
            cluster = get(req, "complaint_cluster", "Complaint Cluster") or "review_pain"
            rows.append({
                "candidate_id": get(req, "candidate_id", "Candidate ID"),
                "sku": get(req, "sku", "SKU"),
                "qc_area": cluster,
                "inspection_item": get(req, "product_action", "Product Action") or cluster,
                "evidence_needed": get(req, "image_brief_hint", "Image Brief Hint") or "photo/video and measured result",
                "acceptance_rule": get(req, "claim_caution", "Claim Caution") or "must match approved sample",
                "status": "needs_proof",
            })
        return rows

    for key, label in DEFAULT_QC_CHECKS:
        rows.append({
            "candidate_id": "",
            "sku": "",
            "qc_area": key,
            "inspection_item": label,
            "evidence_needed": "photo/video and measured result",
            "acceptance_rule": "must match approved sample",
            "status": "needs_proof",
        })
    return rows


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_review(path, supplier_rows, qc_rows):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Sourcing QC Sample Review\n\n")
        f.write("## Supplier Decisions\n\n")
        for row in supplier_rows:
            f.write(f"- `{row['supplier_name'] or row['sku']}` score={row['supplier_score']} decision={row['decision']}: {row['next_action']}\n")
        f.write("\n## QC Evidence Needed\n\n")
        for row in qc_rows[:20]:
            f.write(f"- {row['qc_area']}: {row['inspection_item']} -> {row['evidence_needed']}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suppliers", required=True)
    parser.add_argument("--requirements")
    parser.add_argument("--output-prefix", default="sourcing_qc")
    args = parser.parse_args()

    supplier_rows = [supplier_score(row) for row in read_csv(args.suppliers)]
    qc_rows = build_qc_rows(read_csv(args.requirements))
    write_csv(f"{args.output_prefix}.supplier_scorecard.csv", supplier_rows, [
        "candidate_id", "sku", "supplier_name", "unit_cost_jpy", "moq",
        "lead_time_days", "certifications", "sample_status", "supplier_score",
        "decision", "next_action",
    ])
    write_csv(f"{args.output_prefix}.qc_checklist.csv", qc_rows, [
        "candidate_id", "sku", "qc_area", "inspection_item", "evidence_needed",
        "acceptance_rule", "status",
    ])
    write_review(f"{args.output_prefix}.sample_review.md", supplier_rows, qc_rows)
    print(f"{args.output_prefix}.supplier_scorecard.csv")
    print(f"{args.output_prefix}.qc_checklist.csv")
    print(f"{args.output_prefix}.sample_review.md")


if __name__ == "__main__":
    main()
