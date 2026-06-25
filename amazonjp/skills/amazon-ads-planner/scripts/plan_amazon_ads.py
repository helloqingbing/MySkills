#!/usr/bin/env python3
import argparse
import csv
import re


FORBIDDEN_TERMS = [
    "食品", "サプリ", "医療", "医薬", "治療", "ベビー", "子供", "こども", "キッズ",
    "電動", "電池", "充電", "バッテリー", "液体", "オイル", "スプレー",
]


def parse_number(value):
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def get(row, *names):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return ""


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clamp(value, low, high):
    return max(low, min(high, value))


def normalize_relevance(value):
    text = str(value or "").strip().lower()
    if text in {"high", "高", "h"}:
        return 1.0
    if text in {"medium", "中", "m"}:
        return 0.65
    if text in {"low", "低", "l"}:
        return 0.35
    score = parse_number(text)
    if score > 1:
        return clamp(score / 100.0, 0.0, 1.0)
    return clamp(score or 0.7, 0.0, 1.0)


def normalize_product(row, default_budget):
    asin = get(row, "asin", "ASIN", "Parent ASIN", "parent_asin", "sku")
    price = parse_number(get(row, "price_jpy", "Price", "Selling Price", "Avg Selling Price (360d)"))
    profit = parse_number(get(row, "gross_profit_jpy", "Gross Profit", "profit_jpy"))
    margin_pct = parse_number(get(row, "gross_margin_pct", "Gross Margin", "margin_pct"))
    if not profit and margin_pct and price:
        profit = price * margin_pct / 100.0
    break_even_acos = profit / price if price else 0.0
    provided_target = parse_number(get(row, "target_acos_pct", "Target ACOS"))
    target_acos = provided_target / 100.0 if provided_target else min(break_even_acos * 0.8, 0.35)
    daily_budget = parse_number(get(row, "daily_budget_jpy", "Daily Budget", "budget_jpy")) or default_budget
    return {
        "asin": asin,
        "title": get(row, "title", "Product Title", "product_title"),
        "price_jpy": price,
        "gross_profit_jpy": profit,
        "break_even_acos": break_even_acos,
        "target_acos": target_acos,
        "daily_budget_jpy": daily_budget,
    }


def normalize_keyword(row):
    keyword = get(row, "keyword", "Keyword", "Search Term", "search_term")
    cvr = parse_number(get(row, "conversion_rate_pct", "Search Conversion Rate", "CVR"))
    relevance = normalize_relevance(get(row, "relevance", "Relevance", "score"))
    volume = parse_number(get(row, "search_volume", "Search Volume", "Search Volume (360d)"))
    return {
        "keyword": keyword,
        "cvr_pct": cvr,
        "relevance": relevance,
        "search_volume": volume,
        "source": get(row, "source", "Source"),
        "intent": get(row, "intent", "Intent"),
        "ads_match_type": get(row, "ads_match_type", "Ads Match Type", "match_type"),
        "risk": get(row, "risk", "Risk"),
        "listing_action": get(row, "listing_action", "Listing Action"),
    }


def normalize_search_term_report(row):
    spend = parse_number(get(row, "spend_jpy", "Spend", "Cost", "Spend JPY"))
    clicks = parse_number(get(row, "clicks", "Clicks"))
    orders = parse_number(get(row, "orders", "Orders", "7 Day Total Orders (#)"))
    sales = parse_number(get(row, "sales_jpy", "Sales", "7 Day Total Sales"))
    impressions = parse_number(get(row, "impressions", "Impressions"))
    acos = parse_number(get(row, "acos_pct", "ACOS", "Advertising Cost of Sales"))
    ctr = (clicks / impressions * 100.0) if impressions else 0.0
    cvr = (orders / clicks * 100.0) if clicks else 0.0
    return {
        "launch_id": get(row, "launch_id", "Launch ID"),
        "sku": get(row, "sku", "SKU", "Advertised SKU"),
        "search_term": get(row, "search_term", "Search Term", "Customer Search Term"),
        "campaign": get(row, "campaign", "Campaign", "Campaign Name"),
        "match_type": get(row, "match_type", "Match Type"),
        "impressions": impressions,
        "clicks": clicks,
        "spend_jpy": spend,
        "orders": orders,
        "sales_jpy": sales,
        "acos_pct": acos,
        "ctr_pct": ctr,
        "cvr_pct": cvr,
    }


