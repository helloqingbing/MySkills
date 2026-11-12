#!/usr/bin/env python3
import argparse
import csv
import math
from collections import Counter
from collections import defaultdict
from datetime import date
from pathlib import Path

REQUIRED_CONTROLS = {"AMZ-JP-CAT-01", "GTIN-ASIN-01", "IP-JP-01", "JP-LABEL-CERT-01", "JP-IMPORT-FBA-01", "SUPPLIER-QC-01", "CLAIMS-JP-01", "ECON-JP-01"}


MAJOR_COST_FIELDS = [
    "selling_price_jpy",
    "unit_cost_jpy",
    "international_freight_jpy",
    "duty_tax_jpy",
    "fba_fee_jpy",
    "referral_fee_jpy",
]

OPTIONAL_COST_FIELDS = [
    "inspection_packaging_jpy",
    "first_mile_jpy",
    "storage_return_allowance_jpy",
    "ad_allowance_jpy",
]


def parse_number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(str(value).replace(",", "").replace("￥", "").strip())
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get(row, name):
    return (row.get(name) or "").strip()


def evaluate_cost(row, min_margin_pct):
    missing = [field for field in MAJOR_COST_FIELDS if parse_number(row.get(field)) is None]
    missing += [field for field in OPTIONAL_COST_FIELDS if get(row, field) and parse_number(row.get(field)) is None]
    missing += [field for field in MAJOR_COST_FIELDS + OPTIONAL_COST_FIELDS if parse_number(row.get(field)) is not None and parse_number(row.get(field)) < 0]
    if parse_number(row.get("selling_price_jpy")) == 0:
        missing.append("selling_price_jpy must be positive")
    if missing:
        return {
            "sku": get(row, "sku"),
            "candidate_id": get(row, "candidate_id"),
            "decision": "blocked",
            "reason": f"invalid cost fields: {', '.join(sorted(set(missing)))}",
        }

    selling_price = parse_number(row.get("selling_price_jpy")) or 0.0
    costs = 0.0
    for field in MAJOR_COST_FIELDS:
        if field != "selling_price_jpy":
            costs += parse_number(row.get(field)) or 0.0
    for field in OPTIONAL_COST_FIELDS:
        costs += parse_number(row.get(field)) or 0.0

    gross_profit = selling_price - costs
    margin_pct = (gross_profit / selling_price * 100.0) if selling_price else 0.0
    decision = "pass" if margin_pct >= min_margin_pct else "blocked"
    reason = (
        f"gross margin {margin_pct:.1f}% >= {min_margin_pct:.1f}%"
        if decision == "pass"
        else f"gross margin {margin_pct:.1f}% below {min_margin_pct:.1f}%"
    )
    return {
        "candidate_id": get(row, "candidate_id"),
        "sku": get(row, "sku"),
        "selling_price_jpy": round(selling_price, 2),
        "landed_cost_jpy": round(costs, 2),
        "gross_profit_jpy": round(gross_profit, 2),
        "gross_margin_pct": round(margin_pct, 2),
        "break_even_acos_pct": round(max(gross_profit, 0.0) / selling_price * 100.0, 2) if selling_price else 0.0,
        "decision": decision,
        "reason": reason,
    }


def valid_proof(value, evidence_root):
    if "://" in value:
        return False
    path = Path(value)
    if not path.is_absolute():
        path = Path(evidence_root) / path
    return path.is_file() and path.stat().st_size > 0


