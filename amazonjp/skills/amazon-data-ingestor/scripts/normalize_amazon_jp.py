#!/usr/bin/env python3
import argparse
import csv
import os
import re


MAPPINGS = {
    "niches": {
        "candidate_id": "candidate_id",
        "Candidate ID": "candidate_id",
        "Niche Name": "niche_name",
        "Top Search Term": "top_search_term",
        "Search Volume (360d)": "search_volume_360d",
        "Search Volume Growth YoY": "search_volume_growth_yoy_pct",
        "Search Volume Growth QoQ": "search_volume_growth_qoq_pct",
        "Units Sold (360d)": "units_sold_360d",
        "Avg Units Per Purchase": "avg_units_per_purchase",
        "Avg Selling Price (360d)": "avg_selling_price_jpy",
        "Number of Top Clicked Products": "number_of_top_clicked_products",
        "Total Brands in Niche": "total_brands_in_niche",
        "Top5 Brand Click Share": "top5_brand_click_share_pct",
        "Top20 Brand Click Share": "top20_brand_click_share_pct",
        "Avg Review Count": "avg_review_count",
        "Avg Star Rating": "avg_star_rating",
        "New ASINs Launched (12m)": "new_asins_launched_12m",
    },
    "products": {
        "candidate_id": "candidate_id",
        "Candidate ID": "candidate_id",
        "sku": "sku",
        "SKU": "sku",
        "Parent ASIN": "parent_asin",
        "Product Title": "product_title",
        "Brand": "brand",
        "Category Path": "category_path",
        "Launch Date": "launch_date",
        "Avg Selling Price (360d)": "avg_selling_price_jpy",
        "Total Reviews": "total_reviews",
        "Average Star Rating": "average_star_rating",
        "360 Day Clicks": "clicks_360d",
        "Click Share (360d)": "click_share_360d_pct",
        "Avg BSR (360d)": "avg_bsr_360d",
        "Number of Sellers/Vendors": "seller_vendor_count",
        "Variation Count": "variation_count",
        "Is Amazon Basics": "is_amazon_basics",
        "Top Search Term Driving Clicks": "top_search_term_driving_clicks",
        "360 Day Units Sold": "units_sold_360d",
        "Price Min": "price_min_jpy",
        "Price Max": "price_max_jpy",
    },
    "search_terms": {
        "candidate_id": "candidate_id",
        "Candidate ID": "candidate_id",
        "keyword": "search_term",
        "search_term": "search_term",
        "Search Term": "search_term",
        "Search Volume (360d)": "search_volume_360d",
        "YoY Search Volume Growth": "search_volume_growth_yoy_pct",
        "QoQ Search Volume Growth": "search_volume_growth_qoq_pct",
        "Click Share": "click_share_pct",
        "Search Conversion Rate": "search_conversion_rate_pct",
        "Top 3 Clicked ASINs": "top_clicked_asins",
        "Median Price of Converted Products": "median_price_converted_jpy",
        "Avg Units Per Order": "avg_units_per_order",
    },
    "supplier_quotes": {
        "candidate_id": "candidate_id",
        "Candidate ID": "candidate_id",
        "sku": "sku",
        "SKU": "sku",
        "supplier_name": "supplier_name",
        "Supplier": "supplier_name",
        "Supplier URL": "supplier_url",
        "Unit Cost JPY": "unit_cost_jpy",
        "Currency": "unit_cost_currency",
        "MOQ": "moq",
        "Sample Cost JPY": "sample_cost_jpy",
        "Lead Time Days": "lead_time_days",
        "Package Length cm": "package_length_cm",
        "Package Width cm": "package_width_cm",
        "Package Height cm": "package_height_cm",
        "Package Weight g": "package_weight_g",
        "Carton Qty": "carton_qty",
        "Certifications": "certifications",
        "Notes": "quote_notes",
    },
    "ad_search_terms": {
        "launch_id": "launch_id",
        "Launch ID": "launch_id",
        "sku": "sku",
        "SKU": "sku",
        "search_term": "search_term",
        "Customer Search Term": "search_term",
        "Campaign Name": "campaign",
        "Match Type": "match_type",
        "Impressions": "impressions",
        "Clicks": "clicks",
        "Spend": "spend_jpy",
        "Orders": "orders",
        "Sales": "sales_jpy",
        "ACOS": "acos_pct",
    },
}


def clean_value(field, value):
    if value is None:
        return ""
    value = value.strip()
    if value == "":
        return ""
    if field.endswith("_jpy"):
        return re.sub(r"[^0-9.]", "", value)
    if field.endswith("_pct"):
        return re.sub(r"[^0-9.\-]", "", value)
    if field in {
        "search_volume_360d",
        "units_sold_360d",
        "number_of_top_clicked_products",
        "total_brands_in_niche",
        "avg_review_count",
        "new_asins_launched_12m",
        "total_reviews",
        "clicks_360d",
        "avg_bsr_360d",
        "seller_vendor_count",
        "variation_count",
        "moq",
        "lead_time_days",
        "package_length_cm",
        "package_width_cm",
        "package_height_cm",
        "package_weight_g",
        "carton_qty",
        "impressions",
        "clicks",
        "orders",
    }:
        return re.sub(r"[^0-9.]", "", value)
    return value


def normalize_file(kind, path, output_dir):
    mapping = MAPPINGS[kind]
    fieldnames = []
    for target in mapping.values():
        if target not in fieldnames:
            fieldnames.append(target)
    with open(path, newline="", encoding="utf-8-sig") as src:
        reader = csv.DictReader(src)
        rows = []
        for row in reader:
            normalized = {field: "" for field in fieldnames}
            for source, target in mapping.items():
                value = row.get(source, "")
                if value not in (None, ""):
                    normalized[target] = clean_value(target, value)
            rows.append(normalized)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{kind}.normalized.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_path, len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niches")
    parser.add_argument("--products")
    parser.add_argument("--search-terms")
    parser.add_argument("--supplier-quotes")
    parser.add_argument("--ad-search-terms")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    inputs = {
        "niches": args.niches,
        "products": args.products,
        "search_terms": args.search_terms,
        "supplier_quotes": args.supplier_quotes,
        "ad_search_terms": args.ad_search_terms,
    }
    for kind, path in inputs.items():
        if path:
            out_path, count = normalize_file(kind, path, args.output_dir)
            print(f"{kind}: {count} rows -> {out_path}")


if __name__ == "__main__":
    main()
