#!/usr/bin/env python3
import argparse
import csv
import hashlib
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_number(value):
    text = str(value or "").replace(",", "").replace("%", "").replace("￥", "").strip()
    if not text:
        return None
    try:
        number = float(text)
        return number if math.isfinite(number) else None
    except ValueError:
        return None


def get(row, *names):
    for name in names:
        if row.get(name) not in (None, ""):
            return str(row[name]).strip()
    return ""


def review_metric_row(row, max_age_days=14, today=None):
    launch_id = get(row, "launch_id", "Launch ID")
    sku = get(row, "sku", "SKU")
    acos = parse_number(get(row, "acos_pct", "ACOS"))
    tacos = parse_number(get(row, "tacos_pct", "TACOS"))
    break_even = parse_number(get(row, "break_even_acos_pct", "Break-even ACOS"))
    cvr = parse_number(get(row, "unit_session_pct", "Unit Session %", "cvr_pct"))
    rating = parse_number(get(row, "rating", "Rating"))
    returns = parse_number(get(row, "returns", "Returns"))
    inventory_days = parse_number(get(row, "days_of_supply", "Days of Supply"))
    sessions = parse_number(get(row, "sessions", "Sessions"))
    orders = parse_number(get(row, "orders", "Orders"))
    sales = parse_number(get(row, "sales_jpy", "Sales"))
    ad_spend = parse_number(get(row, "ad_spend_jpy", "Ad Spend"))
    week_start = get(row, "week_start", "Week Start")
    missing = [name for name, value in (("sku", sku), ("week_start", week_start),
               ("sessions", sessions), ("orders", orders), ("sales_jpy", sales),
               ("ad_spend_jpy", ad_spend), ("acos_pct", acos), ("tacos_pct", tacos),
               ("break_even_acos_pct", break_even), ("unit_session_pct", cvr),
               ("rating", rating), ("returns", returns), ("days_of_supply", inventory_days))
               if value is None or value == ""]
    invalid = [name for name, value in (("sessions", sessions), ("orders", orders),
               ("sales_jpy", sales), ("ad_spend_jpy", ad_spend), ("acos_pct", acos),
               ("tacos_pct", tacos), ("break_even_acos_pct", break_even),
               ("unit_session_pct", cvr), ("rating", rating), ("returns", returns),
               ("days_of_supply", inventory_days)) if value is not None and value < 0]
    if rating is not None and rating > 5:
        invalid.append("rating")
    if cvr is not None and cvr > 100:
        invalid.append("unit_session_pct")
    if invalid:
        missing.append("invalid metrics: " + ", ".join(sorted(set(invalid))))
    if week_start:
        try:
            start = date.fromisoformat(week_start)
            age = ((today or date.today()) - start).days
            if age < 6 or age > max_age_days:
                missing.append("complete recent 7-day window")
        except ValueError:
            missing.append("valid week_start")
    if sessions is not None and sessions <= 0 or orders is not None and orders <= 0 or sales is not None and sales <= 0 or ad_spend is not None and ad_spend <= 0:
        missing.append("positive sessions, orders, sales and ad spend")
    actions = []

    if acos is not None and break_even is not None and acos > break_even:
        actions.append(("ads", "reduce_bid_or_add_negatives", f"ACOS {acos:.1f}% above break-even {break_even:.1f}%"))
    if tacos is not None and tacos > 35:
        actions.append(("profit", "check_price_margin_and_budget", f"TACOS {tacos:.1f}% is high"))
    if cvr is not None and cvr < 5:
        actions.append(("listing", "review_price_images_reviews", f"conversion {cvr:.1f}% is weak"))
    if inventory_days is not None and inventory_days < 21:
        actions.append(("fba", "trigger_replenishment", f"inventory {inventory_days:.1f} days"))
    if rating is not None and rating < 4.2:
        actions.append(("product", "run_review_mining_and_pause_scale", f"rating {rating:.1f} below 4.2"))
    if returns is not None and returns >= 3:
        actions.append(("qc", "inspect_return_reasons", f"returns count {returns:.0f}"))
    if missing:
        actions.append(("data", "needs_proof", "missing or stale: " + ", ".join(sorted(set(missing)))))
    elif not actions:
        actions.append(("growth", "watch_or_scale_carefully", "complete recent metrics within thresholds"))

    return [
        {
            "launch_id": launch_id,
            "sku": sku,
            "area": area,
            "action": action,
            "reason": reason,
            "owner": owner_for(area),
            "status": "todo",
        }
        for area, action, reason in actions
    ]


def owner_for(area):
    return {
        "ads": "ads",
        "profit": "operator",
        "listing": "content",
        "fba": "operations",
        "product": "product",
        "qc": "sourcing",
        "growth": "operator",
        "data": "operator",
    }.get(area, "operator")