def evaluate_sku(sku, evidence, costs, min_margin_pct, evidence_root="."):
    """Evaluate a single SKU; omitted and malformed controls fail closed."""
    blocked, needs = [], []
    if not sku:
        needs.append("missing SKU")
    by_ref = defaultdict(list)
    for row in evidence:
        by_ref[get(row, "control_ref")].append(row)
    for ref in sorted(REQUIRED_CONTROLS):
        rows = by_ref[ref]
        blocked.extend(f"{ref}: {get(row, 'blocking_reason') or 'blocked'}"
                       for row in rows if get(row, "status").lower() == "blocked")
        if len(rows) != 1:
            needs.append(f"{ref}: expected one row, got {len(rows)}")
            continue
        row = rows[0]
        status = get(row, "status").lower()
        if status == "needs_proof":
            needs.append(f"{ref}: needs proof")
        elif status not in {"pass", "not_applicable", "blocked"}:
            needs.append(f"{ref}: invalid status {status or '<blank>'}")
        if status in {"pass", "not_applicable"}:
            for field in ("owner", "evidence", "evidence_source", "evidence_date"):
                if not get(row, field):
                    needs.append(f"{ref}: missing {field}")
            try:
                proof_date = date.fromisoformat(get(row, "evidence_date"))
                if proof_date > date.today():
                    needs.append(f"{ref}: evidence_date is in the future")
            except ValueError:
                needs.append(f"{ref}: invalid evidence_date")
            if get(row, "evidence") and not valid_proof(get(row, "evidence"), evidence_root):
                needs.append(f"{ref}: local evidence snapshot is missing or empty")
            if status == "not_applicable" and not get(row, "blocking_reason"):
                needs.append(f"{ref}: not_applicable requires a reason")
            if status == "not_applicable" and ref not in {"JP-LABEL-CERT-01", "CLAIMS-JP-01"}:
                needs.append(f"{ref}: cannot be not_applicable")
    for ref in set(by_ref) - REQUIRED_CONTROLS:
        needs.append(f"unknown control {ref or '<blank>'}")
        blocked.extend(f"{ref or '<blank>'}: blocked" for row in by_ref[ref]
                       if get(row, "status").lower() == "blocked")
    economics = [evaluate_cost(row, min_margin_pct) for row in costs]
    if len(economics) != 1:
        needs.append(f"cost model: expected one row, got {len(economics)}")
    blocked += [row["reason"] for row in economics if row["decision"] == "blocked"]
    statuses = Counter(get(row, "status").lower() for row in evidence)
    decision = "blocked" if blocked else "needs_proof" if needs else "pass"
    return {"sku": sku, "candidate_id": get(costs[0], "candidate_id") if costs else "",
            "decision": decision, "evidence_statuses": ";".join(f"{k}:{v}" for k, v in sorted(statuses.items())),
            "blocked_controls": len(blocked), "needs_proof_controls": len(needs),
            "cost_rows": len(economics), "reasons": "; ".join(blocked + needs), "economics": economics}


def evaluate_all(evidence, costs, min_margin_pct, evidence_root="."):
    by_sku_evidence, by_sku_cost = defaultdict(list), defaultdict(list)
    for row in evidence:
        by_sku_evidence[get(row, "sku")].append(row)
    for row in costs:
        by_sku_cost[get(row, "sku")].append(row)
    skus = sorted(set(by_sku_evidence) | set(by_sku_cost)) or [""]
    return [evaluate_sku(sku, by_sku_evidence[sku], by_sku_cost[sku], min_margin_pct, evidence_root) for sku in skus]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--costs", required=True)
    parser.add_argument("--min-margin-pct", type=float, default=35.0)
    parser.add_argument("--output-prefix", default="launch_gate")
    args = parser.parse_args()

    evidence = read_csv(args.evidence)
    costs = read_csv(args.costs)
    results = evaluate_all(evidence, costs, args.min_margin_pct, Path(args.evidence).resolve().parent)
    with open(f"{args.output_prefix}.decision.csv", "w", newline="", encoding="utf-8") as f:
        fields = ["sku", "candidate_id", "decision", "evidence_statuses", "blocked_controls", "needs_proof_controls", "cost_rows", "reasons"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: result[field] for field in fields} for result in results)
    with open(f"{args.output_prefix}.report.md", "w", encoding="utf-8") as f:
        f.write("# Amazon JP Launch Gate Report\n\n")
        for result in results:
            f.write(f"## SKU {result['sku'] or '<missing>'}: {result['decision']}\n\n")
            f.write(f"- Reasons: {result['reasons'] or 'all required controls passed'}\n")
            for cost in result["economics"]:
                f.write(f"- Economics: {cost['decision']}; {cost['reason']}\n")
    print(f"{args.output_prefix}.decision.csv")
    print(f"{args.output_prefix}.report.md")


if __name__ == "__main__":
    main()