def normalize_competitor(row):
    return {
        "asin": get(row, "competitor_asin", "ASIN", "Parent ASIN"),
        "title": get(row, "title", "Product Title"),
        "brand": get(row, "brand", "Brand"),
        "price_jpy": parse_number(get(row, "price_jpy", "Price", "Avg Selling Price (360d)")),
        "reviews": parse_number(get(row, "reviews", "Total Reviews")),
        "rating": parse_number(get(row, "rating", "Average Star Rating")),
    }


def has_forbidden_term(text):
    return [term for term in FORBIDDEN_TERMS if term.lower() in text.lower()]


def bid_from(product, cvr_pct, multiplier=1.0):
    cvr = cvr_pct / 100.0 if cvr_pct else 0.06
    raw = product["price_jpy"] * product["target_acos"] * cvr * multiplier
    return round(clamp(raw, 25, 150))


def allocate_budget(total, share):
    return max(300, round(total * share / 100.0))


def campaign_name(product, group):
    return f"JP_SP_{product['asin']}_{group}"


def plan_for_product(product, keywords, competitors):
    campaigns = []
    negatives = []
    blocked_keywords = [
        k for k in keywords
        if (k.get("risk") or "").lower() == "blocked"
        or (k.get("ads_match_type") and "negative" in k["ads_match_type"].lower())
    ]
    usable_keywords = [k for k in keywords if k not in blocked_keywords]
    high_keywords = [k for k in usable_keywords if k["keyword"] and k["relevance"] >= 0.75]
    mid_keywords = [k for k in usable_keywords if k["keyword"] and k["relevance"] >= 0.45]

    total_budget = product["daily_budget_jpy"]
    collapsed = total_budget < 2000
    budget_shares = {
        "AUTO_DISCOVERY": 45 if collapsed else 30,
        "BROAD_DISCOVERY": 0 if collapsed else 20,
        "EXACT_PROFIT": 55 if collapsed else 35,
        "PRODUCT_TARGETING": 0 if collapsed else 15,
    }

    auto_bid = bid_from(product, 5.0, 0.8)
    campaigns.append({
        "campaign_name": campaign_name(product, "AUTO_DISCOVERY"),
        "campaign_type": "Sponsored Products",
        "targeting": "auto",
        "ad_group": "auto",
        "asin": product["asin"],
        "target": "*auto*",
        "match_type": "auto",
        "bid_jpy": auto_bid,
        "daily_budget_jpy": allocate_budget(total_budget, budget_shares["AUTO_DISCOVERY"]),
        "purpose": "mine search terms and ASIN placements",
    })

    for kw in blocked_keywords:
        if kw.get("keyword"):
            negatives.append({
                "campaign_name": campaign_name(product, "BROAD_DISCOVERY"),
                "negative_type": kw.get("ads_match_type") or "negative phrase",
                "target": kw["keyword"],
                "reason": "keyword master marked as blocked or negative",
            })

    if budget_shares["BROAD_DISCOVERY"]:
        for kw in mid_keywords[:30]:
            if kw.get("ads_match_type") and "negative" in kw["ads_match_type"].lower():
                negatives.append({
                    "campaign_name": campaign_name(product, "BROAD_DISCOVERY"),
                    "negative_type": kw["ads_match_type"],
                    "target": kw["keyword"],
                    "reason": "keyword master marked as negative",
                })
                continue
            forbidden = has_forbidden_term(kw["keyword"])
            if forbidden:
                negatives.append({
                    "campaign_name": campaign_name(product, "BROAD_DISCOVERY"),
                    "negative_type": "negative phrase",
                    "target": kw["keyword"],
                    "reason": f"forbidden term: {','.join(forbidden)}",
                })
                continue
            campaigns.append({
                "campaign_name": campaign_name(product, "BROAD_DISCOVERY"),
                "campaign_type": "Sponsored Products",
                "targeting": "manual keyword",
                "ad_group": "broad",
                "asin": product["asin"],
                "target": kw["keyword"],
                "match_type": "broad",
                "bid_jpy": bid_from(product, kw["cvr_pct"] or 4.5, 0.78),
                "daily_budget_jpy": allocate_budget(total_budget, budget_shares["BROAD_DISCOVERY"]),
                "purpose": "long-tail discovery",
            })

    for kw in high_keywords[:20]:
        if kw.get("ads_match_type") and "negative" in kw["ads_match_type"].lower():
            negatives.append({
                "campaign_name": campaign_name(product, "EXACT_PROFIT"),
                "negative_type": kw["ads_match_type"],
                "target": kw["keyword"],
                "reason": "keyword master marked as negative",
            })
            continue
        forbidden = has_forbidden_term(kw["keyword"])
        if forbidden:
            negatives.append({
                "campaign_name": campaign_name(product, "EXACT_PROFIT"),
                "negative_type": "negative exact",
                "target": kw["keyword"],
                "reason": f"forbidden term: {','.join(forbidden)}",
            })
            continue
        campaigns.append({
            "campaign_name": campaign_name(product, "EXACT_PROFIT"),
            "campaign_type": "Sponsored Products",
            "targeting": "manual keyword",
            "ad_group": "exact",
            "asin": product["asin"],
            "target": kw["keyword"],
            "match_type": "exact",
            "bid_jpy": bid_from(product, kw["cvr_pct"] or 7.0, 1.0),
            "daily_budget_jpy": allocate_budget(total_budget, budget_shares["EXACT_PROFIT"]),
            "purpose": "profit and rank high-intent terms",
        })

    if budget_shares["PRODUCT_TARGETING"]:
        for comp in competitors[:20]:
            if not comp["asin"]:
                continue
            weakness = 1.0
            if comp["rating"] and comp["rating"] < 4.3:
                weakness += 0.1
            if comp["price_jpy"] and comp["price_jpy"] > product["price_jpy"]:
                weakness += 0.1
            campaigns.append({
                "campaign_name": campaign_name(product, "PRODUCT_TARGETING"),
                "campaign_type": "Sponsored Products",
                "targeting": "manual product",
                "ad_group": "product_targeting",
                "asin": product["asin"],
                "target": comp["asin"],
                "match_type": "asin target",
                "bid_jpy": bid_from(product, 5.5, clamp(weakness, 0.7, 1.1)),
                "daily_budget_jpy": allocate_budget(total_budget, budget_shares["PRODUCT_TARGETING"]),
                "purpose": "capture competitor detail-page traffic",
            })

    return campaigns, negatives


