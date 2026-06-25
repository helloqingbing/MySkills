# Amazon Japan Product Research Canonical Schema

## Universal Identifiers

Include these fields when available so all Amazon JP skills can join artifacts:

| Canonical field | Source aliases |
|---|---|
| `candidate_id` | `candidate_id`, `Candidate ID`, `Opportunity ID` |
| `sku` | `SKU`, `Seller SKU`, `sku` |
| `parent_asin` | `Parent ASIN`, `ASIN`, `parent_asin` |
| `launch_id` | `Launch ID`, `launch_id` |

## Niche Overview

| Canonical field | Source aliases |
|---|---|
| `niche_name` | `Niche Name` |
| `top_search_term` | `Top Search Term` |
| `search_volume_360d` | `Search Volume (360d)` |
| `search_volume_growth_yoy_pct` | `Search Volume Growth YoY` |
| `search_volume_growth_qoq_pct` | `Search Volume Growth QoQ` |
| `units_sold_360d` | `Units Sold (360d)` |
| `avg_units_per_purchase` | `Avg Units Per Purchase` |
| `avg_selling_price_jpy` | `Avg Selling Price (360d)` |
| `number_of_top_clicked_products` | `Number of Top Clicked Products` |
| `total_brands_in_niche` | `Total Brands in Niche` |
| `top5_brand_click_share_pct` | `Top5 Brand Click Share` |
| `top20_brand_click_share_pct` | `Top20 Brand Click Share` |
| `avg_review_count` | `Avg Review Count` |
| `avg_star_rating` | `Avg Star Rating` |
| `new_asins_launched_12m` | `New ASINs Launched (12m)` |

## Product Detail

| Canonical field | Source aliases |
|---|---|
| `parent_asin` | `Parent ASIN` |
| `product_title` | `Product Title` |
| `brand` | `Brand` |
| `category_path` | `Category Path` |
| `launch_date` | `Launch Date` |
| `avg_selling_price_jpy` | `Avg Selling Price (360d)` |
| `total_reviews` | `Total Reviews` |
| `average_star_rating` | `Average Star Rating` |
| `clicks_360d` | `360 Day Clicks` |
| `click_share_360d_pct` | `Click Share (360d)` |
| `avg_bsr_360d` | `Avg BSR (360d)` |
| `seller_vendor_count` | `Number of Sellers/Vendors` |
| `variation_count` | `Variation Count` |
| `is_amazon_basics` | `Is Amazon Basics` |
| `top_search_term_driving_clicks` | `Top Search Term Driving Clicks` |
| `units_sold_360d` | `360 Day Units Sold` |
| `price_min_jpy` | `Price Min` |
| `price_max_jpy` | `Price Max` |

## Search Terms

| Canonical field | Source aliases |
|---|---|
| `search_term` | `Search Term` |
| `search_volume_360d` | `Search Volume (360d)` |
| `search_volume_growth_yoy_pct` | `YoY Search Volume Growth` |
| `search_volume_growth_qoq_pct` | `QoQ Search Volume Growth` |
| `click_share_pct` | `Click Share` |
| `search_conversion_rate_pct` | `Search Conversion Rate` |
| `top_clicked_asins` | `Top 3 Clicked ASINs` |
| `median_price_converted_jpy` | `Median Price of Converted Products` |
| `avg_units_per_order` | `Avg Units Per Order` |

## Supplier Quotes

Use this table for launch-gate economics and supplier validation.

| Canonical field | Source aliases |
|---|---|
| `candidate_id` | `candidate_id`, `Candidate ID`, `Opportunity ID` |
| `sku` | `SKU`, `Seller SKU`, `sku` |
| `supplier_name` | `Supplier`, `Supplier Name`, `supplier_name` |
| `supplier_url` | `Supplier URL`, `URL`, `supplier_url` |
| `unit_cost_jpy` | `Unit Cost JPY`, `Unit Cost`, `FOB JPY`, `unit_cost_jpy` |
| `unit_cost_currency` | `Currency`, `unit_cost_currency` |
| `moq` | `MOQ`, `Minimum Order Quantity`, `moq` |
| `sample_cost_jpy` | `Sample Cost`, `Sample Cost JPY`, `sample_cost_jpy` |
| `lead_time_days` | `Lead Time Days`, `Lead Time`, `lead_time_days` |
| `package_length_cm` | `Package Length cm`, `package_length_cm` |
| `package_width_cm` | `Package Width cm`, `package_width_cm` |
| `package_height_cm` | `Package Height cm`, `package_height_cm` |
| `package_weight_g` | `Package Weight g`, `package_weight_g` |
| `carton_qty` | `Carton Qty`, `Units per Carton`, `carton_qty` |
| `certifications` | `Certifications`, `Test Reports`, `certifications` |
| `quote_notes` | `Notes`, `quote_notes` |

## Keepa / Trend Notes

| Canonical field | Source aliases |
|---|---|
| `candidate_id` | `candidate_id`, `Candidate ID` |
| `parent_asin` | `Parent ASIN`, `ASIN`, `parent_asin` |
| `price_stability` | `Price Stability`, `price_stability` |
| `bsr_trend` | `BSR Trend`, `bsr_trend` |
| `seasonality_note` | `Seasonality`, `seasonality_note` |
| `stockout_note` | `Stockout`, `stockout_note` |
| `keepa_notes` | `Keepa Notes`, `keepa_notes` |

## Advertising Search-Term Report

Use this for post-launch feedback into `amazon-ads-planner` and `amazon-jp-sop-orchestrator`.

| Canonical field | Source aliases |
|---|---|
| `launch_id` | `Launch ID`, `launch_id` |
| `sku` | `SKU`, `Advertised SKU`, `sku` |
| `search_term` | `Customer Search Term`, `Search Term`, `search_term` |
| `campaign` | `Campaign Name`, `Campaign`, `campaign` |
| `match_type` | `Match Type`, `match_type` |
| `impressions` | `Impressions`, `impressions` |
| `clicks` | `Clicks`, `clicks` |
| `spend_jpy` | `Spend`, `Cost`, `Spend JPY`, `spend_jpy` |
| `orders` | `Orders`, `7 Day Total Orders (#)`, `orders` |
| `sales_jpy` | `Sales`, `7 Day Total Sales`, `sales_jpy` |
| `acos_pct` | `ACOS`, `Advertising Cost of Sales`, `acos_pct` |

## Default Japan Profile

- Target market: Amazon Japan.
- Target categories: home, pet, outdoor.
- Avoid: food, baby/children, medical, electric or battery-powered products, liquids.
- Target price: JPY 3,000-7,500 by default, equivalent to USD 20-50 at an approximate planning rate of 150 JPY/USD.
- If actual niche price is below target but the product is naturally bundleable, mark `bundle_needed` instead of rejecting automatically.
