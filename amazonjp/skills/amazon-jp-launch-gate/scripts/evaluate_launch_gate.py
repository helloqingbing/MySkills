#!/usr/bin/env python3
import argparse
import csv
from collections import Counter


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
        return float(str(value).replace(",", "").replace("￥", "").strip())
    except ValueError:
        return None


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def get(row, name):
    return (row.get(name) or "").strip()


def evaluate_evidence(rows):
    statuses = Counter((get(row, "status") or "needs_proof").lower() for row in rows)
    blocked = [row for row in rows if (get(row, "status").lower() == "blocked")]
    needs = [
        row for row in rows
        if (get(row, "status").lower() in {"", "needs_proof", "pending", "unknown"})
    ]
    return statuses, blocked, needs


def evaluate_cost(row, min_margin_pct):
    missing = [field for field in MAJOR_COST_FIELDS if parse_number(row.get(field)) is None]
    if missing:
        return {
            "decision": "blocked",
            "reason": f"missing major cost fields: {', '.join(missing)}",
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


def final_decision(blocked_controls, needs_controls, cost_results):
    if blocked_controls:
        return "blocked"
    if any(row["decision"] == "blocked" for row in cost_results):
        return "blocked"
    if needs_controls:
        return "needs_proof"
    if not cost_results:
        return "needs_proof"
    return "pass"


def write_decision_csv(path, decision, statuses, blocked, needs, cost_results):
    rows = [{
        "decision": decision,
        "evidence_statuses": ";".join(f"{k}:{v}" for k, v in sorted(statuses.items())),
        "blocked_controls": len(blocked),
        "needs_proof_controls": len(needs),
        "cost_rows": len(cost_results),
    }]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path, decision, statuses, blocked, needs, cost_results):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Amazon JP Launch Gate Report\n\n")
        f.write(f"Final decision: `{decision}`\n\n")
        f.write("## Evidence Status\n\n")
        for status, count in sorted(statuses.items()):
            f.write(f"- {status}: {count}\n")
        if blocked:
            f.write("\n## Blocked Controls\n\n")
            for row in blocked:
                f.write(f"- `{get(row, 'control_ref')}` {get(row, 'requirement')}: {get(row, 'blocking_reason') or 'blocked'}\n")
        if needs:
            f.write("\n## Needs Proof\n\n")
            for row in needs[:20]:
                f.write(f"- `{get(row, 'control_ref')}` {get(row, 'requirement')} owner={get(row, 'owner') or '-'}\n")
        f.write("\n## Economics\n\n")
        if cost_results:
            f.write("| Candidate | SKU | Price | Landed Cost | Gross Margin | Break-even ACOS | Decision | Reason |\n")
            f.write("|---|---|---:|---:|---:|---:|---|---|\n")
            for row in cost_results:
                f.write(
                    f"| {row.get('candidate_id', '')} | {row.get('sku', '')} | "
                    f"{row.get('selling_price_jpy', '')} | {row.get('landed_cost_jpy', '')} | "
                    f"{row.get('gross_margin_pct', '')}% | {row.get('break_even_acos_pct', '')}% | "
                    f"{row['decision']} | {row['reason']} |\n"
                )
        else:
            f.write("- No landed cost rows provided.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--costs")
    parser.add_argument("--min-margin-pct", type=float, default=35.0)
    parser.add_argument("--output-prefix", default="launch_gate")
    args = parser.parse_args()

    evidence = read_csv(args.evidence)
    costs = read_csv(args.costs)
    statuses, blocked, needs = evaluate_evidence(evidence)
    cost_results = [evaluate_cost(row, args.min_margin_pct) for row in costs]
    decision = final_decision(blocked, needs, cost_results)

    write_decision_csv(f"{args.output_prefix}.decision.csv", decision, statuses, blocked, needs, cost_results)
    write_report(f"{args.output_prefix}.report.md", decision, statuses, blocked, needs, cost_results)
    print(f"{args.output_prefix}.decision.csv")
    print(f"{args.output_prefix}.report.md")


if __name__ == "__main__":
    main()