def search_term_actions(rows):
    actions = []
    for row in rows:
        spend = parse_number(get(row, "spend_jpy", "Spend"))
        orders = parse_number(get(row, "orders", "Orders"))
        sales = parse_number(get(row, "sales_jpy", "Sales"))
        clicks = parse_number(get(row, "clicks", "Clicks"))
        acos = parse_number(get(row, "acos_pct", "ACOS"))
        term = get(row, "search_term", "Customer Search Term", "Search Term")
        action = ""
        reason = ""
        if spend is not None and orders == 0 and spend >= 1500:
            action = "negate_or_reduce_bid"
            reason = "spent at least 1500 JPY with no orders"
        elif orders is not None and orders >= 2 and acos is not None and acos <= 30 and sales is not None and sales > 0:
            action = "promote_exact"
            reason = "orders with efficient ACOS"
        elif clicks is not None and clicks >= 20 and orders == 0:
            action = "check_relevance_or_listing"
            reason = "click volume without conversion"
        if action:
            actions.append({
                "launch_id": get(row, "launch_id", "Launch ID"),
                "sku": get(row, "sku", "SKU"),
                "search_term": term,
                "action": action,
                "reason": reason,
                "sales_jpy": sales,
            })
    return actions


def inventory_actions(rows):
    actions = []
    for row in rows:
        days = parse_number(get(row, "days_of_supply", "Days of Supply"))
        sku = get(row, "sku", "SKU", "seller_sku")
        if days is not None and days < 21:
            actions.append({
                "launch_id": get(row, "launch_id", "Launch ID"),
                "sku": sku,
                "area": "fba",
                "action": "trigger_replenishment",
                "reason": f"inventory {days:.1f} days below 21-day threshold",
                "owner": "operations",
                "status": "todo",
            })
    return actions


def return_actions(rows):
    totals = {}
    reasons = {}
    for row in rows:
        sku = get(row, "sku", "SKU")
        if not sku:
            continue
        qty = parse_number(get(row, "return_qty", "Quantity"))
        if qty is None or qty < 0:
            continue
        totals[sku] = totals.get(sku, 0.0) + qty
        reason = get(row, "return_reason", "Reason", "Return Reason")
        if reason:
            reasons.setdefault(sku, set()).add(reason)

    actions = []
    for sku, qty in sorted(totals.items()):
        if qty >= 3:
            reason_text = ", ".join(sorted(reasons.get(sku, []))) or "return reasons not classified"
            actions.append({
                "launch_id": "",
                "sku": sku,
                "area": "qc",
                "action": "inspect_return_reasons",
                "reason": f"{qty:.0f} returns; reasons: {reason_text}",
                "owner": "sourcing",
                "status": "todo",
            })
    return actions


def final_decision(actions):
    action_names = {row["action"] for row in actions}
    if "run_review_mining_and_pause_scale" in action_names:
        return "pause"
    if not actions or "needs_proof" in action_names:
        return "needs_proof"
    if "trigger_replenishment" in action_names:
        return "optimize"
    if "reduce_bid_or_add_negatives" in action_names:
        return "optimize"
    if action_names == {"watch_or_scale_carefully"}:
        return "scale"
    return "watch"


def manifest_issues(rows, max_age_days, today=None, sku=""):
    required = {"business_metrics", "ads_search_terms", "inventory", "returns", "reviews"}
    by_name = {row.get("report_name", ""): row for row in rows}
    issues = [f"missing report {name}" for name in sorted(required - set(by_name))]
    if len(by_name) != len(rows):
        issues.append("duplicate report manifest entries")
    for name in sorted(required & set(by_name)):
        row = by_name[name]
        scope = {item.strip() for item in row.get("sku_scope", "").split(";") if item.strip()}
        if not scope or sku and sku not in scope:
            issues.append(f"SKU {sku or '<unknown>'} is outside report {name} scope")
        try:
            period_end = date.fromisoformat(row.get("period_end", ""))
            period_start = date.fromisoformat(row.get("period_start", ""))
            exported_at = date.fromisoformat(row.get("exported_at", "")[:10])
            age = ((today or date.today()) - period_end).days
            if period_start > period_end or exported_at < period_end:
                age = max_age_days + 1
        except ValueError:
            age = max_age_days + 1
        if age < 0 or age > max_age_days or row.get("freshness") != "fresh" or row.get("blocking_gap"):
            issues.append(f"stale or blocked report {name}")
        count = row.get("rows", "")
        normalized_path = Path(row.get("normalized_file") or "")
        source_path = Path(row.get("source_file") or "")
        valid_count = count.isdigit() and (int(count) > 0 or name in {"returns", "reviews"} and int(count) == 0)
        try:
            with normalized_path.open("rb") as f:
                normalized_hash = hashlib.file_digest(f, "sha256").hexdigest()
            with source_path.open("rb") as f:
                source_hash = hashlib.file_digest(f, "sha256").hexdigest()
            with normalized_path.open(newline="", encoding="utf-8-sig") as f:
                normalized_rows = list(csv.DictReader(f))
            valid_files = (normalized_hash == row.get("normalized_sha256") and
                           source_hash == row.get("sha256") and valid_count and
                           len(normalized_rows) == int(count) and
                           all(not item.get("sku") or item["sku"] in scope for item in normalized_rows) and
                           (not sku or name not in {"business_metrics", "inventory"} or
                            any(item.get("sku") == sku for item in normalized_rows)))
        except (OSError, UnicodeError, csv.Error):
            valid_files = False
        if not valid_files:
            issues.append(f"unverified report {name}")
    return issues


