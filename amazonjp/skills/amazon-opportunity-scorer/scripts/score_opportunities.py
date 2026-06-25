#!/usr/bin/env python3
import argparse
import csv
import math
import re
from collections import defaultdict


HARD_RISK_KEYWORDS = [
    "食品", "サプリ", "医療", "医薬", "治療", "ベビー", "子供", "こども", "キッズ",
    "電動", "電池", "充電", "バッテリー", "液体", "オイル", "化粧品",
]

BUNDLEABLE_KEYWORDS = [
    "袋", "マット", "収納", "ストロー", "ブラシ", "ケース", "カバー", "シート",
    "セット", "交換", "携帯", "小分け", "保存", "ペット", "アウトドア",
]

IMPROVEMENT_KEYWORDS = [
    "漏れ", "防水", "厚手", "BPA", "冷凍", "小分け", "サイズ", "収納",
    "携帯", "滑り止め", "抗菌", "洗える", "折りたたみ",
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


def read_csv(path):
    if not path:
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def norm(value, cap):
    if cap <= 0:
        return 0.0
    return clamp(value / cap)


def get(row, *names):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return ""


def niche_key(row):
    return get(row, "Niche Name", "niche_name")


def top_term(row):
    return get(row, "Top Search Term", "top_search_term")


def candidate_id(row):
    existing = get(row, "candidate_id", "Candidate ID", "Opportunity ID")
    if existing:
        return existing
    base = f"{niche_key(row)} {top_term(row)}".strip().lower()
    slug = re.sub(r"[^a-z0-9ぁ-んァ-ン一-龥]+", "-", base).strip("-")
    return f"cand-{slug[:48]}" if slug else "cand-unknown"


def product_matches_niche(product, niche):
    term = top_term(niche)
    product_term = get(product, "Top Search Term Driving Clicks", "top_search_term_driving_clicks")
    title = get(product, "Product Title", "product_title")
    return term and (term == product_term or term in title)


def search_matches_niche(search_term, niche):
    term = top_term(niche)
    text = get(search_term, "Search Term", "search_term")
    return term and (term == text or term in text or text in term)


def has_hard_risk(text):
    return [kw for kw in HARD_RISK_KEYWORDS if kw.lower() in text.lower()]


def is_bundleable(text):
    return any(kw.lower() in text.lower() for kw in BUNDLEABLE_KEYWORDS)


def score_niche(niche, products, search_terms, args):
    name = niche_key(niche)
    term = top_term(niche)
    all_text = " ".join([name, term] + [get(p, "Product Title", "product_title") for p in products])
    hard_risks = has_hard_risk(all_text)

    search_volume = parse_number(get(niche, "Search Volume (360d)", "search_volume_360d"))
    units_sold = parse_number(get(niche, "Units Sold (360d)", "units_sold_360d"))
    yoy = parse_number(get(niche, "Search Volume Growth YoY", "search_volume_growth_yoy_pct"))
    qoq = parse_number(get(niche, "Search Volume Growth QoQ", "search_volume_growth_qoq_pct"))
    avg_price = parse_number(get(niche, "Avg Selling Price (360d)", "avg_selling_price_jpy"))
    avg_reviews = parse_number(get(niche, "Avg Review Count", "avg_review_count"))
    avg_rating = parse_number(get(niche, "Avg Star Rating", "avg_star_rating"))
    new_asins = parse_number(get(niche, "New ASINs Launched (12m)", "new_asins_launched_12m"))
    top5_share = parse_number(get(niche, "Top5 Brand Click Share", "top5_brand_click_share_pct"))
    top20_share = parse_number(get(niche, "Top20 Brand Click Share", "top20_brand_click_share_pct"))

    demand_score = norm(search_volume, 200000) * 12 + norm(units_sold, 150000) * 8
    growth_score = norm(max(yoy, 0), 40) * 17.5 + norm(max(qoq, 0), 15) * 7.5

    review_score = clamp((3000 - avg_reviews) / 3000) * 8
    concentration_score = clamp((85 - top5_share) / 35) * 5 if top5_share else 3
    product_count = parse_number(get(niche, "Number of Top Clicked Products", "number_of_top_clicked_products"))
    product_depth_score = clamp(product_count / 40) * 2
    competition_score = review_score + concentration_score + product_depth_score

    if args.target_min_jpy <= avg_price <= args.target_max_jpy:
        price_score = 15
        price_note = "in_price_band"
    elif avg_price < args.target_min_jpy and is_bundleable(all_text):
        price_score = 9
        price_note = "bundle_needed"
    elif avg_price < args.target_min_jpy:
        price_score = 5
        price_note = "below_price_band"
    else:
        price_score = clamp((args.target_max_jpy * 1.4 - avg_price) / (args.target_max_jpy * 0.4)) * 10
        price_note = "above_price_band"

    rating_gap = 5 if 4.0 <= avg_rating <= 4.35 else 2 if avg_rating < 4.0 else 1
    modifier_hits = sum(1 for st in search_terms for kw in IMPROVEMENT_KEYWORDS if kw.lower() in get(st, "Search Term", "search_term").lower())
    variation_avg = sum(parse_number(get(p, "Variation Count", "variation_count")) for p in products) / len(products) if products else 0
    improvement_score = rating_gap + clamp(modifier_hits / 5) * 5 + clamp(variation_avg / 12) * 5

    new_asin_score = 4 if 5 <= new_asins <= 30 else 2 if new_asins else 1
    category_fit_score = 4
    lightweight_score = 2 if is_bundleable(all_text) else 1
    supply_score = new_asin_score + category_fit_score + lightweight_score

    penalties = 0
    penalty_reasons = []
    if any(get(p, "Is Amazon Basics", "is_amazon_basics").lower() == "yes" for p in products):
        penalties += 8
        penalty_reasons.append("amazon_basics_present")
    if top5_share >= 65:
        penalties += 5
        penalty_reasons.append("top5_brand_share_high")
    if top20_share >= 85:
        penalties += 4
        penalty_reasons.append("top20_brand_share_high")
    if avg_reviews >= 2000:
        penalties += 8
        penalty_reasons.append("avg_reviews_over_2000")
    if avg_reviews >= 5000:
        penalties += 6
        penalty_reasons.append("avg_reviews_over_5000")

    raw_score = demand_score + growth_score + competition_score + price_score + improvement_score + supply_score
    final_score = 0 if hard_risks else max(0, raw_score - penalties)
    if hard_risks:
        label = "Reject"
    elif final_score >= 75:
        label = "A"
    elif final_score >= 60:
        label = "B"
    elif final_score >= 45:
        label = "C"
    else:
        label = "Reject"

    return {
        "candidate_id": candidate_id(niche),
        "niche_name": name,
        "top_search_term": term,
        "final_score": round(final_score, 1),
        "label": label,
        "demand_score": round(demand_score, 1),
        "growth_score": round(growth_score, 1),
        "competition_score": round(competition_score, 1),
        "price_score": round(price_score, 1),
        "improvement_score": round(improvement_score, 1),
        "supply_score": round(supply_score, 1),
        "penalties": penalties,
        "price_note": price_note,
        "hard_risks": ",".join(hard_risks),
        "penalty_reasons": ",".join(penalty_reasons),
        "search_volume_360d": int(search_volume),
        "units_sold_360d": int(units_sold),
        "yoy_growth_pct": yoy,
        "qoq_growth_pct": qoq,
        "avg_price_jpy": int(avg_price),
        "avg_review_count": int(avg_reviews),
        "avg_rating": avg_rating,
        "top5_brand_click_share_pct": top5_share,
        "top20_brand_click_share_pct": top20_share,
        "matched_products": len(products),
        "matched_search_terms": len(search_terms),
        "parent_asin_targets": ",".join([
            get(p, "Parent ASIN", "parent_asin") for p in products[:10]
            if get(p, "Parent ASIN", "parent_asin")
        ]),
        "review_mining_needed": "yes",
        "supplier_quote_needed": "yes",
        "keepa_check_needed": "yes",
        "launch_gate_required": "yes",
    }


def write_outputs(rows, prefix):
    fieldnames = list(rows[0].keys()) if rows else []
    csv_path = f"{prefix}.opportunities.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md_path = f"{prefix}.opportunities.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Amazon Japan Opportunity Shortlist\n\n")
        f.write("| Rank | Niche | Score | Label | Evidence | Notes |\n")
        f.write("|---:|---|---:|---|---|---|\n")
        for idx, row in enumerate(rows, 1):
            evidence = f"SV {row['search_volume_360d']}, YoY {row['yoy_growth_pct']}%, reviews {row['avg_review_count']}"
            notes = f"{row['price_note']}; penalties={row['penalty_reasons'] or '-'}; risks={row['hard_risks'] or '-'}"
            f.write(f"| {idx} | {row['niche_name']} | {row['final_score']} | {row['label']} | {evidence} | {notes} |\n")
    print(csv_path)
    print(md_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niches", required=True)
    parser.add_argument("--products")
    parser.add_argument("--search-terms")
    parser.add_argument("--target-min-jpy", type=int, default=3000)
    parser.add_argument("--target-max-jpy", type=int, default=7500)
    parser.add_argument("--output-prefix", default="amazon_jp")
    args = parser.parse_args()

    niches = read_csv(args.niches)
    products = read_csv(args.products)
    search_terms = read_csv(args.search_terms)

    rows = []
    for niche in niches:
        matched_products = [p for p in products if product_matches_niche(p, niche)]
        matched_terms = [s for s in search_terms if search_matches_niche(s, niche)]
        rows.append(score_niche(niche, matched_products, matched_terms, args))
    rows.sort(key=lambda r: r["final_score"], reverse=True)
    write_outputs(rows, args.output_prefix)


if __name__ == "__main__":
    main()
