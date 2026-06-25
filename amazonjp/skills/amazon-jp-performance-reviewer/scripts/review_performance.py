#!/usr/bin/env python3
import argparse
import csv


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_number(value):
    text = str(value or "").replace(",", "").replace("%", "").replace("￥", "").strip()
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


def review_metric_row(row):
    launch_id = get(row, "launch_id", "Launch ID")
    sku = get(row, "sku", "SKU")
    acos = parse_number(get(row, "acos_pct", "ACOS"))
    tacos = parse_number(get(row, "tacos_pct", "TACOS"))
    break_even = parse_number(get(row, "break_even_acos_pct", "Break-even ACOS"))
    cvr = parse_number(get(row, "unit_session_pct", "Unit Session %", "cvr_pct"))
    rating = parse_number(get(row, "rating", "Rating"))
    returns = parse_number(get(row, "returns", "Returns"))
    inventory_days = parse_number(get(row, "days_of_supply", "Days of Supply"))
    actions = []

    if break_even and acos > break_even:
        actions.append(("ads", "reduce_bid_or_add_negatives", f"ACOS {acos:.1f}% above break-even {break_even:.1f}%"))
    if tacos and tacos > 35:
        actions.append(("profit", "check_price_margin_and_budget", f"TACOS {tacos:.1f}% is high"))
    if cvr and cvr < 5:
        actions.append(("listing", "review_price_images_reviews", f"conversion {cvr:.1f}% is weak"))
    if inventory_days and inventory_days < 21:
        actions.append(("fba", "trigger_replenishment", f"inventory {inventory_days:.1f} days"))
    if rating and rating < 4.2:
        actions.append(("product", "run_review_mining_and_pause_scale", f"rating {rating:.1f} below 4.2"))
    if returns >= 3:
        actions.append(("qc", "inspect_return_reasons", f"returns count {returns:.0f}"))
    if not actions:
        actions.append(("growth", "watch_or_scale_carefully", "core metrics within action thresholds"))

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
        if spend >= 1500 and orders == 0:
            action = "negate_or_reduce_bid"
            reason = "spent at least 1500 JPY with no orders"
        elif orders >= 2 and (acos == 0 or acos <= 30):
            action = "promote_exact"
            reason = "orders with efficient ACOS"
        elif clicks >= 20 and orders == 0:
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
        if days and days < 21:
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
        totals[sku] = totals.get(sku, 0.0) + (parse_number(get(row, "return_qty", "Quantity")) or 1.0)
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
    if "trigger_replenishment" in action_names:
        return "optimize"
    if "reduce_bid_or_add_negatives" in action_names:
        return "optimize"
    if action_names == {"watch_or_scale_carefully"}:
        return "scale"
    return "watch"


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
    parser.add_argument("--output-prefix", default="performance")
    args = parser.parse_args()

    actions = []
    for row in read_csv(args.metrics):
        actions.extend(review_metric_row(row))
    actions.extend(inventory_actions(read_csv(args.inventory)))
    actions.extend(return_actions(read_csv(args.returns)))
    term_actions = search_term_actions(read_csv(args.search_terms))
    decision = final_decision(actions)
    write_csv(f"{args.output_prefix}.actions.csv", actions, [
        "launch_id", "sku", "area", "action", "reason", "owner", "status",
    ])
    write_csv(f"{args.output_prefix}.alerts.csv", term_actions, [
        "launch_id", "sku", "search_term", "action", "reason", "sales_jpy",
    ])
    write_report(f"{args.output_prefix}.weekly_review.md", decision, actions, term_actions)
    print(f"{args.output_prefix}.actions.csv")
    print(f"{args.output_prefix}.alerts.csv")
    print(f"{args.output_prefix}.weekly_review.md")


if __name__ == "__main__":
    main()
