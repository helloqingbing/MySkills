# Amazon Japan Risk Rules

## Hard Reject by User Preference

Reject unless the user explicitly overrides:

- Food and supplement: 食品, サプリ, 栄養, 飲料
- Children/baby: ベビー, 子供, キッズ, 赤ちゃん
- Medical or therapeutic: 医療, 医薬, 治療, 矯正, 痛み
- Electric/battery-powered: 電動, 電池, 充電, USB, バッテリー
- Liquid: 液体, オイル, スプレー, 化粧水, 洗剤

## High-Risk Watchlist

- Pet products with ingestion, medication, or safety restraint claims.
- Outdoor products requiring certification, load-bearing safety, fire resistance, or sharp tools.
- Home products touching food can be considered only if they are non-liquid, non-consumable, and claims are limited to material facts like BPA-free where supplier proof exists.

## Competitive Risk

- Amazon Basics in top clicked ASINs: strong penalty.
- Top 5 brand click share >= 65%: concentrated market.
- Top 20 brand click share >= 85%: difficult long-tail entry.
- Average review count >= 2,000: red-ocean warning for this user's preference.

## Listing Claim Caution

Avoid making unsupported claims:

- antibacterial / 抗菌
- medical / pain relief / therapeutic
- child-safe
- food-grade unless documented
- waterproof unless tested

## Output Format

```text
Decision: pass/watch/reject/needs_proof/blocked_pending_approval
Risk level: low/medium/high
Reasons:
- ...
Data needed:
- ...
Mitigation:
- ...
```

## Structured Risk CSV

Use these columns when the audit must feed a launch workflow:

| Field | Values |
|---|---|
| `candidate_id` | stable ID |
| `risk_decision` | pass/watch/reject/needs_proof/blocked_pending_approval |
| `risk_level` | low/medium/high |
| `control_area` | category/ip/claim/logistics/fba/competition/seasonality |
| `reason` | evidence |
| `data_needed` | missing proof |
| `mitigation` | next action |