def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(path, decision, actions, term_actions):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Amazon JP Weekly Performance Review\n\n")
        f.write(f"Decision: `{decision}`\n\n")
        f.write("## Operating Actions\n\n")
        for row in actions:
            f.write(f"- `{row['sku']}` {row['area']} -> {row['action']}: {row['reason']}\n")
        f.write("\n## Search Term Actions\n\n")
        if term_actions:
            for row in term_actions:
                f.write(f"- `{row['search_term']}` -> {row['action']}: {row['reason']}\n")
        else:
            f.write("- No search-term actions crossed thresholds.\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True)
    parser.add_argument("--search-terms")
    parser.add_argument("--inventory")
    parser.add_argument("--returns")
    parser.add_argument("--report-manifest")
    parser.add_argument("--output-prefix", default="performance")
    parser.add_argument("--max-age-days", type=int, default=14)
    args = parser.parse_args()

    actions = []
    metric_rows = read_csv(args.metrics)
    for row in metric_rows:
        actions.extend(review_metric_row(row, args.max_age_days))
    manifest_rows = read_csv(args.report_manifest)
    for metric in metric_rows or [{}]:
        issues = manifest_issues(manifest_rows, args.max_age_days, sku=get(metric, "sku", "SKU"))
        if issues:
            actions.append({"launch_id": get(metric, "launch_id", "Launch ID"),
                            "sku": get(metric, "sku", "SKU"), "area": "data", "action": "needs_proof",
                            "reason": "; ".join(issues), "owner": "operator", "status": "todo"})
    if not metric_rows:
        actions.append({"launch_id": "", "sku": "", "area": "data", "action": "needs_proof",
                        "reason": "metrics report has no rows", "owner": "operator", "status": "todo"})
    actions.extend(inventory_actions(read_csv(args.inventory)))
    actions.extend(return_actions(read_csv(args.returns)))
    term_actions = search_term_actions(read_csv(args.search_terms))
    launch_by_sku = {get(row, "sku", "SKU"): get(row, "launch_id", "Launch ID") for row in metric_rows}
    for action in actions:
        if action["sku"] and not action["launch_id"]:
            action["launch_id"] = launch_by_sku.get(action["sku"], "")
    for term in term_actions:
        if term["action"] == "negate_or_reduce_bid":
            actions.append({"launch_id": term["launch_id"] or launch_by_sku.get(term["sku"], ""),
                            "sku": term["sku"], "area": "ads", "action": "reduce_bid_or_add_negatives",
                            "reason": f"search term {term['search_term']}: {term['reason']}",
                            "owner": "ads", "status": "todo"})
    decision = final_decision(actions)
    grouped = defaultdict(list)
    for action in actions:
        grouped[(action["launch_id"], action["sku"])].append(action)
    per_sku = [{"launch_id": launch_id, "sku": sku, "decision": final_decision(rows)}
               for (launch_id, sku), rows in sorted(grouped.items())]
    write_csv(f"{args.output_prefix}.decisions.csv", per_sku, ["launch_id", "sku", "decision"])
    write_csv(f"{args.output_prefix}.actions.csv", actions, [
        "launch_id", "sku", "area", "action", "reason", "owner", "status",
    ])
    write_csv(f"{args.output_prefix}.alerts.csv", term_actions, [
        "launch_id", "sku", "search_term", "action", "reason", "sales_jpy",
    ])
    write_report(f"{args.output_prefix}.weekly_review.md", decision, actions, term_actions)
    print(f"{args.output_prefix}.actions.csv")
    print(f"{args.output_prefix}.decisions.csv")
    print(f"{args.output_prefix}.alerts.csv")
    print(f"{args.output_prefix}.weekly_review.md")


if __name__ == "__main__":
    main()