def feedback_action(row, product):
    gross_profit = product["gross_profit_jpy"]
    target_acos_pct = product["target_acos"] * 100.0
    term = row["search_term"]
    if has_forbidden_term(term):
        return "negate", "forbidden or out-of-scope term"
    if row["orders"] >= 1 and (row["acos_pct"] == 0 or row["acos_pct"] <= target_acos_pct):
        return "promote_exact", "orders with acceptable ACOS"
    if gross_profit and row["spend_jpy"] > gross_profit and row["orders"] == 0:
        return "negate", "spend exceeded gross profit without order"
    if row["clicks"] >= 15 and row["orders"] == 0:
        return "negate", "15+ clicks without order"
    if row["ctr_pct"] >= 0.4 and row["cvr_pct"] < 2.0 and row["clicks"] >= 10:
        return "listing_action", "traffic clicks but does not convert"
    if row["clicks"] >= 3 and row["orders"] == 0:
        return "watch", "collect more data"
    return "watch", "insufficient signal"


def build_feedback(products, report_rows):
    if not report_rows:
        return []
    product = products[0] if products else {
        "gross_profit_jpy": 0.0,
        "target_acos": 0.3,
    }
    rows = []
    for raw in report_rows:
        row = normalize_search_term_report(raw)
        action, reason = feedback_action(row, product)
        row["action"] = action
        row["reason"] = reason
        rows.append(row)
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_plan(path, products, campaigns, negatives):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Amazon Japan Sponsored Products 30-Day Plan\n\n")
        for product in products:
            f.write(f"## ASIN {product['asin']}\n\n")
            f.write(f"- Price: JPY {product['price_jpy']:.0f}\n")
            f.write(f"- Gross profit: JPY {product['gross_profit_jpy']:.0f}\n")
            f.write(f"- Break-even ACOS: {product['break_even_acos'] * 100:.1f}%\n")
            f.write(f"- Target ACOS: {product['target_acos'] * 100:.1f}%\n")
            f.write(f"- Daily budget: JPY {product['daily_budget_jpy']:.0f}\n\n")
        f.write("## Campaign Structure\n\n")
        f.write("| Campaign | Targeting | Target | Match | Bid | Budget | Purpose |\n")
        f.write("|---|---|---|---|---:|---:|---|\n")
        for row in campaigns:
            f.write(
                f"| {row['campaign_name']} | {row['targeting']} | {row['target']} | "
                f"{row['match_type']} | {row['bid_jpy']} | {row['daily_budget_jpy']} | {row['purpose']} |\n"
            )
        f.write("\n## Negative Rules\n\n")
        if negatives:
            for row in negatives:
                f.write(f"- `{row['campaign_name']}`: add `{row['target']}` as {row['negative_type']} because {row['reason']}.\n")
        else:
            f.write("- No hard negative keywords detected from the provided keyword list. Add negatives from the search-term report after launch.\n")
        f.write("\n## 30-Day Optimization Plan\n\n")
        f.write("### Days 1-7\n\n")
        f.write("- Launch Auto, Broad, Exact, and Product Targeting campaigns if budget allows.\n")
        f.write("- Watch CTR and spend, but do not overreact before terms collect clicks.\n")
        f.write("- If CTR is weak, improve main image, price, coupon, title, and first bullet.\n\n")
        f.write("### Days 8-14\n\n")
        f.write("- Pull Search Term Report.\n")
        f.write("- Move converting terms from Auto/Broad into Exact.\n")
        f.write("- Add irrelevant terms as negative exact or negative phrase.\n")
        f.write("- Lower targets that spend over 0.7x gross profit without orders.\n\n")
        f.write("### Days 15-21\n\n")
        f.write("- Split winners into a profit campaign.\n")
        f.write("- Raise bids 10-20% on exact terms with 2+ orders and acceptable ACOS.\n")
        f.write("- Expand ASIN targeting where competitors are weaker on price, rating, images, bundle, or reviews.\n\n")
        f.write("### Days 22-30\n\n")
        f.write("- Keep discovery campaigns capped.\n")
        f.write("- Push only 3-5 strategic exact terms for ranking.\n")
        f.write("- Evaluate TACOS and organic rank movement before scaling budget.\n")


