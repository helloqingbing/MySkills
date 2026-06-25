#!/usr/bin/env python3
import argparse
import csv
from collections import defaultdict


GROUPS = {
    "leakage_waterproofing": ["漏れ", "水漏れ", "防水", "密閉", "leak"],
    "durability": ["破れ", "壊れ", "耐久", "薄い", "すぐ", "durable", "broke"],
    "size_usability": ["小さい", "大きい", "使いにくい", "サイズ", "fit", "size"],
    "cleaning_odor": ["洗いにくい", "臭い", "匂い", "カビ", "odor", "smell"],
    "bundle_gap": ["足りない", "セット", "予備", "付属", "accessory", "set"],
    "packaging": ["箱", "梱包", "破損", "届いた", "package", "damaged"],
    "localization": ["説明書", "日本語", "わかりにくい", "manual"],
}


PRODUCT_ACTIONS = {
    "leakage_waterproofing": ("Improve seal / validate waterproof or airtight structure", "Do not claim waterproof/airtight without test proof", "Seal or leak-prevention detail", "Close-up of seal, lid, or water/leak test setup"),
    "durability": ("Upgrade material thickness, reinforcement, or QC standard", "Do not claim durability without material spec or test", "Durability proof", "Material close-up and stress point diagram"),
    "size_usability": ("Clarify size, ergonomics, compatibility, or provide size guide", "Do not imply fit for unsupported models/sizes", "Size and usability guide", "Dimension graphic with hand/object scale"),
    "cleaning_odor": ("Improve cleanability, drying, or low-odor material", "Anti-odor/anti-mold claims need proof", "Easy care", "Cleaning steps or removable parts diagram"),
    "bundle_gap": ("Add missing accessory, spare part, or clearer set contents", "Do not show accessories not included", "Set contents", "Flat lay of included items"),
    "packaging": ("Strengthen packaging and damage-prevention QC", "Avoid guaranteed damage-free claims", "Packaging protection", "Box/protection layer diagram"),
    "localization": ("Add Japanese manual, QR video, or clearer image instructions", "Instruction claims must match included materials", "Easy Japanese instructions", "Manual/QR instruction visual"),
}


def get(row, *names):
    for name in names:
        if name in row and row[name]:
            return row[name]
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--csv-output")
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--sku", default="")
    args = parser.parse_args()

    clusters = defaultdict(list)
    affected = defaultdict(set)
    with open(args.reviews, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rating = float(get(row, "rating", "Rating", "star", "Star") or 0)
            if rating > 3:
                continue
            text = " ".join([get(row, "review_title", "Title"), get(row, "review_text", "Review Text", "body")])
            asin = get(row, "asin", "ASIN", "parent_asin")
            for group, keywords in GROUPS.items():
                if any(k.lower() in text.lower() for k in keywords):
                    clusters[group].append((asin, text[:180].replace("\n", " ")))
                    if asin:
                        affected[group].add(asin)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("# Review-Derived Product Opportunities\n\n")
        for group, items in sorted(clusters.items(), key=lambda kv: len(kv[1]), reverse=True):
            f.write(f"## {group} ({len(items)} evidence)\n\n")
            for asin, excerpt in items[:8]:
                f.write(f"- `{asin}`: {excerpt}\n")
            f.write("\n")

    if args.csv_output:
        with open(args.csv_output, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "candidate_id", "sku", "complaint_cluster", "affected_asins",
                "evidence_count", "fixability", "product_action", "claim_caution",
                "aplus_module_candidate", "image_brief_hint",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for group, items in sorted(clusters.items(), key=lambda kv: len(kv[1]), reverse=True):
                action, caution, module, image_hint = PRODUCT_ACTIONS.get(group, ("Investigate product change", "Needs proof before claim", "Objection handling", "Comparison or proof image"))
                count = len(items)
                fixability = "high" if group in {"bundle_gap", "localization", "packaging", "size_usability"} else "medium"
                writer.writerow({
                    "candidate_id": args.candidate_id,
                    "sku": args.sku,
                    "complaint_cluster": group,
                    "affected_asins": ",".join(sorted(affected[group])),
                    "evidence_count": count,
                    "fixability": fixability,
                    "product_action": action,
                    "claim_caution": caution,
                    "aplus_module_candidate": module,
                    "image_brief_hint": image_hint,
                })


if __name__ == "__main__":
    main()
