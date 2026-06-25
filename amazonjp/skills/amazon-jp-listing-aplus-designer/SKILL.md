---
name: amazon-jp-listing-aplus-designer
description: Create Amazon Japan product listings and A+ Content design briefs for marketplace sellers. Use when Codex needs to generate or improve Amazon.co.jp titles, bullet points, product descriptions, backend search terms, Japanese keyword strategy, A+ module maps, image briefs, mobile-first A+ layouts, compliance checks, or launch-ready listing packages for Japan.
---

# Amazon JP Listing + A+ Designer

## Overview

Create Amazon.co.jp-ready listing copy and A+ Content design briefs from product, customer, competitor, review, or supplier inputs. Produce Japanese buyer-facing copy by default, with Chinese or English strategy notes matching the user's language.

When the user asks to use Agency agents, coordinate or simulate these roles if available: Cross-Border E-Commerce Specialist for marketplace fit, SEO Specialist for keywords, Content Creator for copy, UI Designer for A+ modules, Brand Guardian for voice, and Reality Checker for risk review.

For full launch workflows, require `amazon-jp-launch-gate` before final Listing/A+ approval, and output `amazon_keyword_master.csv` or an Ads export table so `amazon-ads-planner` can consume the keyword strategy.

## Intake

Ask only for missing information that materially affects accuracy. If the user wants a first draft, proceed with stated assumptions and mark gaps.

Collect:
- Product: category, brand/trademark status, existing ASIN or new listing decision, JAN/GTIN or exemption, SKU, product type, model, materials, dimensions, weight, colors, set contents, variation plan.
- Buyer: target persona, usage occasions, pains, objections, gift or seasonal relevance.
- Proof: specs, test data, certifications, warranty, origin, packaging, before/after limits.
- Market: competitor ASINs, current listing, target keywords, review complaints, Q&A, price band.
- Brand: tone, forbidden claims, visual identity, required phrases, differentiators.
- Compliance: category restrictions, FBA restrictions, regulated claims, IP ownership, Brand Registry and A+ eligibility, Japan labeling or certification requirements.

## Workflow

1. Define the purchase thesis.
   Summarize who buys, why now, what makes this product easier to choose, and which claims require proof.

2. Build the keyword map.
   Group terms into core category, attributes, use cases, pain points, specs, materials, audience, season/gift, and Japanese variants. Prefer Amazon.co.jp search language over direct translation.

3. Draft the listing.
   Create title, 5 bullet points, product description, backend Search Terms, image text suggestions, and compliance notes. Keep copy natural, specific, and conversion-led.

4. Design the A+ flow.
   Use 5-7 high-information modules unless the product is simple. Sequence: value proposition, core benefits, use scenes, detail proof, size/specs, comparison/FAQ, brand trust.

5. Run risk and quality checks.
   Check for unsupported claims, keyword stuffing, competitor marks, unavailable variants, medical or safety claims, promotional language, ranking claims, and mobile readability.
   Mark each risk as `Pass`, `Needs Proof`, or `Blocked`.

6. Deliver a launch package.
   Use the output format in `references/output-spec.md`. Include assumptions, missing inputs, launch-gate blockers, and a revision checklist.

## Listing Rules

Title:
- Use: brand + core category keyword + key attribute/spec + use case/audience.
- Put the main keyword and purchase-critical facts early for mobile truncation.
- Avoid keyword piles, repeated synonyms, unsupported superlatives, promo wording, or competitor brands.

Bullet points:
- Write one benefit per bullet: keyword + buyer benefit + concrete proof/spec.
- Cover materials, size/capacity, compatibility, scenes, differentiation, package contents, and care or caution.
- Use consumer language, not factory-only terminology.

Description:
- Use for usage scenarios, FAQ, setup/care, compatibility, long-tail terms, and trust-building details.
- Do not repeat the title mechanically.

Backend Search Terms:
- Add missed synonyms, abbreviations, kana/katakana variants, and high-value English terms used in Japan.
- Separate with spaces. Avoid commas, quotes, competitor marks, ASINs, claims, promo words, and repeated title terms.
- Check current Seller Central byte limits before final submission, especially because Japanese full-width characters consume more bytes.

Japanese localization:
- Write for Japanese shoppers, not as translated Chinese.
- Prefer common katakana for loanwords when that is how Japanese buyers search.
- Keep useful English specs such as USB-C, LED, Bluetooth, IPX, model numbers, and capacity formats.

## A+ Design Rules

Use mobile-first design judgment. Each module should communicate one idea.

Module pattern:
- Hero/value proposition: product visible, one crisp promise, no dense text.
- Benefit modules: 3-5 priority benefits with scene or detail proof.
- Detail proof: materials, dimensions, mechanism, before/after caveats, compatibility.
- Use cases: show real Japanese living/use contexts where relevant.
- Comparison/spec table: clarify variants or competitor-neutral differences.
- FAQ/care: handle objections that block purchase.
- Brand story: concise trust cue, not generic self-praise.

Visual rules:
- Let the real product carry the design; brand color supports hierarchy.
- Use clean backgrounds, strong contrast, short text, consistent typography, and readable image text.
- Convert fixable negative reviews into modules: complaint, design improvement, user benefit.
- Avoid price, discounts, reviews, ratings, rankings, exaggerated absolutes, and risky efficacy language.

## Current-Policy Check

Amazon listing, A+ Content, category, and claim rules change. For final production work, verify current official Amazon Seller Central or sell.amazon.co.jp guidance when:
- the user asks for compliance assurance,
- the user is creating a new ASIN, choosing a variation structure, or relying on JAN/GTIN exemption,
- the product is regulated, medical, food, cosmetic, child/pet, electrical, battery, or safety-related,
- a hard character, byte, image, or module limit matters,
- A+ eligibility, Brand Registry, or category approval is uncertain.

Prefer official Amazon sources, then Japanese regulator sources for non-Amazon legal constraints. Cite sources in the final answer when browsing was used.

## Output

Read `references/output-spec.md` when producing a full listing package, A+ package, audit, or revision checklist. For quick tasks, provide only the requested section while preserving the same quality checks.