def write_feedback_plan(path, feedback_rows):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Amazon JP Ads Search-Term Feedback\n\n")
        if not feedback_rows:
            f.write("- No search-term report provided.\n")
            return
        f.write("| Search Term | Clicks | Spend | Orders | Sales | ACOS | Action | Reason |\n")
        f.write("|---|---:|---:|---:|---:|---:|---|---|\n")
        for row in feedback_rows:
            f.write(
                f"| {row['search_term']} | {row['clicks']:.0f} | {row['spend_jpy']:.0f} | "
                f"{row['orders']:.0f} | {row['sales_jpy']:.0f} | {row['acos_pct']:.1f}% | "
                f"{row['action']} | {row['reason']} |\n"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--competitors")
    parser.add_argument("--search-term-report")
    parser.add_argument("--default-daily-budget-jpy", type=int, default=3000)
    parser.add_argument("--output-prefix", default="amazon_jp_ads")
    args = parser.parse_args()

    products = [normalize_product(row, args.default_daily_budget_jpy) for row in read_csv(args.products)]
    keywords = [normalize_keyword(row) for row in read_csv(args.keywords)]
    competitors = [normalize_competitor(row) for row in read_csv(args.competitors)]
    search_report = read_csv(args.search_term_report)

    all_campaigns = []
    all_negatives = []
    for product in products:
        campaigns, negatives = plan_for_product(product, keywords, competitors)
        all_campaigns.extend(campaigns)
        all_negatives.extend(negatives)

    write_csv(f"{args.output_prefix}.campaigns.csv", all_campaigns)
    write_csv(f"{args.output_prefix}.negatives.csv", all_negatives)
    write_plan(f"{args.output_prefix}.30_day_plan.md", products, all_campaigns, all_negatives)
    feedback = build_feedback(products, search_report)
    write_csv(f"{args.output_prefix}.search_term_feedback.csv", feedback)
    write_feedback_plan(f"{args.output_prefix}.search_term_feedback.md", feedback)
    print(f"{args.output_prefix}.campaigns.csv")
    print(f"{args.output_prefix}.negatives.csv")
    print(f"{args.output_prefix}.30_day_plan.md")
    print(f"{args.output_prefix}.search_term_feedback.csv")
    print(f"{args.output_prefix}.search_term_feedback.md")


if __name__ == "__main__":
    main()
